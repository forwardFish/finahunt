from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.event import judge_theme_candidate_pools


class PurityJudgeAgent(BaseAgent):
    agent_name = "Purity Judge Agent"
    stage = "purity_judge"

    def build_content(self, state: GraphState) -> dict:
        mapped_theme_clusters = get_result(state, "candidate_mapper").get("mapped_theme_clusters", [])
        purity_rules = load_yaml("config/rules/standards.yaml").get("purity_judge_rules", {})
        judged_theme_clusters = judge_theme_candidate_pools(mapped_theme_clusters, purity_rules)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="theme_purity_candidates.json",
            payload=judged_theme_clusters,
            record_count=len(judged_theme_clusters),
            summary={"artifact_type": "theme_purity_candidates"},
        )
        return {
            "judged_theme_clusters": judged_theme_clusters,
            "judge_summary": {
                "mapped_cluster_count": len(mapped_theme_clusters),
                "accepted_candidate_count": sum(
                    len(item.get("accepted_candidates", [])) for item in judged_theme_clusters
                ),
                "watch_candidate_count": sum(
                    len(item.get("watch_candidates", [])) for item in judged_theme_clusters
                ),
                "filtered_candidate_count": sum(
                    len(item.get("filtered_candidates", [])) for item in judged_theme_clusters
                ),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "theme_purity_candidates.json")],
        }
