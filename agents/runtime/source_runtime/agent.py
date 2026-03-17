from __future__ import annotations

from datetime import UTC, datetime

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_context
from packages.schema.models import RawNewsItem, SourceRegistryEntry
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.fetch import build_fetch_plan, fetch_documents


def _default_seed_documents(enabled_sources: list[dict]) -> list[dict]:
    published_at = datetime.now(UTC).isoformat()
    samples: list[dict] = []
    template_by_source = {
        "cls-telegraph": {
            "title": "财联社快讯披露机器人产业政策支持",
            "content_text": "工信部发布机器人产业支持政策，板块关注度提升，相关公司300024.SZ受到关注。",
            "stock_code": "300024.SZ",
            "plate_name": "机器人",
        },
        "jiuyangongshe-live": {
            "title": "韭研公社追踪算力服务器订单进展",
            "content_text": "多家公司披露算力服务器订单进展，AIDC 与算力主题热度上升，相关标的000063.SZ被提及。",
            "stock_code": "000063.SZ",
            "plate_name": "算力",
        },
        "xueqiu-hot-spot": {
            "title": "雪球热点讨论低空物流试点催化",
            "content_text": "低空物流试点推进，无人机配送与 eVTOL 商业化叙事升温，相关标的300696.SZ进入讨论名单。",
            "stock_code": "300696.SZ",
            "plate_name": "低空经济",
        },
    }
    for index, source in enumerate(enabled_sources, start=1):
        template = template_by_source.get(
            source["source_id"],
            {
                "title": f"{source['source_name']} 披露早期题材线索",
                "content_text": "产业催化开始形成，主题方向仍处于早期认知阶段。",
                "stock_code": "000001.SZ",
                "plate_name": "主题观察",
            },
        )
        samples.append(
            {
                "document_id": f"raw-{index:03d}",
                "source_id": source["source_id"],
                "title": template["title"],
                "summary": template["content_text"][:80],
                "published_at": published_at,
                "url": f"{source['base_url']}#sample-{index}",
                "source_name": source["source_name"],
                "content_text": template["content_text"],
                "evidence_snippet": template["content_text"][:120],
                "source_type": source["channel_type"],
                "tags": ["foundation", "sample", "finance"],
                "metadata": {
                    "parser_key": source["field_contract"]["parser_key"],
                    "stock_list": [{"secu_code": template["stock_code"], "secu_name": "示例标的"}],
                    "plate_list": [{"plate_name": template["plate_name"]}],
                },
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

        validated_sources = [SourceRegistryEntry.model_validate(item).model_dump(mode="json") for item in active_sources]
        fetch_plan = build_fetch_plan({"sources": validated_sources, "default_schedule": registry.get("default_schedule")})

        if get_context(state, "seed_documents"):
            raw_documents = get_context(state, "seed_documents")
            execution_log = [{"source_id": "seed_documents", "status": "success", "count": len(raw_documents)}]
            storage_summary = {}
        elif get_context(state, "live_fetch", False):
            fetched = fetch_documents(
                validated_sources,
                max_items_per_source=get_context(state, "max_items_per_source", 10),
                timeout=get_context(state, "request_timeout", 20),
                run_id=state["run_id"],
            )
            raw_documents = fetched["raw_documents"]
            execution_log = fetched["execution_log"]
            storage_summary = fetched.get("storage_summary", {})
        else:
            raw_documents = _default_seed_documents(validated_sources)
            execution_log = [{"source_id": "default_seed", "status": "success", "count": len(raw_documents)}]
            storage_summary = {}

        validated_documents = [RawNewsItem.model_validate(item).model_dump(mode="json") for item in raw_documents]
        success_count = sum(1 for item in execution_log if item.get("status") == "success")
        failure_count = sum(1 for item in execution_log if item.get("status") == "failed")

        return {
            "registry_snapshot": {
                "registry_version": registry.get("registry_version", "unknown"),
                "enabled_sources": [item["source_id"] for item in validated_sources],
            },
            "raw_documents": validated_documents,
            "fetch_status_report": {
                "sources": fetch_plan["enabled_sources"],
                "success_count": success_count,
                "failure_count": failure_count,
                "document_count": len(validated_documents),
                "schedule": fetch_plan["schedule"],
                "live_fetch": bool(get_context(state, "live_fetch", False)),
            },
            "fetch_execution_log": execution_log,
            "raw_content_storage": storage_summary,
            "artifact_refs": [
                artifact_ref("runtime", "raw_documents.json"),
                artifact_ref("runtime", "source_runtime.log"),
            ],
        }
