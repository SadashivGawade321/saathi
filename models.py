"""
SAATHI ONE — Data Models
Helper functions that return well-structured documents for MongoDB.
No ORM — plain dicts with factory functions for consistency.
"""

from datetime import datetime, date, time, timezone
from bson import ObjectId


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now():
    return datetime.now(timezone.utc)


def _oid():
    return str(ObjectId())


# ---------------------------------------------------------------------------
# User (business owner account)
# ---------------------------------------------------------------------------
def new_user(email: str, password_hash: str, name: str = "") -> dict:
    return {
        "email": email,
        "password_hash": password_hash,
        "name": name,
        "created_at": _now(),
    }


# ---------------------------------------------------------------------------
# Business
# ---------------------------------------------------------------------------
def new_business(
    owner_id: str,
    name: str,
    business_type: str,
    description: str = "",
    address: str = "",
    phone: str = "",
    email: str = "",
    instructions: str = "",
    working_hours: dict | None = None,
    capabilities: dict | None = None,
    languages: list | None = None,
    booking_rules: dict | None = None,
) -> dict:
    from config import DEFAULT_WORKING_HOURS, DEFAULT_CAPABILITIES, SUPPORTED_LANGUAGES

    return {
        "owner_id": owner_id,
        "name": name,
        "business_type": business_type,
        "description": description,
        "address": address,
        "phone": phone,
        "email": email,
        "instructions": instructions,
        "working_hours": working_hours or dict(DEFAULT_WORKING_HOURS),
        "capabilities": capabilities or dict(DEFAULT_CAPABILITIES),
        "languages": languages or list(SUPPORTED_LANGUAGES.keys()),
        "booking_rules": booking_rules or {
            "max_advance_days": 30,
            "min_advance_hours": 1,
            "allow_cancellation": True,
            "cancellation_hours": 2,
            "allow_rescheduling": True,
        },
        "created_at": _now(),
        "updated_at": _now(),
    }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
def new_service(
    business_id: str,
    name: str,
    duration_minutes: int = 30,
    price: float = 0.0,
    description: str = "",
    active: bool = True,
) -> dict:
    return {
        "business_id": business_id,
        "name": name,
        "duration_minutes": duration_minutes,
        "price": price,
        "description": description,
        "active": active,
        "created_at": _now(),
    }


# ---------------------------------------------------------------------------
# Resource (table / barber / doctor / room / etc.)
# ---------------------------------------------------------------------------
def new_resource(
    business_id: str,
    name: str,
    resource_type: str = "Resource",
    capacity: int = 1,
    active: bool = True,
    metadata: dict | None = None,
) -> dict:
    return {
        "business_id": business_id,
        "name": name,
        "resource_type": resource_type,
        "capacity": capacity,
        "active": active,
        "metadata": metadata or {},
        "created_at": _now(),
    }


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------
def new_customer(
    business_id: str,
    name: str,
    phone: str = "",
    email: str = "",
    language_preference: str = "en",
) -> dict:
    return {
        "business_id": business_id,
        "name": name,
        "phone": phone,
        "email": email,
        "language_preference": language_preference,
        "created_at": _now(),
    }


# ---------------------------------------------------------------------------
# Booking
# ---------------------------------------------------------------------------
def new_booking(
    business_id: str,
    customer_id: str,
    service_id: str,
    resource_id: str,
    booking_date: str,
    start_time: str,
    end_time: str,
    status: str = "confirmed",
    source: str = "ai_voice",
    notes: str = "",
    guests: int = 1,
    booking_ref: str = "",
) -> dict:
    import uuid
    ref = booking_ref or f"BK-{uuid.uuid4().hex[:8].upper()}"
    return {
        "business_id": business_id,
        "booking_ref": ref,
        "bookingRef": ref,
        "idempotency_key": f"IDEM-{uuid.uuid4().hex}",
        "customer_id": customer_id,
        "service_id": service_id,
        "resource_id": resource_id,
        "date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "source": source,
        "notes": notes,
        "guests": guests,
        "created_at": _now(),
        "updated_at": _now(),
    }


# ---------------------------------------------------------------------------
# AI Employee
# ---------------------------------------------------------------------------
def new_ai_employee(
    business_id: str,
    name: str = "Maya",
    role: str = "AI Receptionist",
    languages: list | None = None,
    capabilities: dict | None = None,
    personality: str = "polite, professional, helpful",
) -> dict:
    from config import DEFAULT_CAPABILITIES, SUPPORTED_LANGUAGES

    return {
        "business_id": business_id,
        "name": name,
        "role": role,
        "languages": languages or list(SUPPORTED_LANGUAGES.keys()),
        "capabilities": capabilities or dict(DEFAULT_CAPABILITIES),
        "personality": personality,
        "active": True,
        "created_at": _now(),
        "updated_at": _now(),
    }


# ---------------------------------------------------------------------------
# Demo Number
# ---------------------------------------------------------------------------
def new_demo_number(business_id: str, number: str) -> dict:
    return {
        "business_id": business_id,
        "number": number,
        "active": True,
        "created_at": _now(),
    }


# ---------------------------------------------------------------------------
# Call
# ---------------------------------------------------------------------------
def new_call(
    business_id: str,
    language: str = "",
    intent: str = "",
    outcome: str = "",
) -> dict:
    return {
        "business_id": business_id,
        "started_at": _now(),
        "ended_at": None,
        "language": language,
        "intent": intent,
        "outcome": outcome,
        "transcript": [],
        "booking_id": None,
    }


# ---------------------------------------------------------------------------
# Conversation Message
# ---------------------------------------------------------------------------
def new_conversation_message(
    call_id: str,
    business_id: str,
    role: str,
    content: str,
    language: str = "",
    language_confidence: float = 0.0,
    intent: str = "",
    tool_calls: list | None = None,
) -> dict:
    return {
        "call_id": call_id,
        "business_id": business_id,
        "role": role,
        "content": content,
        "language": language,
        "language_confidence": language_confidence,
        "intent": intent,
        "tool_calls": tool_calls or [],
        "timestamp": _now(),
    }


# ---------------------------------------------------------------------------
# Tool Execution Log
# ---------------------------------------------------------------------------
def new_tool_execution(
    business_id: str,
    conversation_id: str,
    tool_name: str,
    tool_input: dict,
    result: dict,
    success: bool,
) -> dict:
    return {
        "business_id": business_id,
        "conversation_id": conversation_id,
        "tool_name": tool_name,
        "input": tool_input,
        "result": result,
        "success": success,
        "timestamp": _now(),
    }
