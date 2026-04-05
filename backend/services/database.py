"""
services/database.py — PathFinder AI  ·  MongoDB Integration
=============================================================
Async MongoDB client using Motor.  Provides connection lifecycle management
and three high-level helpers for the reports collection.

Connection lifecycle
--------------------
connect_db()    called from main.py lifespan on startup
disconnect_db() called from main.py lifespan on shutdown

Report helpers
--------------
save_report(report)          → str          inserts, returns UUID report_id
get_report(report_id)        → dict | None  finds by report_id field (not _id)
list_reports(limit)          → list[dict]   most recent N reports

Design notes
------------
- MongoDB _id (ObjectId) is always excluded from returned dicts — callers
  never see it, which avoids JSON serialisation errors.
- report_id is a UUID4 string we generate ourselves; _id is MongoDB's internal key.
- All functions are safe to call even when MongoDB is not available — they
  raise RuntimeError with a clear message rather than crashing silently.
- Datetime fields are stored as Python datetime objects (UTC) so MongoDB
  can sort them natively, but they are serialised to ISO-8601 strings for the API.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import settings

logger = logging.getLogger(__name__)

# ── Module-level singletons — set by connect_db(), cleared by disconnect_db() ─
_client: AsyncIOMotorClient | None = None
_db:     AsyncIOMotorDatabase | None = None

# Collection name constants
REPORTS_COLLECTION = "reports"


# ══════════════════════════════════════════════════════════════════════════════
#  CONNECTION LIFECYCLE
# ══════════════════════════════════════════════════════════════════════════════

async def connect_db() -> None:
    """
    Open the MongoDB connection and verify it with a ping.

    Called automatically from main.py lifespan on server startup.
    Sets module-level ``_client`` and ``_db`` singletons.

    Raises
    ------
    Exception
        If the connection cannot be established (wrong URL, auth failure, etc.)
        The caller (lifespan) catches this and logs a warning.
    """
    global _client, _db
    _client = AsyncIOMotorClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=5000,   # fail fast if MongoDB is unreachable
    )
    _db = _client[settings.mongodb_db_name]
    # Ping confirms the connection is live (raises if not)
    await _client.admin.command("ping")

    # Ensure indexes for common query patterns
    await _db[REPORTS_COLLECTION].create_index("report_id", unique=True)
    await _db[REPORTS_COLLECTION].create_index([("created_at", -1)])   # sort by newest

    logger.info(f"Connected to MongoDB: {settings.mongodb_db_name}")


async def disconnect_db() -> None:
    """
    Close the MongoDB connection cleanly.
    Called from main.py lifespan on server shutdown.
    """
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db     = None
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the active database instance.

    Can be used as a FastAPI dependency:
        db = Depends(get_database)

    Returns
    -------
    AsyncIOMotorDatabase

    Raises
    ------
    RuntimeError
        If connect_db() has not been called yet (e.g. during testing without
        a real MongoDB).
    """
    if _db is None:
        raise RuntimeError(
            "MongoDB is not connected. "
            "Ensure connect_db() was called during application startup, "
            "or that MONGODB_URL is set correctly in .env."
        )
    return _db


# ══════════════════════════════════════════════════════════════════════════════
#  SERIALISATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _clean_doc(doc: dict) -> dict:
    """
    Remove MongoDB's internal ``_id`` field and convert any ObjectId or
    datetime values to JSON-safe types.

    Parameters
    ----------
    doc : dict
        Raw document from Motor (may contain _id, ObjectId, datetime).

    Returns
    -------
    dict
        Clean dict safe for Pydantic / JSON serialisation.
    """
    if doc is None:
        return {}
    cleaned = {}
    for key, value in doc.items():
        if key == "_id":
            continue                          # never expose _id
        if isinstance(value, ObjectId):
            cleaned[key] = str(value)
        elif isinstance(value, datetime):
            cleaned[key] = value.isoformat()  # → "2025-01-15T10:30:00+00:00"
        elif isinstance(value, dict):
            cleaned[key] = _clean_doc(value)  # recurse for nested dicts
        elif isinstance(value, list):
            cleaned[key] = [
                _clean_doc(i) if isinstance(i, dict) else i
                for i in value
            ]
        else:
            cleaned[key] = value
    return cleaned


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT CRUD OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

async def save_report(report: dict) -> str:
    """
    Insert a full analysis report into the ``reports`` collection.

    The ``report`` dict should already contain a ``report_id`` (UUID4 string)
    and a ``created_at`` (datetime) field — both generated by the caller.

    Parameters
    ----------
    report : dict
        The full_report dict assembled by the pipeline endpoint.

    Returns
    -------
    str
        The ``report_id`` (UUID4 string) that was saved.
        Use this to retrieve the report later via get_report().

    Raises
    ------
    RuntimeError
        If MongoDB is not connected.
    Exception
        If the insert fails (duplicate key, write error, etc.).
    """
    db         = get_database()
    collection = db[REPORTS_COLLECTION]

    # Make a copy so we don't mutate the caller's dict
    doc = dict(report)

    # Ensure created_at is stored as a native datetime for MongoDB sorting
    if isinstance(doc.get("created_at"), str):
        try:
            doc["created_at"] = datetime.fromisoformat(doc["created_at"])
        except ValueError:
            doc["created_at"] = datetime.now(timezone.utc)

    result = await collection.insert_one(doc)
    report_id = str(doc.get("report_id", str(result.inserted_id)))

    logger.info(f"Report saved — report_id: {report_id}, _id: {result.inserted_id}")
    return report_id


async def get_report(report_id: str) -> dict | None:
    """
    Retrieve a single report by its ``report_id`` field (UUID4 string).

    Note: this queries by our own ``report_id`` field, NOT by MongoDB's ``_id``.

    Parameters
    ----------
    report_id : str
        The UUID4 string assigned at save time.

    Returns
    -------
    dict or None
        The report document with ``_id`` excluded, or None if not found.

    Raises
    ------
    RuntimeError
        If MongoDB is not connected.
    """
    db         = get_database()
    collection = db[REPORTS_COLLECTION]

    # Projection: exclude _id explicitly
    doc = await collection.find_one(
        {"report_id": report_id},
        {"_id": 0},           # exclude _id from result
    )
    if doc is None:
        logger.debug(f"Report not found: {report_id}")
        return None

    return _clean_doc(doc)


async def list_reports(limit: int = 10) -> list[dict]:
    """
    Return the most recent ``limit`` reports, sorted newest-first.

    Used by the demo listing endpoint GET /api/analysis/.

    Parameters
    ----------
    limit : int
        Maximum number of reports to return (default 10, capped at 50).

    Returns
    -------
    list[dict]
        List of report dicts with ``_id`` excluded and datetimes as ISO strings.
        Each dict is a lightweight summary — full bridge_skills / xai_explanations
        lists are preserved but four_week_plan is included in full.

    Raises
    ------
    RuntimeError
        If MongoDB is not connected.
    """
    limit = min(limit, 50)   # hard cap to avoid accidentally dumping the whole collection
    db         = get_database()
    collection = db[REPORTS_COLLECTION]

    cursor = collection.find(
        {},
        {"_id": 0},                          # exclude _id
    ).sort("created_at", -1).limit(limit)    # newest first

    docs = await cursor.to_list(length=limit)
    return [_clean_doc(doc) for doc in docs]