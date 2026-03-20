from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.llm import MultiModelRouter
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.event import (
    StockReasonLLMWriter,
    ThemeCandidateLLMEnhancer,
    XueqiuEvidenceResolver,
    map_theme_clusters_to_candidates,
)


class CandidateMapperAgent(BaseAgent):
    agent_name = "Candidate Mapper Agent"
    stage = "candidate_mapper"

    def build_content(self, state: GraphState) -> dict:
        theme_clusters = get_result(state, "theme_cluster").get("theme_clusters", [])
        llm_rules = load_yaml("config/rules/standards.yaml").get("llm_candidate_mapper", {})
        llm_enhancer = None
        llm_reason_writer = None
        if llm_rules.get("enabled", True):
            router = MultiModelRouter(
                llm_rules.get("registry_path", "config/llm/model_hub.json"),
                agent_id=llm_rules.get("agent_id", "theme_candidate_mapper"),
                timeout_seconds=float(llm_rules.get("timeout_seconds", 20.0)),
            )
            if router.available:
                llm_enhancer = ThemeCandidateLLMEnhancer(
                    router,
                    fallback_models=list(llm_rules.get("fallback_models", [])),
                    max_signals_per_theme=int(llm_rules.get("max_signals_per_theme", 4)),
                    max_candidates_per_theme=int(llm_rules.get("max_candidates_per_theme", 4)),
                    min_confidence=float(llm_rules.get("min_confidence", 0.55)),
                )

        llm_reason_rules = load_yaml("config/rules/standards.yaml").get("llm_stock_reason_writer", {})
        if llm_reason_rules.get("enabled", True):
            reason_router = MultiModelRouter(
                llm_reason_rules.get("registry_path", "config/llm/model_hub.json"),
                agent_id=llm_reason_rules.get("agent_id", "stock_reason_writer"),
                timeout_seconds=float(llm_reason_rules.get("timeout_seconds", 20.0)),
            )
            if reason_router.available:
                llm_reason_writer = StockReasonLLMWriter(
                    reason_router,
                    fallback_models=list(llm_reason_rules.get("fallback_models", [])),
                )

        mapped_theme_clusters = map_theme_clusters_to_candidates(
            theme_clusters,
            llm_enhancer=llm_enhancer,
            source_reason_resolver=XueqiuEvidenceResolver(),
            llm_reason_writer=llm_reason_writer,
        )
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
                "llm_mapping_cluster_count": sum(1 for item in mapped_theme_clusters if item.get("llm_mapping_used")),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "theme_candidate_mappings.json")],
        }
