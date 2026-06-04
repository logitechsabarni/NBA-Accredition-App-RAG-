"""
NBA Enterprise AI Platform — MongoDB Async Client
Motor-based async client for workflow audits, chat history,
and analytics cache collections.
"""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

# Collection name constants
COLLECTION_WORKFLOW_AUDIT = "workflow_audit"
COLLECTION_CHAT_HISTORY = "chat_history"
COLLECTION_ANALYTICS_CACHE = "analytics_cache"
COLLECTION_AGENT_TRACES = "agent_traces"


class MongoDBClient:
    """Singleton-style async MongoDB client wrapper."""

    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        if cls._client is not None:
            return
        cls._client = AsyncIOMotorClient(
            settings.db.MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=5,
        )
        cls._db = cls._client[settings.db.MONGO_DB]
        await cls._ensure_indexes()
        logger.info("MongoDB connected", db=settings.db.MONGO_DB)

    @classmethod
    async def disconnect(cls) -> None:
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB disconnected")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        if cls._db is None:
            raise RuntimeError("MongoDB client not initialised. Call connect() first.")
        return cls._db

    @classmethod
    async def _ensure_indexes(cls) -> None:
        db = cls._db

        # workflow_audit indexes
        await db[COLLECTION_WORKFLOW_AUDIT].create_indexes([
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("workflow_type", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("session_id", ASCENDING)]),
        ])

        # chat_history indexes
        await db[COLLECTION_CHAT_HISTORY].create_indexes([
            IndexModel([("user_id", ASCENDING)]),
            IndexModel([("session_id", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ])

        # analytics_cache indexes
        await db[COLLECTION_ANALYTICS_CACHE].create_indexes([
            IndexModel([("cache_key", ASCENDING)], unique=True),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
        ])

        # agent_traces indexes
        await db[COLLECTION_AGENT_TRACES].create_indexes([
            IndexModel([("trace_id", ASCENDING)], unique=True),
            IndexModel([("agent_name", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ])

        logger.info("MongoDB indexes ensured")


def get_mongo_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency: return the active MongoDB database."""
    return MongoDBClient.get_db()
