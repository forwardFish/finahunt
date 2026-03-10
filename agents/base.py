from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from packages.audit.logger import AuditLogger
from packages.schema.models import AgentError, AgentOutput, AgentStatus
from packages.schema.state import GraphState


class BaseAgent(ABC):
    """Shared execution wrapper for all plane agents."""

    agent_name: str
    stage: str
    agent_version: str = "v1"

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self.audit_logger = audit_logger or AuditLogger()

    def __call__(self, state: GraphState) -> GraphState:
        started_at = datetime.now(UTC)
        try:
            content = self.build_content(state)
            output = AgentOutput(
                task_id=state["task_id"],
                run_id=state["run_id"],
                stage=self.stage,
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                rule_version=state["rule_version"],
                status=AgentStatus.SUCCESS,
                content=content,
                artifact_refs=content.get("artifact_refs", []),
                metadata={
                    "start_time": started_at.isoformat(),
                    "end_time": datetime.now(UTC).isoformat(),
                    "trace_id": state["metadata"]["trace_id"],
                    "upstream_dependency": state.get("stage", ""),
                },
            )
        except Exception as exc:  # pragma: no cover - defensive path
            error = AgentError(
                error_type=type(exc).__name__,
                error_msg=str(exc),
                error_source=self.agent_name,
                impact_scope=self.stage,
            )
            output = AgentOutput(
                task_id=state["task_id"],
                run_id=state["run_id"],
                stage=self.stage,
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                rule_version=state["rule_version"],
                status=AgentStatus.FAIL,
                content={},
                error=error,
                metadata={
                    "start_time": started_at.isoformat(),
                    "end_time": datetime.now(UTC).isoformat(),
                    "trace_id": state["metadata"]["trace_id"],
                    "upstream_dependency": state.get("stage", ""),
                },
            )

        updated_results = dict(state.get("results", {}))
        updated_results[self.stage] = output.model_dump(mode="json")
        next_state: GraphState = {
            **state,
            "stage": self.stage,
            "status": output.status.value,
            "output_ref": f"state://results/{self.stage}",
            "results": updated_results,
            "artifact_refs": [
                *state.get("artifact_refs", []),
                *output.artifact_refs,
            ],
            "metadata": {
                **state["metadata"],
                "last_agent": self.agent_name,
                "last_stage": self.stage,
                "updated_at": datetime.now(UTC).isoformat(),
            },
        }
        if output.error:
            next_state["error"] = output.error.model_dump(mode="json")
        self.audit_logger.log_agent_output(output)
        return next_state

    @abstractmethod
    def build_content(self, state: GraphState) -> dict[str, Any]:
        """Return the structured content body for the agent."""


class StaticAgent(BaseAgent):
    """Convenience agent for deterministic scaffold outputs."""

    def __init__(self, payload_builder, audit_logger: AuditLogger | None = None) -> None:
        super().__init__(audit_logger=audit_logger)
        self._payload_builder = payload_builder

    def build_content(self, state: GraphState) -> dict[str, Any]:
        return self._payload_builder(state)
