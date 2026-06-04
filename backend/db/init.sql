-- ============================================================
-- NBA Enterprise AI Platform — PostgreSQL Initialisation
-- Runs once on first container start.
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Default search path
ALTER DATABASE nba_platform SET search_path TO public;

-- Permissions
GRANT ALL PRIVILEGES ON DATABASE nba_platform TO nba_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nba_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nba_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nba_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nba_admin;
