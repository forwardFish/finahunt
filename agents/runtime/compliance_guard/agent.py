from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.models import RawNewsItem
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.compliance_check import evaluate_content


class SourceComplianceGuardAgent(BaseAgent):
    agent_name = "Source Compliance Guard Agent"
    stage = "compliance_guard"

    def build_content(self, state: GraphState) -> dict:
        rules = load_yaml("config/rules/compliance_rules.yaml")
        registry = load_yaml("config/rules/source_registry.yaml")
        registry_map = {item["source_id"]: item for item in registry.get("sources", [])}
        raw_documents = get_result(state, "source_runtime").get("raw_documents", [])

        allowed_documents: list[dict] = []
        blocked_documents: list[dict] = []

        for item in raw_documents:
            validated = RawNewsItem.model_validate(item)
            source = registry_map.get(validated.source_id)
            if not source:
                blocked_documents.append(
                    {
                        "document_id": validated.document_id,
                        "source_id": validated.source_id,
                        "reason": "source_not_registered",
                        "risk_level": "high",
                    }
                )
                continue
            if not source.get("legality_evidence"):
                blocked_documents.append(
                    {
                        "document_id": validated.document_id,
                        "source_id": validated.source_id,
                        "reason": "missing_legality_evidence",
                        "risk_level": "high",
                    }
                )
                continue

            blocked_terms = rules["blocking_rules"]["blocked_terms"]
            text_check = evaluate_content(f"{validated.title}\n{validated.summary}\n{validated.content_text}", blocked_terms)
            if not text_check["passed"]:
                blocked_documents.append(
                    {
                        "document_id": validated.document_id,
                        "source_id": validated.source_id,
                        "reason": "blocked_terms_detected",
                        "violations": text_check["violations"],
                        "risk_level": "high",
                    }
                )
                continue

            allowed_documents.append(validated.model_dump(mode="json"))

        manual_review_required = bool(blocked_documents)
        return {
            "allowed_documents": allowed_documents,
            "blocked_documents": blocked_documents,
            "compliance_runtime_log": artifact_ref("audit", "compliance_runtime.log"),
            "compliance_summary": {
                "allowed_count": len(allowed_documents),
                "blocked_count": len(blocked_documents),
                "manual_review_required": manual_review_required,
            },
            "manual_review_required": manual_review_required,
            "artifact_refs": [artifact_ref("audit", "compliance_runtime.log")],
        }
