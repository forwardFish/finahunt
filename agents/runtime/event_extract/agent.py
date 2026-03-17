from __future__ import annotations

import hashlib

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.models import EventObject, NormalizedNewsItem
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.event import extract_event_profile, extract_symbol_candidates


class EventExtractAgent(BaseAgent):
    agent_name = "Event Extract Agent"
    stage = "event_extract"

    def build_content(self, state: GraphState) -> dict:
        normalized_documents = get_result(state, "normalize").get("normalized_documents", [])
        theme_rules = load_yaml("config/rules/standards.yaml").get("theme_rules", {})
        extracted_events: list[dict] = []
        failures: list[dict] = []

        for item in normalized_documents:
            try:
                document = NormalizedNewsItem.model_validate(item)
                content_text = str(document.metadata.get("content_text", ""))
                merged_text = f"{document.title} {document.summary} {content_text}"
                event_profile = extract_event_profile(
                    document.title,
                    document.summary,
                    content_text,
                    document.metadata,
                    document.published_at,
                    theme_rules,
                )
                linked_assets = extract_symbol_candidates(merged_text, document.metadata)
                event_id = f"evt-{hashlib.sha256(document.document_id.encode('utf-8')).hexdigest()[:12]}"

                event = EventObject(
                    event_id=event_id,
                    title=document.title,
                    summary=document.summary,
                    event_type=event_profile["event_type"],
                    source_refs=[str(document.url)],
                    evidence_refs=[snippet.evidence_id for snippet in document.evidence_snippets],
                    status="NEW",
                    risk_level="low",
                    event_time=document.published_at,
                    event_subject=event_profile["event_subject"],
                    occurred_at=event_profile["occurred_at"],
                    first_disclosed_at=event_profile["first_disclosed_at"],
                    related_themes=event_profile["related_themes"],
                    related_industries=event_profile["related_industries"],
                    involved_products=event_profile["involved_products"],
                    involved_technologies=event_profile["involved_technologies"],
                    involved_policies=event_profile["involved_policies"],
                    impact_direction=event_profile["impact_direction"],
                    impact_scope=event_profile["impact_scope"],
                    theme_tags=event_profile["related_themes"],
                    linked_assets=linked_assets,
                    metadata={
                        "document_id": document.document_id,
                        "source_id": document.source_id,
                        "quality_score": document.normalized_fields.get("quality_score", 0.0),
                        "content_text": content_text,
                        "event_profile": event_profile,
                    },
                )
                extracted_events.append(event.model_dump(mode="json"))
            except Exception as exc:
                failures.append({"document_id": item.get("document_id", "unknown"), "reason": str(exc)})

        return {
            "candidate_events": extracted_events,
            "event_extraction_failures": failures,
            "artifact_refs": [artifact_ref("runtime", "candidate_events.json")],
        }
