from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState


class SourceAuditAgent(BaseAgent):
    agent_name = "Source Audit Agent"
    stage = "source_audit"

    def build_content(self, state: GraphState) -> dict:
        return {
            "runtime_audit_log": artifact_ref("audit", "runtime_audit.log"),
            "trace_report": {
                "trace_id": state["metadata"]["trace_id"],
                "stages": ["source_runtime", "compliance_guard", "normalize"],
            },
            "runtime_exception_summary": [],
            "artifact_refs": [artifact_ref("audit", "runtime_audit.log")],
        }
