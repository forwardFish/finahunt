from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState


class DevelopmentAgent(BaseAgent):
    agent_name = "Development Agent"
    stage = "development"

    def build_content(self, state: GraphState) -> dict:
        artifacts = [
            artifact_ref("code", "agents"),
            artifact_ref("code", "graphs"),
            artifact_ref("code", "workflows"),
        ]
        return {
            "build_artifacts": artifacts,
            "code_package": "repo://finahunt",
            "dependency_manifest": ["langgraph", "pydantic", "PyYAML"],
            "dev_notes": "initial scaffold generated from design doc",
            "unit_test_report": artifact_ref("tests", "unit"),
            "artifact_refs": artifacts,
        }
