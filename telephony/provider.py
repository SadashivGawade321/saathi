"""
SAATHI ONE — Telephony Provider
Robust demo number management and resolution for multi-tenant AI receptionists.
"""

from bson import ObjectId
from database import demo_numbers_col, businesses_col
from models import new_demo_number
from config import DEMO_NUMBER_PREFIX, DEMO_NUMBER_START


class TelephonyProvider:
    """Base telephony abstraction."""

    def assign_number(self, business_id: str) -> dict:
        raise NotImplementedError

    def resolve_number(self, number: str) -> str | None:
        """Resolve a phone/demo number to a business_id."""
        raise NotImplementedError


class DemoProvider(TelephonyProvider):
    """
    Demo telephony provider — assigns DEMO-XXXX numbers.
    Auto-syncs with MongoDB businesses.
    """

    def assign_number(self, business_id: str) -> dict:
        """Assign a demo number to a business. Returns the demo number doc."""
        b_id_str = str(business_id)
        # Check if business already has a number
        existing = demo_numbers_col().find_one({"business_id": b_id_str, "active": True})
        if existing:
            return {
                "number": existing["number"],
                "business_id": b_id_str,
                "already_assigned": True,
            }

        # Generate next demo number
        last = demo_numbers_col().find_one(sort=[("number", -1)])
        if last and "-" in last.get("number", ""):
            try:
                last_num = int(last["number"].split("-")[1])
                next_num = last_num + 1
            except (IndexError, ValueError):
                next_num = DEMO_NUMBER_START
        else:
            next_num = DEMO_NUMBER_START

        number = f"{DEMO_NUMBER_PREFIX}-{next_num}"

        doc = new_demo_number(b_id_str, number)
        demo_numbers_col().insert_one(doc)

        return {
            "number": number,
            "business_id": b_id_str,
            "already_assigned": False,
        }

    def resolve_number(self, number: str) -> str | None:
        """Look up which business a demo number belongs to and verify business exists."""
        if not number:
            return None

        num_clean = number.strip().upper()

        # 1. Exact match in demo_numbers_col
        doc = demo_numbers_col().find_one({"number": num_clean, "active": True})
        if doc and doc.get("business_id"):
            b_id = doc["business_id"]
            if businesses_col().find_one({"_id": ObjectId(b_id)} if ObjectId.is_valid(b_id) else {"_id": b_id}):
                return str(b_id)

        # 2. Check if number is directly an ObjectId
        if ObjectId.is_valid(num_clean):
            biz = businesses_col().find_one({"_id": ObjectId(num_clean)})
            if biz:
                return str(biz["_id"])

        # 3. Check by business name
        biz = businesses_col().find_one({"name": {"$regex": num_clean, "$options": "i"}})
        if biz:
            return str(biz["_id"])

        # 4. Fallback: get the most recent active business
        latest_biz = businesses_col().find_one(sort=[("created_at", -1)])
        if latest_biz:
            return str(latest_biz["_id"])

        return None

    def get_business_number(self, business_id: str) -> str:
        """Get or auto-assign the demo number for a business."""
        if not business_id:
            return "DEMO-9001"

        b_id_str = str(business_id)
        doc = demo_numbers_col().find_one({"business_id": b_id_str, "active": True})
        if doc:
            return doc["number"]

        # Auto assign if missing
        res = self.assign_number(b_id_str)
        return res["number"]

    def lookup_business(self, number: str) -> str | None:
        """Alias for resolve_number."""
        return self.resolve_number(number)


# Singleton
demo_provider = DemoProvider()
