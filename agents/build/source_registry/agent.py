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
        return {
            "source_registry": registry,
            "source_legality_evidence": registry["legality_evidence"],
            "source_access_profile": registry["access_profiles"],
            "source_risk_level": registry["risk_matrix"],
            "artifact_refs": [artifact_ref("registry", "source_registry.yaml")],
        }
