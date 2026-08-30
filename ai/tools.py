"""
SAATHI ONE — Gemini Function-Calling Tools
Python functions that Gemini can call. Each tool validates business_id,
executes business logic, and returns structured results.
Gemini NEVER touches MongoDB directly.
"""

from datetime import datetime, timedelta, timezone
from bson import ObjectId
from database import (
    businesses_col,
    services_col,
    resources_col,
    customers_col,
    bookings_col,
    tool_executions_col,
)
from models import new_tool_execution
from booking.engine import booking_engine


# ---------------------------------------------------------------------------
# Tool execution logger
# ---------------------------------------------------------------------------
def _log_tool(business_id, conversation_id, tool_name, tool_input, result, success):
    """Log every tool execution for auditability."""
    doc = new_tool_execution(business_id, conversation_id, tool_name, tool_input, result, success)
    tool_executions_col().insert_one(doc)
    return doc


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_business_information(business_id: str, **kwargs) -> dict:
    """Get business details including name, type, address, contact, and working hours."""
    biz = businesses_col().find_one({"_id": ObjectId(business_id)})
    if not biz:
        return {"error": "Business not found."}
    return {
        "name": biz["name"],
        "type": biz["business_type"],
        "description": biz.get("description", ""),
        "address": biz.get("address", ""),
        "phone": biz.get("phone", ""),
        "email": biz.get("email", ""),
        "instructions": biz.get("instructions", ""),
        "working_hours": biz.get("working_hours", {}),
    }


def get_services(business_id: str, **kwargs) -> dict:
    """Get all active services offered by the business."""
    svcs = list(services_col().find({"business_id": business_id, "active": True}))
    result = []
    for s in svcs:
        result.append({
            "service_id": str(s["_id"]),
            "name": s["name"],
            "duration_minutes": s.get("duration_minutes", 30),
            "price": s.get("price", 0),
            "description": s.get("description", ""),
        })
    return {"services": result, "count": len(result)}


def get_service_details(business_id: str, service_name: str = "", **kwargs) -> dict:
    """Get details of a specific service by name."""
    query = {"business_id": business_id, "active": True}
    if service_name:
        # Case-insensitive partial match
        import re
        query["name"] = {"$regex": re.escape(service_name), "$options": "i"}

    svc = services_col().find_one(query)
    if not svc:
        # Try a broader search
        all_svcs = list(services_col().find({"business_id": business_id, "active": True}))
        for s in all_svcs:
            if service_name.lower() in s["name"].lower():
                svc = s
                break
        if not svc:
            return {"error": f"Service '{service_name}' not found.", "available_services": [s["name"] for s in all_svcs]}

    return {
        "service_id": str(svc["_id"]),
        "name": svc["name"],
        "duration_minutes": svc.get("duration_minutes", 30),
        "price": svc.get("price", 0),
        "description": svc.get("description", ""),
    }


def check_availability(
    business_id: str,
    service_name: str = "",
    date: str = "",
    time: str = "",
    resource_name: str = "",
    **kwargs,
) -> dict:
    """Check if a specific date/time is available for a service."""
    # Resolve service
    svc_result = _resolve_service(business_id, service_name)
    if "error" in svc_result:
        return svc_result
    service_id = svc_result["service_id"]

    # Resolve date
    date_str = _resolve_date(date)
    if not date_str:
        return {"error": f"Could not understand the date: '{date}'"}

    # Resolve time
    time_str = _resolve_time(time)
    if not time_str:
        return {"error": f"Could not understand the time: '{time}'"}

    # Resolve resource (optional)
    resource_id = None
    if resource_name:
        res = resources_col().find_one({
            "business_id": business_id,
            "name": {"$regex": resource_name, "$options": "i"},
            "active": True,
        })
        if res:
            resource_id = str(res["_id"])

    result = booking_engine.check_availability(business_id, service_id, date_str, time_str, resource_id)
    return result


