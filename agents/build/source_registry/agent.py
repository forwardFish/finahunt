from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState
from packages.utils import load_yaml


class SourceRegistryAgent(BaseAgent):
    agent_name = "Source Registry Agent"
    stage = "source_registry"

    def build_content(self, state: GraphState) -> dict:
        registry = load_yaml("config/rules/source_registry.yaml")
        sources = registry.get("sources", [])
        return {
            "source_registry": registry,
            "source_legality_evidence": {
                item["source_id"]: item.get("legality_evidence", "")
                for item in sources
            },
            "source_access_profile": {
                item["source_id"]: item.get("access_profile", {})
                for item in sources
            },
            "source_risk_level": {
                item["source_id"]: item.get("risk_level", "unknown")
                for item in sources
            },
            "artifact_refs": [artifact_ref("registry", "source_registry.yaml")],
        }
