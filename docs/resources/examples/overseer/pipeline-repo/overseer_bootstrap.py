from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from overseer_sdk import OverseerClient


def load_env_file(path: str = ".env.overseer") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


class PipelineOverseer:
    def __init__(self) -> None:
        load_env_file()
        self.pipeline_id = os.getenv("OVERSEER_PIPELINE_ID", "unknown_pipeline")
        self.pipeline_name = os.getenv("OVERSEER_PIPELINE_NAME", self.pipeline_id)
        self.owner = os.getenv("OVERSEER_PIPELINE_OWNER", "data")
        self.criticality = os.getenv("OVERSEER_PIPELINE_CRITICALITY", "medium")
        self.schedule = os.getenv("OVERSEER_PIPELINE_SCHEDULE", "manual")
        self.client = OverseerClient()

    def register_catalog(self, *, nodes: list[dict], edges: list[dict]) -> dict:
        return self.client.register_pipeline(
            pipeline_id=self.pipeline_id,
            name=self.pipeline_name,
            owner=self.owner,
            criticality=self.criticality,
            schedule=self.schedule,
            nodes=nodes,
            edges=edges,
        )

    @contextmanager
    def run(self, trigger_type: str = "pipeline"):
        with self.client.run(
            self.pipeline_id,
            pipeline_name=self.pipeline_name,
            trigger_type=trigger_type,
            requested_by=os.getenv("USER") or os.getenv("USERNAME") or "pipeline",
        ) as run_id:
            yield run_id

    @contextmanager
    def step(self, run_id: str, module_id: str):
        with self.client.step(run_id=run_id, pipeline_id=self.pipeline_id, module_id=module_id):
            yield

    def log(self, run_id: str, message: str, *, module_id: str | None = None, level: str = "info") -> None:
        self.client.log(
            message,
            run_id=run_id,
            pipeline_id=self.pipeline_id,
            module_id=module_id,
            level=level,
        )


overseer = PipelineOverseer()
