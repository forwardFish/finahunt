from __future__ import annotations

import json
from pathlib import Path

from packages.schema.state import GraphState


class FileCheckpointStore:
    """Simple filesystem checkpoint store for local development."""

    def __init__(self, root: str = "workspace/artifacts/checkpoints") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, state: GraphState) -> Path:
        path = self.root / f"{state['task_id']}-{state['run_id']}.json"
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, task_id: str, run_id: str) -> GraphState:
        path = self.root / f"{task_id}-{run_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))
