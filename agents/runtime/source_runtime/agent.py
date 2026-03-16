from __future__ import annotations

from datetime import UTC, datetime

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_context
from packages.schema.models import RawNewsItem, SourceRegistryEntry
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.fetch import build_fetch_plan


def _default_seed_documents(enabled_sources: list[dict]) -> list[dict]:
    published_at = datetime.now(UTC).isoformat()
    samples: list[dict] = []
    for index, source in enumerate(enabled_sources, start=1):
        samples.append(
            {
                "document_id": f"raw-{index:03d}",
                "source_id": source["source_id"],
                "title": f"{source['source_name']} 样本资讯 {index}",
                "summary": f"来自 {source['source_name']} 的合规样本，用于验证 Sprint 0 runtime 基线。",
                "published_at": published_at,
                "url": f"{source['base_url']}sample-{index}",
                "source_name": source["source_name"],
                "content_text": "官方披露信息，包含可追踪来源和基础摘要。",
                "evidence_snippet": "官方披露信息，包含可追踪来源和基础摘要。",
                "source_type": source["channel_type"],
                "tags": ["foundation", "sample"],
            }
        )
    return samples


class SourceRuntimeAgent(BaseAgent):
    agent_name = "Source Runtime Agent"
    stage = "source_runtime"

    def build_content(self, state: GraphState) -> dict:
        registry = load_yaml("config/rules/source_registry.yaml")
        active_sources = [item for item in registry.get("sources", []) if item.get("status") == "active"]
        requested_sources = set(get_context(state, "requested_sources", []))
        if requested_sources:
            active_sources = [item for item in active_sources if item["source_id"] in requested_sources]

        # Validate registry entries to ensure Sprint 0 contracts are executable.
        validated_sources = [SourceRegistryEntry.model_validate(item).model_dump(mode="json") for item in active_sources]
        fetch_plan = build_fetch_plan({"sources": validated_sources, "default_schedule": registry.get("default_schedule")})
        raw_documents = get_context(state, "seed_documents") or _default_seed_documents(validated_sources)
        validated_documents = [RawNewsItem.model_validate(item).model_dump(mode="json") for item in raw_documents]

        return {
            "registry_snapshot": {
                "registry_version": registry.get("registry_version", "unknown"),
                "enabled_sources": [item["source_id"] for item in validated_sources],
            },
            "raw_documents": validated_documents,
            "fetch_status_report": {
                "sources": fetch_plan["enabled_sources"],
                "success_count": len(validated_documents),
                "failure_count": 0,
                "schedule": fetch_plan["schedule"],
            },
            "fetch_execution_log": artifact_ref("runtime", "source_runtime.log"),
            "artifact_refs": [
                artifact_ref("runtime", "raw_documents.json"),
                artifact_ref("runtime", "source_runtime.log"),
            ],
        }
