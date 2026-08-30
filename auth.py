"""
SAATHI ONE — Authentication
Simple email/password auth with bcrypt, stored in MongoDB.
Uses Streamlit session_state for session management.
"""

import bcrypt
import streamlit as st
from database import users_col
from models import new_user


# ---------------------------------------------------------------------------
# Core auth functions
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def register_user(email: str, password: str, name: str = "") -> dict | None:
    """Register a new user. Returns user doc or None if email exists."""
    email = email.strip().lower()
    if users_col().find_one({"email": email}):
        return None
    user_doc = new_user(email, hash_password(password), name)
    result = users_col().insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc


def login_user(email: str, password: str) -> dict | None:
    """Authenticate user. Returns user doc or None."""
    email = email.strip().lower()
    user = users_col().find_one({"email": email})
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
def init_session():
    """Initialize auth-related session state."""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "user_email": None,
        "user_name": None,
        "business_id": None,
        "business_name": None,
        "auth_page": "login",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def set_authenticated(user: dict):
    """Set session after successful login."""
    st.session_state.authenticated = True
    st.session_state.user_id = str(user["_id"])
    st.session_state.user_email = user["email"]
    st.session_state.user_name = user.get("name", "")


def logout():
    """Clear session."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def require_auth():
    """Returns True if user is authenticated, False otherwise."""
    return st.session_state.get("authenticated", False)


def get_current_user_id() -> str | None:
    return st.session_state.get("user_id")


def get_current_business_id() -> str | None:
    return st.session_state.get("business_id")


def set_current_business(business: dict):
    """Set the active business in session."""
    st.session_state.business_id = str(business["_id"])
    st.session_state.business_name = business["name"]
