"""
NBA Enterprise AI Platform — Audit Logger
Writes immutable audit events to MongoDB for compliance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from db.mongodb import COLLECTION_WORKFLOW_AUDIT, get_mongo_db
from config.logging_config import get_logger

logger = get_logger(__name__)


async def write_audit_log(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    workflow_type: Optional[str] = None,
    session_id: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    output_summary: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Write an immutable audit record to MongoDB.
    Returns the audit record ID.
    """
    audit_id = str(uuid4())
    record = {
        "_id": audit_id,
        "audit_id": audit_id,
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "workflow_type": workflow_type,
        "session_id": session_id,
        "input_data": input_data,
        "output_summary": output_summary,
        "status": status,
        "error_message": error_message,
        "metadata": metadata or {},
        "created_at": datetime.now(tz=timezone.utc),
    }
    try:
        db = get_mongo_db()
        await db[COLLECTION_WORKFLOW_AUDIT].insert_one(record)
    except Exception as exc:
        logger.error("Failed to write audit log", error=str(exc), audit_id=audit_id)
    return audit_id


async def get_audit_logs(
    user_id: Optional[str] = None,
    workflow_type: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> list:
    db = get_mongo_db()
    query: Dict[str, Any] = {}
    if user_id:
        query["user_id"] = user_id
    if workflow_type:
        query["workflow_type"] = workflow_type

    cursor = (
        db[COLLECTION_WORKFLOW_AUDIT]
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