def get_available_slots(
    business_id: str,
    service_name: str = "",
    date: str = "",
    resource_name: str = "",
    **kwargs,
) -> dict:
    """Get all available time slots for a service on a given date."""
    svc_result = _resolve_service(business_id, service_name)
    if "error" in svc_result:
        return svc_result
    service_id = svc_result["service_id"]

    date_str = _resolve_date(date)
    if not date_str:
        return {"error": f"Could not understand the date: '{date}'"}

    resource_id = None
    if resource_name:
        res = resources_col().find_one({
            "business_id": business_id,
            "name": {"$regex": resource_name, "$options": "i"},
            "active": True,
        })
        if res:
            resource_id = str(res["_id"])

    slots = booking_engine.get_available_slots(business_id, service_id, date_str, resource_id)

    # Summarize — group by time, show first few
    if len(slots) > 10:
        # Show unique times
        unique_times = sorted(set(s["start_time"] for s in slots))
        return {
            "date": date_str,
            "available_times": unique_times,
            "total_slots": len(slots),
            "message": f"{len(unique_times)} time slots available on {date_str}.",
        }

    return {
        "date": date_str,
        "slots": slots,
        "total_slots": len(slots),
    }


def create_customer(
    business_id: str,
    name: str = "",
    phone: str = "",
    email: str = "",
    language: str = "en",
    **kwargs,
) -> dict:
    """Register a new customer or find existing one."""
    if not name:
        return {"error": "Customer name is required."}
    result = booking_engine.find_or_create_customer(business_id, name, phone, email, language)
    return result


def create_booking(
    business_id: str,
    customer_name: str = "",
    customer_phone: str = "",
    service_name: str = "",
    date: str = "",
    time: str = "",
    resource_name: str = "",
    guests: int = 1,
    notes: str = "",
    **kwargs,
) -> dict:
    """Create a new booking/appointment. This is the main booking action."""
    # Resolve service
    svc_result = _resolve_service(business_id, service_name)
    if "error" in svc_result:
        return svc_result
    service_id = svc_result["service_id"]
    duration = svc_result.get("duration_minutes", 30)

    # Resolve date
    date_str = _resolve_date(date)
    if not date_str:
        return {"error": f"Could not understand the date: '{date}'"}

    # Resolve time
    time_str = _resolve_time(time)
    if not time_str:
        return {"error": f"Could not understand the time: '{time}'"}

    # Calculate end time
    end_time = (datetime.strptime(time_str, "%H:%M") + timedelta(minutes=duration)).strftime("%H:%M")

    # Resolve resource
    resource_id = "any"
    if resource_name:
        res = resources_col().find_one({
            "business_id": business_id,
            "name": {"$regex": resource_name, "$options": "i"},
            "active": True,
        })
        if res:
            resource_id = str(res["_id"])
    else:
        # Auto-assign first available resource
        avail = booking_engine.check_availability(business_id, service_id, date_str, time_str)
        if avail["available"] and avail["slots"]:
            resource_id = avail["slots"][0]["resource_id"]
        elif not avail["available"]:
            return {
                "success": False,
                "error": "The requested time slot is not available.",
                "date": date_str,
                "time": time_str,
            }

    # Find or create customer
    cust_name = customer_name or "Walk-in Customer"
    cust = booking_engine.find_or_create_customer(business_id, cust_name, customer_phone)
    customer_id = cust["customer_id"]

    # Create booking
    result = booking_engine.create_booking(
        business_id=business_id,
        customer_id=customer_id,
        service_id=service_id,
        resource_id=resource_id,
        date_str=date_str,
        start_time=time_str,
        end_time=end_time,
        source="ai_voice",
        notes=notes,
        guests=guests,
    )

    if result["success"]:
        result["customer_name"] = cust_name
        result["service_name"] = svc_result.get("name", service_name)

    return result


