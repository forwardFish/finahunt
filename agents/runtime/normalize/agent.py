from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.models import EvidenceSnippet, NormalizedNewsItem, RawNewsItem
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.normalize import normalize_document


class NormalizeAgent(BaseAgent):
    agent_name = "Normalize Agent"
    stage = "normalize"

    def build_content(self, state: GraphState) -> dict:
        allowed_documents = get_result(state, "compliance_guard").get("allowed_documents", [])
        quality_policy = load_yaml("config/rules/compliance_rules.yaml").get("information_quality_policy", {})

        normalized_documents: list[dict] = []
        failures: list[dict] = []
        dropped_documents: list[dict] = []
        seen_dedup_keys: set[str] = set()

        for item in allowed_documents:
            try:
                raw = RawNewsItem.model_validate(item)
                formatted = normalize_document(raw.model_dump(mode="json"), quality_policy)

                if not formatted["is_effective"]:
                    dropped_documents.append(
                        {
                            "document_id": raw.document_id,
                            "reason": formatted["filter_reasons"],
                            "title": raw.title,
                        }
                    )
                    continue

                if formatted["dedup_key"] in seen_dedup_keys:
                    dropped_documents.append(
                        {
                            "document_id": raw.document_id,
                            "reason": ["duplicate_content"],
                            "title": raw.title,
                        }
                    )
                    continue
                seen_dedup_keys.add(formatted["dedup_key"])

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
                    title=formatted["title"],
                    summary=formatted["summary"],
                    published_at=raw.published_at,
                    url=raw.url,
                    source_name=raw.source_name,
                    evidence_snippets=[evidence],
                    normalized_fields={
                        "channel": raw.source_type,
                        "tag_count": len(raw.tags),
                        "dedup_key": formatted["dedup_key"],
                        "quality_score": formatted["quality_score"],
                        "mentioned_symbols": formatted["mentioned_symbols"],
                        "theme_hints": formatted["theme_hints"],
                        "finance_keyword_hits": formatted["finance_keyword_hits"],
                    },
                    risk_flags=formatted["filter_reasons"],
                    metadata={**raw.metadata, "tags": raw.tags, "content_text": formatted["content_text"]},
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
            "dropped_documents": dropped_documents,
            "format_validation_report": {
                "contract_version": "v2",
                "valid": len(failures) == 0,
                "validated_count": len(normalized_documents),
                "dropped_count": len(dropped_documents),
            },
            "normalize_failure_record": failures,
            "artifact_refs": [artifact_ref("runtime", "normalized_documents.json")],
        }
