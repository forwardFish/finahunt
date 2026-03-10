from __future__ import annotations

from agents.base import BaseAgent
from packages.schema.state import GraphState
from skills.test_execution import run_test_suite


class TestAgent(BaseAgent):
    agent_name = "Test Agent"
    stage = "test"

    def build_content(self, state: GraphState) -> dict:
        suite = run_test_suite(["tests/unit", "tests/integration", "tests/e2e"])
        return {
            "functional_test_report": suite["reports"][0],
            "contract_test_report": suite["reports"][1],
            "compliance_test_report": suite["reports"][2],
            "reliability_test_report": "report://reliability",
            "test_pass": suite["passed"],
            "artifact_refs": suite["reports"],
        }
