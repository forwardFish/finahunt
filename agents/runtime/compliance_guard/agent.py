from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.compliance_check import evaluate_content


class SourceComplianceGuardAgent(BaseAgent):
    agent_name = "Source Compliance Guard Agent"
    stage = "compliance_guard"

    def build_content(self, state: GraphState) -> dict:
        rules = load_yaml("config/rules/compliance_rules.yaml")
        sample = evaluate_content("official public announcement", rules["blocking_rules"]["blocked_terms"])
        return {
            "allowed_documents": [artifact_ref("runtime", "raw_documents.json")],
            "blocked_documents": [] if sample["passed"] else sample["violations"],
            "compliance_runtime_log": artifact_ref("audit", "compliance_runtime.log"),
            "artifact_refs": [artifact_ref("audit", "compliance_runtime.log")],
        }
