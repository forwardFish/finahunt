from __future__ import annotations


def build_fetch_plan(source_registry: dict) -> dict:
    return {
        "enabled_sources": [
            source["source_id"]
            for source in source_registry.get("sources", [])
            if source.get("status") == "active"
        ],
        "schedule": source_registry.get("default_schedule", "0 */1 * * *"),
    }
