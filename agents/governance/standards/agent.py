from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState
from packages.utils import load_yaml


class StandardsAgent(BaseAgent):
    agent_name = "Standards Agent"
    stage = "standards"

    def build_content(self, state: GraphState) -> dict:
        standards = load_yaml("config/rules/standards.yaml")
        return {
            "standards_manual": standards["standards_manual"],
            "standard_version": standards["standard_version"],
            "standard_update_log": standards["standard_update_log"],
            "standard_violation_rules": standards["standard_violation_rules"],
            "artifact_refs": [artifact_ref("rules", "standards.yaml")],
        }
