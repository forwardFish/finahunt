from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from packages.schema.models import AgentStatus, GlobalStateModel
from packages.schema.state import GraphState


class StateManager:
    """Factory and helpers for graph state objects."""

    @staticmethod
    def new_state(
        graph_type: str,
        input_ref: str,
        rule_version: str = "v1",
        task_id: str | None = None,
        run_id: str | None = None,
        context: dict | None = None,
    ) -> GraphState:
        now = datetime.now(UTC).isoformat()
        state = GlobalStateModel(
            task_id=task_id or f"task-{uuid4().hex[:12]}",
            run_id=run_id or f"run-{uuid4().hex[:12]}",
            graph_type=graph_type,  # type: ignore[arg-type]
            stage="start",
            status=AgentStatus.PENDING,
            input_ref=input_ref,
            rule_version=rule_version,
            metadata={
                "trace_id": f"trace-{uuid4().hex}",
                "created_at": now,
                "updated_at": now,
            },
            context=context or {},
        )
        return state.model_dump(mode="json")
