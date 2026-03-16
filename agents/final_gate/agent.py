from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import get_context, get_result
from packages.schema.models import FinalGateArtifact, ManualCorrectionRecord
from packages.schema.state import GraphState


class FinalGateAgent(BaseAgent):
    agent_name = "Final Gate Agent"
    stage = "final_gate"

    def build_content(self, state: GraphState) -> dict:
        evaluation = get_result(state, "evaluation")
        audit = get_result(state, "governance_audit")
        runtime_audit = get_result(state, "source_audit")
        human_approval = get_result(state, "human_approval")

        evaluation_passed = evaluation.get("evaluation_report", {}).get("result", "pass") == "pass"
        risk_findings = audit.get("risk_findings", [])
        runtime_exceptions = runtime_audit.get("runtime_exception_summary", [])
        manual_corrections = [
            ManualCorrectionRecord.model_validate(item).model_dump(mode="json")
            for item in human_approval.get("manual_correction_record", []) or get_context(state, "manual_corrections", [])
        ]
        requires_human_review = bool(
            any(item.get("risk_level") == "high" for item in risk_findings)
            or get_result(state, "compliance_guard").get("manual_review_required")
        )
        human_review_satisfied = (not requires_human_review) or bool(manual_corrections)

        decision = "PASS"
        if not evaluation_passed or runtime_exceptions:
            decision = "BLOCKED"
        elif requires_human_review and not human_review_satisfied:
            decision = "BLOCKED"
        elif risk_findings:
            decision = "PASS_WITH_NOTES"

        artifact = FinalGateArtifact(
            gate_id="manual_review_to_final_acceptance",
            decision=decision,
            requires_human_review=requires_human_review,
            risk_notes=[item.get("stage", "unknown") for item in risk_findings],
            evidence_refs=state.get("artifact_refs", []),
            manual_correction_refs=[item["correction_id"] for item in manual_corrections],
        )
        return {
            "final_gate_decision": decision,
            "rule_check_matrix": [
                {
                    "rule_id": "compliance-first",
                    "rule_content": "all outputs must remain compliant and traceable",
                    "check_result": "pass" if decision != "BLOCKED" else "fail",
                    "evidence": "state://results/source_audit",
                    "risk_level": "high" if decision == "BLOCKED" else "medium" if risk_findings else "low",
                }
            ],
            "risk_notes": risk_findings,
            "action_recommendation": "proceed" if decision == "PASS" else "manual review and rerun" if decision == "PASS_WITH_NOTES" else "fix failing stages and rerun",
            "manual_correction_record": manual_corrections,
            "full_report_refs": state.get("artifact_refs", []),
            "final_gate_artifact": artifact.model_dump(mode="json"),
            "artifact_refs": [],
        }
