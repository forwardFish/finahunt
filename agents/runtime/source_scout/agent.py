from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.models import RawNewsItem
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.event import scout_early_catalyst_inputs


class SourceScoutAgent(BaseAgent):
    agent_name = "Source Scout Agent"
    stage = "source_scout"

    def build_content(self, state: GraphState) -> dict:
        registry = load_yaml("config/rules/source_registry.yaml")
        registry_map = {item["source_id"]: item for item in registry.get("sources", [])}
        allowed_documents = get_result(state, "compliance_guard").get("allowed_documents", [])
        validated_documents = [RawNewsItem.model_validate(item).model_dump(mode="json") for item in allowed_documents]
        scout_result = scout_early_catalyst_inputs(validated_documents, registry_map)

        payload = {
            "scouted_documents": scout_result["candidates"],
            "dropped_documents": scout_result["dropped"],
            "source_priority_summary": {
                "P0": sum(1 for item in scout_result["candidates"] if item.get("metadata", {}).get("source_priority") == "P0"),
                "P1": sum(1 for item in scout_result["candidates"] if item.get("metadata", {}).get("source_priority") == "P1"),
                "P2": sum(1 for item in scout_result["candidates"] if item.get("metadata", {}).get("source_priority") == "P2"),
            },
        }
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="source_scout_candidates.json",
            payload=payload["scouted_documents"],
            record_count=len(payload["scouted_documents"]),
            summary={"artifact_type": "source_scout_candidates"},
        )
        return {
            **payload,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "source_scout_candidates.json")],
        }
