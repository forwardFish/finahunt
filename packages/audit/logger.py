from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from packages.schema.models import AgentOutput


class AuditLogger:
    """Write append-only audit records for agent execution."""

    def __init__(self, root: str = "workspace/audit") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "audit.log"

    def log_agent_output(self, output: AgentOutput) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": output.task_id,
            "run_id": output.run_id,
            "agent_name": output.agent_name,
            "stage": output.stage,
            "status": output.status.value,
            "trace_id": output.metadata.get("trace_id", ""),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
