from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_context
from packages.schema.state import GraphState


class HumanApprovalCheckpoint(BaseAgent):
    agent_name = "Human Approval Checkpoint"
    stage = "human_approval"

    def build_content(self, state: GraphState) -> dict:
        auto_approve = bool(get_context(state, "auto_approve", True))
        return {
            "approved": auto_approve,
            "approval_action": "Approve" if auto_approve else "Reject",
            "approval_note": "auto approved by current execution policy",
            "approval_record": artifact_ref("audit", "approval_record.json"),
            "artifact_refs": [artifact_ref("audit", "approval_record.json")],
        }
