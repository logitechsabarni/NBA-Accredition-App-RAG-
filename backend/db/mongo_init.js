// ============================================================
// NBA Enterprise AI Platform — MongoDB Initialisation
// Runs once on first container start.
// ============================================================

db = db.getSiblingDB("nba_platform_nosql");

db.createCollection("workflow_audit");
db.createCollection("chat_history");
db.createCollection("analytics_cache");
db.createCollection("agent_traces");

// TTL index on analytics_cache
db.analytics_cache.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });

print("MongoDB collections initialised.");
