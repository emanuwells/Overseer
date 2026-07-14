-- Idempotent host_id column migration (MariaDB / MySQL).
-- Prefer: python scripts/migrate_pipeline_host_suffix.py (also rewrites legacy suffix data).

ALTER TABLE overseer_pipelines ADD COLUMN IF NOT EXISTS host_id VARCHAR(128) NOT NULL DEFAULT '';
ALTER TABLE overseer_runs ADD COLUMN IF NOT EXISTS host_id VARCHAR(128) NOT NULL DEFAULT '';
ALTER TABLE overseer_modules ADD COLUMN IF NOT EXISTS host_id VARCHAR(128) NOT NULL DEFAULT '';
ALTER TABLE overseer_logs ADD COLUMN IF NOT EXISTS host_id VARCHAR(128) NULL DEFAULT '';
ALTER TABLE overseer_heartbeats ADD COLUMN IF NOT EXISTS host_id VARCHAR(128) NULL DEFAULT '';
ALTER TABLE overseer_triggers ADD COLUMN IF NOT EXISTS host_id VARCHAR(128) NOT NULL DEFAULT '';
