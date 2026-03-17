from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json, runtime_run_dir
from packages.schema.state import GraphState


class ResultWarehouseAgent(BaseAgent):
    agent_name = "Result Warehouse Agent"
    stage = "result_warehouse"

    def build_content(self, state: GraphState) -> dict:
        artifacts = {
            "raw_documents.json": get_result(state, "source_runtime").get("raw_documents", []),
            "source_scout_candidates.json": get_result(state, "source_scout").get("scouted_documents", []),
            "normalized_documents.json": get_result(state, "normalize").get("normalized_documents", []),
            "canonical_events.json": get_result(state, "event_unify").get("canonical_events", []),
            "theme_clusters.json": get_result(state, "theme_cluster").get("theme_clusters", []),
            "theme_candidate_mappings.json": get_result(state, "candidate_mapper").get("mapped_theme_clusters", []),
            "theme_purity_candidates.json": get_result(state, "purity_judge").get("judged_theme_clusters", []),
            "theme_candidates.json": get_result(state, "theme_candidate_aggregation").get("theme_candidates", []),
            "structured_result_cards.json": get_result(state, "structured_result_cards").get("structured_result_cards", []),
            "theme_heat_snapshots.json": get_result(state, "theme_heat_snapshot").get("theme_heat_snapshots", []),
            "low_position_opportunities.json": get_result(state, "low_position_discovery").get("low_position_opportunities", []),
            "fermenting_theme_feed.json": get_result(state, "fermenting_theme_feed").get("fermenting_theme_feed", []),
            "relevance_ranking.json": get_result(state, "relevance_ranking").get("ranked_events", []),
            "daily_review.json": get_result(state, "daily_review"),
        }

        saved_artifacts: list[dict] = []
        for filename, payload in artifacts.items():
            persist_runtime_json(
                state,
                stage=self.stage,
                filename=filename,
                payload=payload,
                record_count=len(payload) if isinstance(payload, list) else None,
                summary={"artifact_type": filename.removesuffix(".json")},
            )
            saved_artifacts.append(
                {
                    "filename": filename,
                    "artifact_ref": artifact_ref("runtime", state["run_id"], filename),
                    "record_count": len(payload) if isinstance(payload, list) else None,
                }
            )

        summary_payload = {
            "run_id": state["run_id"],
            "trace_id": state["metadata"]["trace_id"],
            "artifact_batch_dir": runtime_run_dir(state["run_id"]).as_posix(),
            "saved_artifacts": saved_artifacts,
        }
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="result_warehouse_summary.json",
            payload=summary_payload,
            summary={"artifact_type": "result_warehouse_summary"},
        )

        return {
            **summary_payload,
            "manifest_ref": artifact_ref("runtime", state["run_id"], "manifest.json"),
            "artifact_refs": [
                *(item["artifact_ref"] for item in saved_artifacts),
                artifact_ref("runtime", state["run_id"], "result_warehouse_summary.json"),
                artifact_ref("runtime", state["run_id"], "manifest.json"),
            ],
        }
