from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_context
from packages.schema.state import GraphState


class RequirementParsingAgent(BaseAgent):
    agent_name = "Requirement Parsing Agent"
    stage = "requirement_parsing"

    def build_content(self, state: GraphState) -> dict:
        demand = get_context(state, "user_demand", state["input_ref"])
        return {
            "requirement_spec": {
                "problem_statement": demand,
                "scope": "compliant information source onboarding and runtime processing",
                "success_criteria": [
                    "strong compliance enforcement",
                    "traceable outputs",
                    "checkpoint-aware graph execution",
                ],
            },
            "ambiguity_list": [],
            "subtask_candidates": [
                "source onboarding",
                "contract definition",
                "runtime validation",
                "governance audit",
            ],
            "must_not_do_list": [
                "bypass compliance guardrails",
                "capture unauthorized fields",
                "ship without audit trail",
            ],
            "artifact_refs": [artifact_ref("build", "requirement_spec.json")],
        }
