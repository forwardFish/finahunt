from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from skills.fetch import build_fetch_plan


class SourceRuntimeAgent(BaseAgent):
    agent_name = "Source Runtime Agent"
    stage = "source_runtime"

    def build_content(self, state: GraphState) -> dict:
        registry = get_result(state, "source_registry").get("source_registry", {})
        fetch_plan = build_fetch_plan(registry)
        return {
            "raw_documents": artifact_ref("runtime", "raw_documents.json"),
            "fetch_status_report": {
                "sources": fetch_plan["enabled_sources"],
                "success_count": len(fetch_plan["enabled_sources"]),
                "failure_count": 0,
            },
            "fetch_execution_log": artifact_ref("logs", "source_runtime.log"),
            "artifact_refs": [
                artifact_ref("runtime", "raw_documents.json"),
                artifact_ref("logs", "source_runtime.log"),
            ],
        }
