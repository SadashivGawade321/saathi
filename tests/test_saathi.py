"""
SAATHI ONE — Automated Verification Test Suite
Tests core business logic, natural language parsing, booking calculations,
data models, telephony numbering, and prompt generation.
"""

import sys
import os
import unittest
from datetime import datetime, timedelta, timezone

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import (
    DEFAULT_WORKING_HOURS,
    SUPPORTED_LANGUAGES,
    ALL_CAPABILITIES,
    BUSINESS_TYPES,
)
from models import (
    new_user,
    new_business,
    new_service,
    new_resource,
    new_customer,
    new_booking,
    new_ai_employee,
    new_demo_number,
    new_call,
)
from ai.prompts import build_system_prompt
from ai.tools import _resolve_date, _resolve_time, TOOL_DECLARATIONS, TOOL_FUNCTIONS
from telephony.provider import DemoProvider


class TestSaathiOneCore(unittest.TestCase):

    def test_data_models(self):
        """Test model factories return valid dict structures."""
        user = new_user("owner@example.com", "hashed_pwd", "Rajesh Sharma")
        self.assertEqual(user["email"], "owner@example.com")
        self.assertIn("created_at", user)

        biz = new_business("user_123", "Apex Salon", "Salon")
        self.assertEqual(biz["name"], "Apex Salon")
        self.assertEqual(biz["business_type"], "Salon")
        self.assertIn("monday", biz["working_hours"])
        self.assertIn("booking", biz["capabilities"])

        svc = new_service("biz_123", "Hair Styling", 45, 500.0)
        self.assertEqual(svc["name"], "Hair Styling")
        self.assertEqual(svc["duration_minutes"], 45)
        self.assertEqual(svc["price"], 500.0)

        res = new_resource("biz_123", "Stylist Priya", "Stylist", 1)
        self.assertEqual(res["name"], "Stylist Priya")

        booking = new_booking(
            "biz_123", "cust_1", "svc_1", "res_1", "2026-09-01", "10:00", "10:45"
        )
        self.assertEqual(booking["date"], "2026-09-01")
        self.assertEqual(booking["status"], "confirmed")

    def test_natural_language_date_resolution(self):
        """Test multilingual and natural language date parsing."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")

        # English
        self.assertEqual(_resolve_date("today"), today)
        self.assertEqual(_resolve_date("tomorrow"), tomorrow)
        self.assertEqual(_resolve_date("day after tomorrow"), day_after)

        # Hindi
        self.assertEqual(_resolve_date("aaj"), today)
        self.assertEqual(_resolve_date("आज"), today)
        self.assertEqual(_resolve_date("kal"), tomorrow)
        self.assertEqual(_resolve_date("कल"), tomorrow)
        self.assertEqual(_resolve_date("parson"), day_after)
        self.assertEqual(_resolve_date("परसों"), day_after)

        # Marathi
        self.assertEqual(_resolve_date("उद्या"), tomorrow)
        self.assertEqual(_resolve_date("परवा"), day_after)

        # Explicit standard dates
        self.assertEqual(_resolve_date("2026-10-15"), "2026-10-15")

    def test_natural_language_time_resolution(self):
        """Test multilingual and natural language time parsing."""
        # 24-hour and 12-hour standard
        self.assertEqual(_resolve_time("14:30"), "14:30")
        self.assertEqual(_resolve_time("7:00 PM"), "19:00")
        self.assertEqual(_resolve_time("7 PM"), "19:00")
        self.assertEqual(_resolve_time("10:00 AM"), "10:00")

        # Hindi & Marathi expressions
        self.assertEqual(_resolve_time("7 baje shaam"), "19:00")
        self.assertEqual(_resolve_time("shaam 7 baje"), "19:00")
        self.assertEqual(_resolve_time("subah 10 baje"), "10:00")
        self.assertEqual(_resolve_time("संध्याकाळी 7 वाजता"), "19:00")
        self.assertEqual(_resolve_time("सकाळी 10 वाजता"), "10:00")

    def test_prompt_builder(self):
        """Test dynamic prompt construction with all tenant metadata."""
        biz = new_business("u1", "Mumbai Spice", "Restaurant", "Fine Indian Dining", "MG Road", "9876543210")
        svcs = [new_service("b1", "Dinner Table", 90, 0.0)]
        resources = [new_resource("b1", "Table 1", "Table", 4)]
        ai_emp = new_ai_employee("b1", "Maya", "AI Hostess")

        prompt = build_system_prompt(biz, svcs, resources, ai_emp)
        self.assertIn("Maya", prompt)
        self.assertIn("Mumbai Spice", prompt)
        self.assertIn("Restaurant", prompt)
        self.assertIn("Dinner Table", prompt)
        self.assertIn("Table 1", prompt)
        self.assertIn("BEHAVIORAL RULES", prompt)
        self.assertIn("Hindi", prompt)
        self.assertIn("Marathi", prompt)

    def test_tool_declarations(self):
        """Verify all 10 tools are registered in declarations and function map."""
        expected_tools = [
            "get_business_information",
            "get_services",
            "get_service_details",
            "check_availability",
            "get_available_slots",
            "create_customer",
            "create_booking",
            "cancel_booking",
            "reschedule_booking",
            "request_human_handoff",
        ]
        declared_names = [t["name"] for t in TOOL_DECLARATIONS]
        for tool_name in expected_tools:
            self.assertIn(tool_name, declared_names)
            self.assertIn(tool_name, TOOL_FUNCTIONS)

    def test_tts_engine_multilingual(self):
        """Verify TTS engine generates speech for supported languages."""
        from voice.text_to_speech import tts_engine
        
        # Test generation to bytes for Hindi & Marathi
        hi_bytes = tts_engine.speak_to_bytes("नमस्ते, मैं आपकी क्या सहायता कर सकती हूँ?", "hi")
        self.assertIsNotNone(hi_bytes)
        self.assertGreater(len(hi_bytes), 100)

        en_bytes = tts_engine.speak_to_bytes("Hello, welcome to our business.", "en")
        self.assertIsNotNone(en_bytes)
        self.assertGreater(len(en_bytes), 100)


if __name__ == "__main__":
    unittest.main()
