"""
SAATHI ONE — Booking Engine
Universal appointment/booking engine that works for all business types.
"""

from datetime import datetime, timedelta, timezone
from bson import ObjectId
from database import (
    bookings_col,
    services_col,
    resources_col,
    businesses_col,
    customers_col,
)
from models import new_booking, new_customer


class BookingEngine:
    """Universal booking engine — works for restaurants, barbers, clinics, etc."""

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------
    def get_working_hours_for_date(self, business_id: str, date_str: str) -> dict | None:
        """Return working hours for a specific date. Returns None if closed."""
        business = businesses_col().find_one({"_id": ObjectId(business_id)})
        if not business:
            return None

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = dt.strftime("%A").lower()
        wh = business.get("working_hours", {})
        day_info = wh.get(day_name, {})

        if not day_info.get("is_open", False):
            return None
        return day_info

    def get_available_slots(
        self,
        business_id: str,
        service_id: str,
        date_str: str,
        resource_id: str | None = None,
    ) -> list[dict]:
        """
        Get all available time slots for a service on a given date.
        Returns list of {"start_time": "HH:MM", "end_time": "HH:MM", "resource_id": ..., "resource_name": ...}
        """
        # Get working hours
        day_info = self.get_working_hours_for_date(business_id, date_str)
        if not day_info:
            return []

        # Get service duration
        service = services_col().find_one({"_id": ObjectId(service_id), "business_id": business_id})
        if not service:
            return []
        duration = service.get("duration_minutes", 30)

        # Get resources
        if resource_id:
            res_list = list(resources_col().find({
                "_id": ObjectId(resource_id),
                "business_id": business_id,
                "active": True,
            }))
        else:
            res_list = list(resources_col().find({
                "business_id": business_id,
                "active": True,
            }))

        if not res_list:
            # If no resources configured, use a virtual resource
            res_list = [{"_id": "any", "name": "Available", "resource_type": "Any"}]

        # Generate time slots in flexible 30-minute intervals
        open_time = datetime.strptime(day_info["open"], "%H:%M")
        close_time = datetime.strptime(day_info["close"], "%H:%M")
        service_duration = timedelta(minutes=duration)
        slot_step = timedelta(minutes=30)  # Step by 30 mins for natural availability

        # Get existing bookings for this date
        existing = list(bookings_col().find({
            "business_id": business_id,
            "date": date_str,
            "status": {"$in": ["confirmed"]},
        }))

        available_slots = []
        current = open_time
        while current + service_duration <= close_time:
            start_str = current.strftime("%H:%M")
            end_str = (current + service_duration).strftime("%H:%M")

            for res in res_list:
                res_id_str = str(res["_id"])
                is_booked = False
                for booking in existing:
                    if booking.get("resource_id") == res_id_str:
                        b_start = booking["start_time"]
                        b_end = booking["end_time"]
                        if not (end_str <= b_start or start_str >= b_end):
                            is_booked = True
                            break

                if not is_booked:
                    available_slots.append({
                        "start_time": start_str,
                        "end_time": end_str,
                        "resource_id": res_id_str,
                        "resource_name": res.get("name", "Available"),
                    })

            current += slot_step

        return available_slots

    def check_availability(
        self,
        business_id: str,
        service_id: str,
        date_str: str,
        time_str: str,
        resource_id: str | None = None,
    ) -> dict:
        """
        Check if a specific time slot is available.
        Checks operating hours and booking overlaps directly.
        """
        day_info = self.get_working_hours_for_date(business_id, date_str)
        if not day_info:
            return {"available": False, "slots": [], "error": "Business is closed on this date.", "date": date_str}

        # Normalize requested time
        req_time = None
        try:
            req_time = datetime.strptime(time_str.strip(), "%H:%M").strftime("%H:%M")
        except ValueError:
            for fmt in ["%I:%M %p", "%I %p", "%I:%M%p", "%I%p", "%H:%M"]:
                try:
                    req_time = datetime.strptime(time_str.strip().upper(), fmt).strftime("%H:%M")
                    break
                except ValueError:
                    continue

        if not req_time:
            # Fallback: check all slots
            all_slots = self.get_available_slots(business_id, service_id, date_str, resource_id)
            return {"available": False, "slots": all_slots[:5], "error": f"Could not parse time: {time_str}"}

        # Get service duration
        service = services_col().find_one({"_id": ObjectId(service_id), "business_id": business_id})
        duration = service.get("duration_minutes", 30) if service else 30

        # Calculate requested end time
        req_start_dt = datetime.strptime(req_time, "%H:%M")
        req_end_dt = req_start_dt + timedelta(minutes=duration)
        req_end = req_end_dt.strftime("%H:%M")

        open_time = datetime.strptime(day_info["open"], "%H:%M")
        close_time = datetime.strptime(day_info["close"], "%H:%M")

        # Check if within working hours
        if req_start_dt < open_time or req_end_dt > close_time:
            all_slots = self.get_available_slots(business_id, service_id, date_str, resource_id)
            return {
                "available": False,
                "slots": all_slots[:5],
                "requested_time": req_time,
                "date": date_str,
                "reason": f"Requested time is outside business hours ({day_info['open']} - {day_info['close']})",
            }

        # Get resources
        if resource_id and resource_id != "any":
            res_list = list(resources_col().find({"_id": ObjectId(resource_id), "business_id": business_id, "active": True}))
        else:
            res_list = list(resources_col().find({"business_id": business_id, "active": True}))

        if not res_list:
            res_list = [{"_id": "any", "name": "Available", "resource_type": "Any"}]

        # Check existing bookings for overlap
        existing = list(bookings_col().find({
            "business_id": business_id,
            "date": date_str,
            "status": {"$in": ["confirmed"]},
        }))

        available_for_resources = []
        for res in res_list:
            res_id_str = str(res["_id"])
            is_booked = False
            for booking in existing:
                if booking.get("resource_id") == res_id_str:
                    b_start = booking["start_time"]
                    b_end = booking["end_time"]
                    if not (req_end <= b_start or req_time >= b_end):
                        is_booked = True
                        break
            if not is_booked:
                available_for_resources.append({
                    "start_time": req_time,
                    "end_time": req_end,
                    "resource_id": res_id_str,
                    "resource_name": res.get("name", "Available"),
                })

        return {
            "available": len(available_for_resources) > 0,
            "slots": available_for_resources,
            "requested_time": req_time,
            "date": date_str,
        }

    # ------------------------------------------------------------------
    # Booking CRUD
    # ------------------------------------------------------------------
    def create_booking(
        self,
        business_id: str,
        customer_id: str,
        service_id: str,
        resource_id: str,
        date_str: str,
        start_time: str,
        end_time: str,
        source: str = "ai_voice",
        notes: str = "",
        guests: int = 1,
    ) -> dict:
        """Create a new booking after validating availability."""
        # Validate availability first
        avail = self.check_availability(business_id, service_id, date_str, start_time, resource_id)
        if not avail["available"]:
            return {
                "success": False,
                "error": "The requested time slot is not available.",
                "booking_id": None,
            }

        booking = new_booking(
            business_id=business_id,
            customer_id=customer_id,
            service_id=service_id,
            resource_id=resource_id,
            booking_date=date_str,
            start_time=start_time,
            end_time=end_time,
            status="confirmed",
            source=source,
            notes=notes,
            guests=guests,
        )
        result = bookings_col().insert_one(booking)
        booking["_id"] = result.inserted_id

        return {
            "success": True,
            "booking_id": str(result.inserted_id),
            "date": date_str,
            "start_time": start_time,
            "end_time": end_time,
            "status": "confirmed",
        }

    def cancel_booking(self, business_id: str, booking_id: str) -> dict:
        """Cancel a booking."""
        try:
            result = bookings_col().update_one(
                {"_id": ObjectId(booking_id), "business_id": business_id, "status": "confirmed"},
                {"$set": {"status": "cancelled", "updated_at": datetime.now(timezone.utc)}},
            )
            if result.modified_count == 0:
                return {"success": False, "error": "Booking not found or already cancelled."}
            return {"success": True, "booking_id": booking_id, "status": "cancelled"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reschedule_booking(
        self,
        business_id: str,
        booking_id: str,
        new_date: str,
        new_start_time: str,
    ) -> dict:
        """Reschedule a booking to a new date/time."""
        # Get the existing booking
        booking = bookings_col().find_one({
            "_id": ObjectId(booking_id),
            "business_id": business_id,
            "status": "confirmed",
        })
        if not booking:
            return {"success": False, "error": "Booking not found or not active."}

        # Get service duration
        service = services_col().find_one({"_id": ObjectId(booking["service_id"])})
        duration = service.get("duration_minutes", 30) if service else 30
        new_end_time = (
            datetime.strptime(new_start_time, "%H:%M") + timedelta(minutes=duration)
        ).strftime("%H:%M")

        # Check new slot availability
        avail = self.check_availability(
            business_id, booking["service_id"], new_date, new_start_time, booking.get("resource_id")
        )
        if not avail["available"]:
            return {"success": False, "error": "The new time slot is not available."}

        # Update booking
        bookings_col().update_one(
            {"_id": ObjectId(booking_id)},
            {
                "$set": {
                    "date": new_date,
                    "start_time": new_start_time,
                    "end_time": new_end_time,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return {
            "success": True,
            "booking_id": booking_id,
            "new_date": new_date,
            "new_start_time": new_start_time,
            "new_end_time": new_end_time,
        }

    # ------------------------------------------------------------------
    # Customer Management
    # ------------------------------------------------------------------
    def find_or_create_customer(
        self,
        business_id: str,
        name: str,
        phone: str = "",
        email: str = "",
        language: str = "en",
    ) -> dict:
        """Find existing customer by phone or create new one."""
        if phone:
            existing = customers_col().find_one({
                "business_id": business_id,
                "phone": phone,
            })
            if existing:
                return {"customer_id": str(existing["_id"]), "name": existing["name"], "is_new": False}

        customer = new_customer(business_id, name, phone, email, language)
        result = customers_col().insert_one(customer)
        return {"customer_id": str(result.inserted_id), "name": name, "is_new": True}

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def get_bookings(self, business_id: str, date_str: str | None = None, status: str | None = None) -> list:
        """Get bookings for a business, optionally filtered."""
        query = {"business_id": business_id}
        if date_str:
            query["date"] = date_str
        if status:
            query["status"] = status
        return list(bookings_col().find(query).sort("date", -1))

    def get_today_bookings_count(self, business_id: str) -> int:
        """Count today's bookings."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return bookings_col().count_documents({
            "business_id": business_id,
            "date": today,
            "status": "confirmed",
        })


# Singleton
booking_engine = BookingEngine()
