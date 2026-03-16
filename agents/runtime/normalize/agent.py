from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.models import EvidenceSnippet, NormalizedNewsItem, RawNewsItem
from packages.schema.state import GraphState


class NormalizeAgent(BaseAgent):
    agent_name = "Normalize Agent"
    stage = "normalize"

    def build_content(self, state: GraphState) -> dict:
        allowed_documents = get_result(state, "compliance_guard").get("allowed_documents", [])
        normalized_documents: list[dict] = []
        failures: list[dict] = []

        for item in allowed_documents:
            try:
                raw = RawNewsItem.model_validate(item)
                evidence = EvidenceSnippet(
                    evidence_id=f"evi-{raw.document_id}",
                    quote=raw.evidence_snippet,
                    source_url=raw.url,
                    source_title=raw.title,
                    published_at=raw.published_at,
                )
                normalized = NormalizedNewsItem(
                    document_id=raw.document_id,
                    source_id=raw.source_id,
                    title=raw.title,
                    summary=raw.summary,
                    published_at=raw.published_at,
                    url=raw.url,
                    source_name=raw.source_name,
                    evidence_snippets=[evidence],
                    normalized_fields={
                        "channel": raw.source_type,
                        "tag_count": len(raw.tags),
                    },
                )
                normalized_documents.append(normalized.model_dump(mode="json"))
            except Exception as exc:  # pragma: no cover - defensive
                failures.append(
                    {
                        "document_id": item.get("document_id", "unknown"),
                        "reason": str(exc),
                    }
                )

        return {
            "normalized_documents": normalized_documents,
            "format_validation_report": {
                "contract_version": "v1",
                "valid": len(failures) == 0,
                "validated_count": len(normalized_documents),
            },
            "normalize_failure_record": failures,
            "artifact_refs": [artifact_ref("runtime", "normalized_documents.json")],
        }
