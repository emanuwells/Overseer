-- Formalizes Overseer schema (tables may already exist from orchestrator bootstrap).
-- Safe to run multiple times on MySQL 8+ / MariaDB 10.5+.

CREATE TABLE IF NOT EXISTS pipeline_runs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  scriptName VARCHAR(255),
  startDate DATETIME,
  endDate DATETIME,
  execTime VARCHAR(64),
  usageCPU DECIMAL(10,4),
  usageMemoria DECIMAL(10,4),
  status VARCHAR(32),
  errorMessage MEDIUMTEXT,
  logMessage MEDIUMTEXT,
  hostname VARCHAR(255),
  pipelineId VARCHAR(128),
  runId VARCHAR(128),
  attemptId VARCHAR(64),
  triggerType VARCHAR(64),
  owner VARCHAR(128),
  criticality VARCHAR(32),
  regDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_module_events (
  event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  pipelineId VARCHAR(128),
  runId VARCHAR(128),
  moduleId VARCHAR(255),
  parentModuleId VARCHAR(255),
  status VARCHAR(32),
  startedAt DATETIME,
  endedAt DATETIME,
  durationSec DECIMAL(12,3),
  errorMessage MEDIUMTEXT,
  logMessage MEDIUMTEXT,
  hostname VARCHAR(255),
  triggerType VARCHAR(64),
  contextJson JSON,
  regDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orchestrator_triggers_local (
  trigger_local_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  trigger_id VARCHAR(128) NOT NULL,
  trigger_type VARCHAR(64) DEFAULT 'run_now',
  pipeline_id VARCHAR(128) NOT NULL,
  requested_by VARCHAR(128),
  requested_by_sso VARCHAR(128),
  requested_at DATETIME,
  source VARCHAR(64),
  runner_host VARCHAR(128),
  status VARCHAR(32) DEFAULT 'queued',
  payload_json JSON,
  notes TEXT,
  claimed_by VARCHAR(128),
  claimed_at DATETIME,
  consumed_at DATETIME,
  error_message TEXT,
  created_at DATETIME,
  updated_at DATETIME,
  UNIQUE KEY uq_trigger_id (trigger_id)
);

CREATE TABLE IF NOT EXISTS orchestrator_runs_local (
  run_local_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  pipeline_id VARCHAR(128),
  pipeline_name VARCHAR(255),
  status VARCHAR(32),
  trigger_source VARCHAR(64),
  requested_by VARCHAR(128),
  requested_by_sso VARCHAR(128),
  runner_host VARCHAR(128),
  started_at DATETIME,
  ended_at DATETIME,
  error_message TEXT,
  created_at DATETIME,
  updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS pipeline_catalog (
  pipeline_id VARCHAR(128) PRIMARY KEY,
  name VARCHAR(255),
  owner VARCHAR(128),
  criticality VARCHAR(32),
  schedule VARCHAR(128),
  runner_host VARCHAR(128),
  active TINYINT DEFAULT 1,
  updated_at DATETIME
);
