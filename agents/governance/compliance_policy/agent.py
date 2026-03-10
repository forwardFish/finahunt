from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState


class CompliancePolicyAgent(BaseAgent):
    agent_name = "Compliance Policy Agent"
    stage = "compliance_policy"

    def build_content(self, state: GraphState) -> dict:
        return {
            "policy_enforcement_log": artifact_ref("audit", "policy_enforcement.log"),
            "violation_record": [],
            "block_action": [],
            "compliance_alert": [],
            "artifact_refs": [artifact_ref("audit", "policy_enforcement.log")],
        }