def cancel_booking(business_id: str, booking_id: str = "", customer_name: str = "", **kwargs) -> dict:
    """Cancel an existing booking."""
    if booking_id:
        return booking_engine.cancel_booking(business_id, booking_id)

    # Try to find by customer name
    if customer_name:
        cust = customers_col().find_one({
            "business_id": business_id,
            "name": {"$regex": customer_name, "$options": "i"},
        })
        if cust:
            booking = bookings_col().find_one({
                "business_id": business_id,
                "customer_id": str(cust["_id"]),
                "status": "confirmed",
            })
            if booking:
                return booking_engine.cancel_booking(business_id, str(booking["_id"]))

    return {"success": False, "error": "Could not find the booking to cancel. Please provide more details."}


def reschedule_booking(
    business_id: str,
    booking_id: str = "",
    new_date: str = "",
    new_time: str = "",
    customer_name: str = "",
    **kwargs,
) -> dict:
    """Reschedule an existing booking to a new date/time."""
    # Find the booking
    if not booking_id and customer_name:
        cust = customers_col().find_one({
            "business_id": business_id,
            "name": {"$regex": customer_name, "$options": "i"},
        })
        if cust:
            booking = bookings_col().find_one({
                "business_id": business_id,
                "customer_id": str(cust["_id"]),
                "status": "confirmed",
            })
            if booking:
                booking_id = str(booking["_id"])

    if not booking_id:
        return {"success": False, "error": "Could not find the booking. Please provide more details."}

    date_str = _resolve_date(new_date) if new_date else None
    time_str = _resolve_time(new_time) if new_time else None

    if not date_str or not time_str:
        return {"success": False, "error": "Please provide both a new date and time."}

    return booking_engine.reschedule_booking(business_id, booking_id, date_str, time_str)


def request_human_handoff(business_id: str, reason: str = "", **kwargs) -> dict:
    """Request transfer to a human operator."""
    return {
        "success": True,
        "message": "I'm transferring you to a human representative. Please hold.",
        "reason": reason,
        "note": "In the demo version, this flags the request for the business owner to handle.",
    }


