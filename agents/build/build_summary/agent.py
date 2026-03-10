from __future__ import annotations

from agents.base import BaseAgent
from packages.schema.state import GraphState


class BuildSummaryAgent(BaseAgent):
    agent_name = "Build Summary Agent"
    stage = "build_summary"

    def build_content(self, state: GraphState) -> dict:
        build_results = {
            key: value
            for key, value in state.get("results", {}).items()
            if key
            in {
                "orchestrator",
                "requirement_parsing",
                "compliance_rules",
                "source_registry",
                "architecture",
                "contract",
                "development",
                "review",
                "test",
                "deploy_staging",
                "human_approval",
                "release",
            }
        }
        return {
            "build_summary_report": build_results,
            "full_artifact_list": state.get("artifact_refs", []),
            "key_milestone_result": {
                "review_pass": build_results.get("review", {}).get("content", {}).get("review_pass", False),
                "test_pass": build_results.get("test", {}).get("content", {}).get("test_pass", False),
                "release_pass": build_results.get("release", {}).get("content", {}).get("release_pass", False),
            },
            "artifact_refs": state.get("artifact_refs", []),
        }
