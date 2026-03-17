from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from packages.utils import load_yaml


class SourceAuditAgent(BaseAgent):
    agent_name = "Source Audit Agent"
    stage = "source_audit"

    def build_content(self, state: GraphState) -> dict:
        traceability = load_yaml("config/spec/traceability.yaml")
        gates = load_yaml("config/spec/gate_registry.yaml")
        source_runtime = get_result(state, "source_runtime")
        compliance_guard = get_result(state, "compliance_guard")
        source_scout = get_result(state, "source_scout")
        normalize = get_result(state, "normalize")
        event_extract = get_result(state, "event_extract")
        event_unify = get_result(state, "event_unify")
        theme_cluster = get_result(state, "theme_cluster")
        candidate_mapper = get_result(state, "candidate_mapper")
        purity_judge = get_result(state, "purity_judge")
        theme_candidate_aggregation = get_result(state, "theme_candidate_aggregation")
        fermentation_monitor = get_result(state, "fermentation_monitor")
        structured_result_cards = get_result(state, "structured_result_cards")
        result_warehouse = get_result(state, "result_warehouse")
        theme_heat_snapshot = get_result(state, "theme_heat_snapshot")
        low_position_discovery = get_result(state, "low_position_discovery")
        similar_case = get_result(state, "similar_case")
        fermenting_theme_feed = get_result(state, "fermenting_theme_feed")
        relevance_ranking = get_result(state, "relevance_ranking")
        daily_review = get_result(state, "daily_review")

        trace_report = {
            "trace_id": state["metadata"]["trace_id"],
            "registry_version": source_runtime.get("registry_snapshot", {}).get("registry_version", "unknown"),
            "stages": [
                "source_runtime",
                "compliance_guard",
                "source_scout",
                "normalize",
                "event_extract",
                "event_unify",
                "theme_detection",
                "catalyst_classification",
                "stock_linkage",
                "theme_cluster",
                "candidate_mapper",
                "purity_judge",
                "theme_candidate_aggregation",
                "fermentation_monitor",
                "structured_result_cards",
                "theme_heat_snapshot",
                "low_position_discovery",
                "similar_case",
                "fermenting_theme_feed",
                "relevance_ranking",
                "daily_review",
                "result_warehouse",
                "source_audit",
            ],
            "documents_seen": len(source_runtime.get("raw_documents", [])),
            "documents_allowed": len(compliance_guard.get("allowed_documents", [])),
            "documents_scouted": len(source_scout.get("scouted_documents", [])),
            "documents_normalized": len(normalize.get("normalized_documents", [])),
            "events_extracted": len(event_extract.get("candidate_events", [])),
            "events_canonical": len(event_unify.get("canonical_events", [])),
            "theme_clusters": len(theme_cluster.get("theme_clusters", [])),
            "candidate_mappings": sum(
                len(item.get("candidate_pool", [])) for item in candidate_mapper.get("mapped_theme_clusters", [])
            ),
            "purity_candidates": sum(
                len(item.get("candidate_pool", [])) for item in purity_judge.get("judged_theme_clusters", [])
            ),
            "theme_candidates": len(theme_candidate_aggregation.get("theme_candidates", [])),
            "fermentation_monitors": len(fermentation_monitor.get("monitored_themes", [])),
            "structured_cards": len(structured_result_cards.get("structured_result_cards", [])),
            "theme_heat_snapshots": len(theme_heat_snapshot.get("theme_heat_snapshots", [])),
            "low_position_count": len(low_position_discovery.get("low_position_opportunities", [])),
            "similar_case_count": len(similar_case.get("similar_theme_cases", [])),
            "fermenting_theme_count": len(fermenting_theme_feed.get("fermenting_theme_feed", [])),
            "events_ranked": len(relevance_ranking.get("ranked_events", [])),
            "focus_cards": len(daily_review.get("today_focus_page", [])),
            "artifact_batch_dir": result_warehouse.get("artifact_batch_dir", ""),
        }

        return {
            "runtime_audit_log": artifact_ref("audit", "runtime_audit.log"),
            "trace_report": trace_report,
            "runtime_exception_summary": [
                *normalize.get("normalize_failure_record", []),
                *event_extract.get("event_extraction_failures", []),
            ],
            "trace_matrix": [
                {
                    "goal": goal_id,
                    "config_refs": payload.get("config_refs", []),
                    "test_refs": payload.get("test_refs", []),
                }
                for goal_id, payload in traceability.get("goals", {}).items()
            ],
            "gate_registry_snapshot": [gate["gate_id"] for gate in gates.get("gates", [])],
            "artifact_refs": [artifact_ref("audit", "runtime_audit.log")],
        }
