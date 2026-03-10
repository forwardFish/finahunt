from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState


class AuditAgent(BaseAgent):
    agent_name = "Audit Agent"
    stage = "governance_audit"

    def build_content(self, state: GraphState) -> dict:
        risk_findings = []
        for stage, result in state.get("results", {}).items():
            if result.get("status") == "fail":
                risk_findings.append(
                    {
                        "stage": stage,
                        "risk_level": "high",
                        "issue": "agent execution failed",
                    }
                )
        return {
            "full_audit_report": {
                "checked_stages": list(state.get("results", {}).keys()),
                "trace_id": state["metadata"]["trace_id"],
            },
            "risk_findings": risk_findings,
            "audit_trail": artifact_ref("audit", "full_audit.log"),
            "rectification_suggestions": [
                "replace local audit persistence with managed storage before production"
            ],
            "artifact_refs": [artifact_ref("audit", "full_audit.log")],
        }
