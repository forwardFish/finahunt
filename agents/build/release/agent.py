from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState


class ReleaseAgent(BaseAgent):
    agent_name = "Release Agent"
    stage = "release"

    def build_content(self, state: GraphState) -> dict:
        approval = get_result(state, "human_approval")
        approved = approval.get("approved", False)
        return {
            "release_report": {
                "release_status": "released" if approved else "blocked",
                "strategy": "canary",
            },
            "rollout_log": artifact_ref("deploy", "rollout.log"),
            "rollback_log_if_any": "",
            "release_pass": approved,
            "artifact_refs": [artifact_ref("deploy", "release_report.json")],
        }
