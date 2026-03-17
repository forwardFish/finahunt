from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event import map_theme_clusters_to_candidates


class CandidateMapperAgent(BaseAgent):
    agent_name = "Candidate Mapper Agent"
    stage = "candidate_mapper"

    def build_content(self, state: GraphState) -> dict:
        theme_clusters = get_result(state, "theme_cluster").get("theme_clusters", [])
        mapped_theme_clusters = map_theme_clusters_to_candidates(theme_clusters)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="theme_candidate_mappings.json",
            payload=mapped_theme_clusters,
            record_count=len(mapped_theme_clusters),
            summary={"artifact_type": "theme_candidate_mappings"},
        )
        return {
            "mapped_theme_clusters": mapped_theme_clusters,
            "mapping_summary": {
                "theme_cluster_count": len(theme_clusters),
                "mapped_cluster_count": len(mapped_theme_clusters),
                "core_candidate_count": sum(
                    len(item.get("core_candidates", [])) for item in mapped_theme_clusters
                ),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "theme_candidate_mappings.json")],
        }
