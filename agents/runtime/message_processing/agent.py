from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import build_valuable_messages


class MessageProcessingAgent(BaseAgent):
    agent_name = "Message Processing Agent"
    stage = "message_processing"

    def build_content(self, state: GraphState) -> dict:
        canonical_events = get_result(state, "event_unify").get("canonical_events", [])
        normalized_documents = get_result(state, "normalize").get("normalized_documents", [])
        valuable_messages = build_valuable_messages(canonical_events, normalized_documents)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="valuable_messages.json",
            payload=valuable_messages,
            record_count=len(valuable_messages),
            summary={"artifact_type": "valuable_messages"},
        )
        return {
            "valuable_messages": valuable_messages,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "valuable_messages.json")],
        }