# ---------------------------------------------------------------------------
# Helper: resolve natural language date/time to structured format
# ---------------------------------------------------------------------------
def _resolve_date(date_input: str) -> str | None:
    """Convert natural language date to YYYY-MM-DD."""
    if not date_input:
        return None

    date_lower = date_input.strip().lower()
    today = datetime.now(timezone.utc)

    # Direct keywords (Hindi, Marathi, English)
    if date_lower in ("today", "aaj", "आज"):
        return today.strftime("%Y-%m-%d")
    if date_lower in ("tomorrow", "kal", "कल", "उद्या"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if date_lower in ("day after tomorrow", "parson", "परसों", "परवा"):
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")

    # Try day names (Hindi, Marathi, English)
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
        "somvar": 0, "mangalvar": 1, "budhvar": 2, "guruvar": 3,
        "shukravar": 4, "shanivar": 5, "ravivar": 6,
        "सोमवार": 0, "मंगळवार": 1, "बुधवार": 2, "गुरुवार": 3,
        "शुक्रवार": 4, "शनिवार": 5, "रविवार": 6,
    }
    for day_name, day_num in day_map.items():
        if day_name in date_lower:
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    # Try dateutil parser
    try:
        from dateutil import parser
        parsed = parser.parse(date_input.strip(), fuzzy=True)
        if parsed.year == 1900:
            parsed = parsed.replace(year=today.year)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Try standard formats fallback
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%B %d", "%b %d"]:
        try:
            parsed = datetime.strptime(date_input.strip(), fmt)
            if parsed.year == 1900:
                parsed = parsed.replace(year=today.year)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def _resolve_time(time_input: str) -> str | None:
    """Convert natural language time to HH:MM (24-hour)."""
    if not time_input:
        return None

    import re
    time_str = time_input.strip().lower()

    # Check for PM qualifiers
    pm_patterns = [r"\bpm\b", r"\bshaam\b", r"\bevening\b", r"\bsham\b", r"संध्याकाळी", r"शाम", r"\braat\b", r"रात", r"\bnight\b", r"\bdopahar\b", r"\bafternoon\b", r"दोपहर"]
    is_pm = any(re.search(p, time_str) for p in pm_patterns)

    # Check for AM qualifiers
    am_patterns = [r"\bam\b", r"\bsubah\b", r"\bmorning\b", r"सुबह", r"सकाळी"]
    is_am = any(re.search(p, time_str) for p in am_patterns)

    # Remove qualifiers cleanly using word boundaries / patterns
    clean_patterns = [
        r"\bbaje\b", r"वाजता", r"\bpm\b", r"\bam\b", r"\bshaam\b", r"\bevening\b",
        r"\bsham\b", r"\bsubah\b", r"\bmorning\b", r"\bdopahar\b", r"\bafternoon\b",
        r"\braat\b", r"\bnight\b", r"संध्याकाळी", r"शाम", r"सुबह", r"सकाळी", r"रात", r"दोपहर",
        r"\bo'clock\b", r"\boclock\b"
    ]
    for p in clean_patterns:
        time_str = re.sub(p, " ", time_str)

    time_str = time_str.strip()

    # Try standard parsing
    for fmt in ["%H:%M", "%I:%M %p", "%I:%M", "%H", "%I %p"]:
        try:
            parsed = datetime.strptime(time_str, fmt)
            hour = parsed.hour
            if is_pm and hour < 12:
                hour += 12
            elif is_am and hour == 12:
                hour = 0
            elif not is_am and not is_pm and hour != 0:
                if 1 <= hour <= 6:
                    hour += 12
            return f"{hour:02d}:{parsed.minute:02d}"
        except ValueError:
            continue

    # Try extracting digits like '7' or '7:30'
    match = re.search(r"(\d{1,2})(?::(\d{2}))?", time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        if is_pm and hour < 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0
        elif not is_am and not is_pm and 1 <= hour <= 6:
            hour += 12
        return f"{hour:02d}:{minute:02d}"

    return None


def _resolve_service(business_id: str, service_name: str) -> dict:
    """Find a service by name. Returns dict with service_id or error."""
    if not service_name:
        # If only one service, auto-select
        svcs = list(services_col().find({"business_id": business_id, "active": True}))
        if len(svcs) == 1:
            return {
                "service_id": str(svcs[0]["_id"]),
                "name": svcs[0]["name"],
                "duration_minutes": svcs[0].get("duration_minutes", 30),
            }
        if not svcs:
            return {"error": "No services are configured for this business."}
        return {
            "error": "Please specify which service you need.",
            "available_services": [s["name"] for s in svcs],
        }

    import re
    svc = services_col().find_one({
        "business_id": business_id,
        "name": {"$regex": re.escape(service_name), "$options": "i"},
        "active": True,
    })
    if svc:
        return {
            "service_id": str(svc["_id"]),
            "name": svc["name"],
            "duration_minutes": svc.get("duration_minutes", 30),
        }

    # Broader search
    all_svcs = list(services_col().find({"business_id": business_id, "active": True}))
    for s in all_svcs:
        if service_name.lower() in s["name"].lower() or s["name"].lower() in service_name.lower():
            return {
                "service_id": str(s["_id"]),
                "name": s["name"],
                "duration_minutes": s.get("duration_minutes", 30),
            }

    return {
        "error": f"Service '{service_name}' not found.",
        "available_services": [s["name"] for s in all_svcs],
    }


# ---------------------------------------------------------------------------
# Tool declarations for Gemini function calling
# ---------------------------------------------------------------------------
TOOL_DECLARATIONS = [
    {
        "name": "get_business_information",
        "description": "Get the business details including name, type, address, contact information, and working hours.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_services",
        "description": "Get all active services offered by the business with their names, durations, and prices.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_service_details",
        "description": "Get detailed information about a specific service by name.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "The name of the service to look up (e.g., 'Haircut', 'Consultation').",
                },
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "check_availability",
        "description": "Check if a specific date and time is available for a service. Use this before confirming any booking.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "The service to check availability for.",
                },
                "date": {
                    "type": "string",
                    "description": "The date to check. Can be natural language like 'tomorrow', 'kal', 'Monday', or a date like '2025-01-15'.",
                },
                "time": {
                    "type": "string",
                    "description": "The time to check. Can be '7 PM', '19:00', '7 baje shaam', etc.",
                },
                "resource_name": {
                    "type": "string",
                    "description": "Optional: specific resource/staff name (e.g., 'Dr. Sharma', 'Table 1').",
                },
            },
            "required": ["service_name", "date", "time"],
        },
    },
    {
        "name": "get_available_slots",
        "description": "Get all available time slots for a service on a specific date. Use when the customer asks what times are available.",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "The service to get slots for.",
                },
                "date": {
                    "type": "string",
                    "description": "The date to get slots for.",
                },
                "resource_name": {
                    "type": "string",
                    "description": "Optional: specific resource/staff name.",
                },
            },
            "required": ["service_name", "date"],
        },
    },
    {
        "name": "create_customer",
        "description": "Register a new customer or find an existing customer by phone number.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The customer's name.",
                },
                "phone": {
                    "type": "string",
                    "description": "The customer's phone number.",
                },
                "email": {
                    "type": "string",
                    "description": "The customer's email address.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "create_booking",
        "description": "Create a new appointment or reservation. ONLY call this after the customer has confirmed they want to book. Always check availability first.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "The customer's name.",
                },
                "customer_phone": {
                    "type": "string",
                    "description": "The customer's phone number (optional).",
                },
                "service_name": {
                    "type": "string",
                    "description": "The service to book.",
                },
                "date": {
                    "type": "string",
                    "description": "The booking date.",
                },
                "time": {
                    "type": "string",
                    "description": "The booking time.",
                },
                "resource_name": {
                    "type": "string",
                    "description": "Optional: preferred staff/resource.",
                },
                "guests": {
                    "type": "integer",
                    "description": "Number of guests (for restaurants).",
                },
                "notes": {
                    "type": "string",
                    "description": "Any special notes or requests.",
                },
            },
            "required": ["service_name", "date", "time"],
        },
    },
    {
        "name": "cancel_booking",
        "description": "Cancel an existing booking/appointment.",
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The booking ID to cancel.",
                },
                "customer_name": {
                    "type": "string",
                    "description": "The customer name to look up the booking.",
                },
            },
        },
    },
    {
        "name": "reschedule_booking",
        "description": "Reschedule an existing booking to a new date and time.",
        "parameters": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The booking ID to reschedule.",
                },
                "customer_name": {
                    "type": "string",
                    "description": "The customer name to look up the booking.",
                },
                "new_date": {
                    "type": "string",
                    "description": "The new date for the booking.",
                },
                "new_time": {
                    "type": "string",
                    "description": "The new time for the booking.",
                },
            },
            "required": ["new_date", "new_time"],
        },
    },
    {
        "name": "request_human_handoff",
        "description": "Transfer the customer to a human representative when they specifically request it.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for the handoff request.",
                },
            },
        },
    },
]

# Map tool names to functions
TOOL_FUNCTIONS = {
    "get_business_information": get_business_information,
    "get_services": get_services,
    "get_service_details": get_service_details,
    "check_availability": check_availability,
    "get_available_slots": get_available_slots,
    "create_customer": create_customer,
    "create_booking": create_booking,
    "cancel_booking": cancel_booking,
    "reschedule_booking": reschedule_booking,
    "request_human_handoff": request_human_handoff,
}
