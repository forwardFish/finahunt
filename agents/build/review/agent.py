from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import get_result
from packages.schema.state import GraphState
from skills.code_review import review_artifacts


class ReviewAgent(BaseAgent):
    agent_name = "Review Agent"
    stage = "review"

    def build_content(self, state: GraphState) -> dict:
        development = get_result(state, "development")
        review = review_artifacts(development.get("build_artifacts", []))
        return {
            "review_report": "scaffold structure aligns with architecture and contract spec",
            "blocking_issues": review["blocking_issues"],
            "refactor_suggestions": [
                "replace file checkpoint store with PostgreSQL in production",
            ],
            "review_pass": review["review_pass"],
            "artifact_refs": development.get("build_artifacts", []),
        }
