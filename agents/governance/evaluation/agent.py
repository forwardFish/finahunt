from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import get_result
from packages.schema.state import GraphState


class EvaluationAgent(BaseAgent):
    agent_name = "Evaluation Agent"
    stage = "evaluation"

    def build_content(self, state: GraphState) -> dict:
        test = get_result(state, "test")
        audit = get_result(state, "governance_audit")
        score = 100
        if not test.get("test_pass", True):
            score -= 40
        score -= min(len(audit.get("risk_findings", [])) * 10, 40)
        return {
            "evaluation_report": {
                "overall_score": score,
                "result": "pass" if score >= 70 else "fail",
            },
            "score_card": {
                "build_readiness": 100 if test.get("test_pass", True) else 60,
                "governance_risk_penalty": len(audit.get("risk_findings", [])) * 10,
            },
            "improvement_suggestions": [
                "wire production checkpoint backend",
                "add live source connectors per approved registry",
            ],
            "rule_optimization_suggestions": [
                "expand blocked terms with policy change management",
            ],
            "artifact_refs": [],
        }
