from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState


class NormalizeAgent(BaseAgent):
    agent_name = "Normalize Agent"
    stage = "normalize"

    def build_content(self, state: GraphState) -> dict:
        return {
            "normalized_documents": artifact_ref("runtime", "normalized_documents.json"),
            "format_validation_report": {
                "contract_version": "v1",
                "valid": True,
            },
            "normalize_failure_record": [],
            "artifact_refs": [artifact_ref("runtime", "normalized_documents.json")],
        }
