from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState
from packages.utils import load_yaml


class ComplianceRulesAgent(BaseAgent):
    agent_name = "Compliance Rules Agent"
    stage = "compliance_rules"

    def build_content(self, state: GraphState) -> dict:
        rules = load_yaml("config/rules/compliance_rules.yaml")
        return {
            "compliance_policy": rules["compliance_policy"],
            "source_whitelist_policy": rules["source_whitelist_policy"],
            "field_capture_policy": rules["field_capture_policy"],
            "blocking_rules": rules["blocking_rules"],
            "rule_version": state["rule_version"],
            "artifact_refs": [artifact_ref("rules", "compliance_rules.yaml")],
        }
