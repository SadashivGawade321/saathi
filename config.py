"""
SAATHI ONE — Configuration
Central configuration loaded from environment variables.
"""

import os
from dotenv import load_dotenv

# Load .env file (local development)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Also load from Streamlit secrets (Streamlit Cloud deployment)
def _get_secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, then env vars, then default."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
GEMINI_API_KEY = _get_secret("GEMINI_API_KEY")
MONGODB_URI    = _get_secret("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME  = _get_secret("DATABASE_NAME", "saathi_one")

# ---------------------------------------------------------------------------
# Groq API (Primary — fast, free, no quota)
# ---------------------------------------------------------------------------
GROQ_API_KEY = _get_secret("GROQ_API_KEY", "")
GROQ_MODEL = "qwen/qwen3.8-27b"          # Supports tool calling — confirmed working
GROQ_FALLBACK_MODEL = "qwen/qwen3.6-27b"  # Fallback

# ---------------------------------------------------------------------------
# Gemini Model & Fallbacks (backup)
# ---------------------------------------------------------------------------
GEMINI_MODEL = "gemini-3.6-flash"
FALLBACK_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
]

# ---------------------------------------------------------------------------
# Supported Languages
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}

# Language codes for Google STT / TTS
LANGUAGE_CODES_STT = {
    "en": "en-IN",
    "hi": "hi-IN",
    "mr": "mr-IN",
}

LANGUAGE_CODES_TTS = {
    "en": "en",
    "hi": "hi",
    "mr": "mr",
}

# ---------------------------------------------------------------------------
# Business Types
# ---------------------------------------------------------------------------
BUSINESS_TYPES = [
    "Restaurant",
    "Barber",
    "Salon",
    "Clinic",
    "Doctor",
    "Dentist",
    "Hotel",
    "Gym",
    "Consultant",
    "Repair Service",
    "Other",
]

# ---------------------------------------------------------------------------
# Business Capabilities
# ---------------------------------------------------------------------------
ALL_CAPABILITIES = [
    "booking",
    "availability",
    "cancellation",
    "rescheduling",
    "business_information",
    "service_information",
    "customer_registration",
    "human_handoff",
]

DEFAULT_CAPABILITIES = {
    "booking": True,
    "availability": True,
    "cancellation": True,
    "rescheduling": True,
    "business_information": True,
    "service_information": True,
    "customer_registration": True,
    "human_handoff": True,
}

# ---------------------------------------------------------------------------
# Booking
# ---------------------------------------------------------------------------
BOOKING_STATUSES = [
    "confirmed",
    "cancelled",
    "completed",
    "no_show",
]

BOOKING_SOURCES = [
    "ai_voice",
    "dashboard",
]

DEFAULT_SLOT_DURATION_MINUTES = 30

# ---------------------------------------------------------------------------
# Demo Number
# ---------------------------------------------------------------------------
DEMO_NUMBER_PREFIX = "DEMO"
DEMO_NUMBER_START = 9001

# ---------------------------------------------------------------------------
# Resource Types (maps business type to typical resource label)
# ---------------------------------------------------------------------------
RESOURCE_TYPE_LABELS = {
    "Restaurant": "Table",
    "Barber": "Barber",
    "Salon": "Stylist",
    "Clinic": "Doctor",
    "Doctor": "Doctor",
    "Dentist": "Dentist",
    "Hotel": "Room",
    "Gym": "Trainer",
    "Consultant": "Consultant",
    "Repair Service": "Technician",
    "Other": "Resource",
}

# ---------------------------------------------------------------------------
# Default Working Hours
# ---------------------------------------------------------------------------
DEFAULT_WORKING_HOURS = {
    "monday":    {"open": "09:00", "close": "23:00", "is_open": True},
    "tuesday":   {"open": "09:00", "close": "23:00", "is_open": True},
    "wednesday": {"open": "09:00", "close": "23:00", "is_open": True},
    "thursday":  {"open": "09:00", "close": "23:00", "is_open": True},
    "friday":    {"open": "09:00", "close": "23:00", "is_open": True},
    "saturday":  {"open": "09:00", "close": "23:00", "is_open": True},
    "sunday":    {"open": "09:00", "close": "23:00", "is_open": True},
}
