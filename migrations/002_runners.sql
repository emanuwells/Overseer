CREATE TABLE IF NOT EXISTS overseer_runners (
  hostname VARCHAR(255) PRIMARY KEY,
  os_name VARCHAR(64),
  os_release VARCHAR(128),
  agent_version VARCHAR(32),
  last_seen_at DATETIME,
  created_at DATETIME,
  updated_at DATETIME
);
