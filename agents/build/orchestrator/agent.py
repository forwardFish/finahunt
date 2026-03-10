from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_context
from packages.schema.state import GraphState


class FeatureOrchestratorAgent(BaseAgent):
    agent_name = "Feature Orchestrator Agent"
    stage = "orchestrator"

    def build_content(self, state: GraphState) -> dict:
        demand = get_context(state, "user_demand", state["input_ref"])
        subtasks = [
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
            "build_summary",
        ]
        return {
            "build_plan": {
                "goal": "deliver compliant information source access capability",
                "demand": demand,
                "subtasks": subtasks,
            },
            "subtask_list": subtasks,
            "execution_status": {task: "pending" for task in subtasks},
            "build_summary": "orchestration initialized",
            "artifact_refs": [artifact_ref("build", "build_plan.json")],
        }
