from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from skills.event import unify_events


class EventUnifyAgent(BaseAgent):
    agent_name = "Event Unify Agent"
    stage = "event_unify"

    def build_content(self, state: GraphState) -> dict:
        candidate_events = get_result(state, "event_extract").get("candidate_events", [])
        canonical_events = unify_events(candidate_events)
        return {
            "canonical_events": canonical_events,
            "unification_summary": {
                "candidate_count": len(candidate_events),
                "canonical_count": len(canonical_events),
            },
            "artifact_refs": [artifact_ref("runtime", "canonical_events.json")],
        }
