from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import build_message_company_candidates, build_symbol_catalog


class CompanyMiningAgent(BaseAgent):
    agent_name = "Company Mining Agent"
    stage = "company_mining"

    def build_content(self, state: GraphState) -> dict:
        valuable_messages = get_result(state, "message_processing").get("valuable_messages", [])
        message_impact_analysis = get_result(state, "impact_analysis").get("message_impact_analysis", [])
        mapped_theme_clusters = get_result(state, "candidate_mapper").get("mapped_theme_clusters", [])
        judged_theme_clusters = get_result(state, "purity_judge").get("judged_theme_clusters", [])
        low_position_opportunities = get_result(state, "low_position_discovery").get("low_position_opportunities", [])
        canonical_events = get_result(state, "event_unify").get("canonical_events", [])
        normalized_documents = get_result(state, "normalize").get("normalized_documents", [])
        symbol_catalog = build_symbol_catalog(canonical_events, normalized_documents)
        message_company_candidates = build_message_company_candidates(
            valuable_messages,
            message_impact_analysis,
            mapped_theme_clusters,
            judged_theme_clusters,
            low_position_opportunities,
            symbol_catalog,
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_company_candidates.json",
            payload=message_company_candidates,
            record_count=len(message_company_candidates),
            summary={"artifact_type": "message_company_candidates"},
        )
        return {
            "message_company_candidates": message_company_candidates,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "message_company_candidates.json")],
        }
