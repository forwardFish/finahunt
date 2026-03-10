from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import get_result
from packages.schema.state import GraphState


class FinalGateAgent(BaseAgent):
    agent_name = "Final Gate Agent"
    stage = "final_gate"

    def build_content(self, state: GraphState) -> dict:
        evaluation = get_result(state, "evaluation")
        audit = get_result(state, "governance_audit")
        passed = evaluation.get("evaluation_report", {}).get("result") == "pass"
        decision = "PASS" if passed and not audit.get("risk_findings") else "PASS_WITH_NOTES"
        if not passed:
            decision = "BLOCKED"
        return {
            "final_gate_decision": decision,
            "rule_check_matrix": [
                {
                    "rule_id": "compliance-first",
                    "rule_content": "all outputs must remain compliant and traceable",
                    "check_result": "pass" if passed else "fail",
                    "evidence": "state://results/evaluation",
                    "risk_level": "low" if passed else "high",
                }
            ],
            "risk_notes": audit.get("risk_findings", []),
            "action_recommendation": "proceed" if passed else "fix failing stages and rerun",
            "full_report_refs": state.get("artifact_refs", []),
            "artifact_refs": [],
        }
