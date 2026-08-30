"""
SAATHI ONE — Database Layer
MongoDB connection manager with tenant-isolated collection accessors.
"""

from pymongo import MongoClient, ASCENDING
from config import MONGODB_URI, DATABASE_NAME

# ---------------------------------------------------------------------------
# Singleton connection
# ---------------------------------------------------------------------------
_client = None
_db = None


def get_client():
    """Return the MongoClient singleton (connection pooled)."""
    global _client
    if _client is None:
        _client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,   # fail fast if unreachable
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=10,
        )
    return _client


def get_db():
    """Return the database handle."""
    global _db
    if _db is None:
        _db = get_client()[DATABASE_NAME]
    return _db


# ---------------------------------------------------------------------------
# Collection accessors
# ---------------------------------------------------------------------------
def users_col():
    return get_db()["users"]


def businesses_col():
    return get_db()["businesses"]


def services_col():
    return get_db()["services"]


def resources_col():
    return get_db()["resources"]


def bookings_col():
    return get_db()["bookings"]


def customers_col():
    return get_db()["customers"]


def ai_employees_col():
    return get_db()["ai_employees"]


def demo_numbers_col():
    return get_db()["demo_numbers"]


def calls_col():
    return get_db()["calls"]


def conversations_col():
    return get_db()["conversations"]


def tool_executions_col():
    return get_db()["tool_executions"]


# ---------------------------------------------------------------------------
# Index creation — run once on startup
# ---------------------------------------------------------------------------
def ensure_indexes():
    """Create indexes for tenant isolation and common queries."""
    def _safe_create_index(col, keys, **kwargs):
        try:
            col.create_index(keys, **kwargs)
        except Exception:
            pass

    # Drop legacy conflicting indexes if present
    for legacy_idx in ["bookingRef_1", "idempotency_key_1"]:
        try:
            if legacy_idx in bookings_col().index_information():
                bookings_col().drop_index(legacy_idx)
        except Exception:
            pass

    # Tenant isolation indexes
    _safe_create_index(businesses_col(), [("owner_id", ASCENDING)])
    _safe_create_index(services_col(), [("business_id", ASCENDING)])
    _safe_create_index(resources_col(), [("business_id", ASCENDING)])
    _safe_create_index(bookings_col(), [("business_id", ASCENDING), ("date", ASCENDING)])
    _safe_create_index(bookings_col(), [("business_id", ASCENDING), ("status", ASCENDING)])
    _safe_create_index(customers_col(), [("business_id", ASCENDING)])
    _safe_create_index(customers_col(), [("business_id", ASCENDING), ("phone", ASCENDING)])
    _safe_create_index(ai_employees_col(), [("business_id", ASCENDING)], unique=True)
    _safe_create_index(demo_numbers_col(), [("number", ASCENDING)], unique=True)
    _safe_create_index(demo_numbers_col(), [("business_id", ASCENDING)], unique=True)
    _safe_create_index(calls_col(), [("business_id", ASCENDING), ("started_at", ASCENDING)])
    _safe_create_index(conversations_col(), [("call_id", ASCENDING)])
    _safe_create_index(tool_executions_col(), [("business_id", ASCENDING)])

    # Auth indexes
    _safe_create_index(users_col(), [("email", ASCENDING)], unique=True)


_connection_ok: bool | None = None

def check_connection():
    """Test the MongoDB connection. Cached after first success."""
    global _connection_ok
    if _connection_ok is True:
        return True  # Already verified — skip repeat ping
    try:
        get_client().admin.command("ping")
        _connection_ok = True
        return True
    except Exception:
        _connection_ok = None   # Allow retry next time
        return False
