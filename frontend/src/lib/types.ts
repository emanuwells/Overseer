export interface Pipeline {
  pipeline_id: string;
  pipeline_name?: string;
  name?: string;
  host_id?: string;
  owner?: string;
  schedule?: string;
  criticality?: string;
  runner_platform?: string;
  last_status?: string;
  last_started_at?: string;
  last_duration_sec?: number;
  last_run_id?: string;
  is_stale?: boolean;
  metadata?: Record<string, unknown>;
}

export interface Run {
  run_id: string;
  pipeline_id: string;
  host_id?: string;
  status?: string;
  started_at?: string;
  duration_sec?: number;
  pipeline_name?: string;
  name?: string;
  metadata?: Record<string, unknown>;
}

export interface RunModule {
  module_id: string;
  pipeline_id?: string;
  status?: string;
  started_at?: string;
  duration_sec?: number;
  error_message?: string;
}

export interface RunLog {
  created_at?: string;
  level?: string;
  message?: string;
}

export interface RunDetail {
  run?: Run;
  modules?: RunModule[];
  logs?: RunLog[];
}

export interface DatabaseInfo {
  reachable?: boolean;
  mode?: string;
  url?: string;
  tables?: Record<string, number>;
}

export interface OverviewData {
  summary?: {
    pipelines?: number;
    runs?: number;
    failed?: number;
    success_rate?: number;
  };
  pipelines?: Pipeline[];
  recent_runs?: Run[];
}

export interface DagNode {
  module_id: string;
  label?: string;
  type?: string;
  metadata?: Record<string, unknown>;
}

export interface DagEdge {
  from_module_id: string;
  to_module_id: string;
}

export interface DagPayload {
  pipeline?: Pipeline;
  nodes?: DagNode[];
  edges?: DagEdge[];
}

export interface Heartbeat {
  host_id?: string;
  hostname?: string;
  source_id?: string;
  source_type?: string;
  pipeline_id?: string;
  host_id_field?: string;
  seen_at?: string;
  status?: string;
  payload?: {
    task_scheduler?: TaskSchedulerSnapshot;
  };
}

export interface TaskSchedulerPipeline {
  pipeline_id?: string;
  host_id?: string;
  task_found?: boolean;
  task_path?: string;
  task_name?: string;
  expected_task_name?: string;
  state?: string;
  next_run_time?: string;
  last_task_result?: string | number | null;
}

export interface TaskSchedulerSnapshot {
  host_id?: string;
  ok?: boolean;
  error?: string;
  collected_at?: string;
  pipelines?: TaskSchedulerPipeline[];
}

export interface Trigger {
  trigger_id?: string;
  pipeline_id?: string;
  host_id?: string;
  status?: string;
}

export interface RunnerHost {
  host_id: string;
  platform?: string;
  ssh?: string;
  repo_path?: string;
}

export interface RunnerHostsPayload {
  hosts?: RunnerHost[];
  ssh_sync_enabled?: boolean;
}

declare global {
  interface Window {
    OVERSEER_CONFIG?: { apiToken?: string };
  }
}
