from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_context
from packages.schema.models import ManualCorrectionRecord
from packages.schema.state import GraphState


class HumanApprovalCheckpoint(BaseAgent):
    agent_name = "Human Approval Checkpoint"
    stage = "human_approval"

    def build_content(self, state: GraphState) -> dict:
        auto_approve = bool(get_context(state, "auto_approve", True))
        raw_corrections = get_context(state, "manual_corrections", [])
        manual_corrections = [ManualCorrectionRecord.model_validate(item).model_dump(mode="json") for item in raw_corrections]
        return {
            "approved": auto_approve,
            "approval_action": "Approve" if auto_approve else "Reject",
            "approval_note": "auto approved by current execution policy" if auto_approve else "manual rejection recorded",
            "approval_record": artifact_ref("audit", "approval_record.json"),
            "manual_correction_record": manual_corrections,
            "artifact_refs": [artifact_ref("audit", "approval_record.json")],
        }
