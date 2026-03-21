from __future__ import annotations

from packages.utils import load_yaml
from graphs.runtime_graph import build_runtime_graph
from packages.state_manager import StateManager


def run_runtime_cycle(
    schedule_name: str = "hourly",
    rule_version: str = "v1",
    *,
    requested_sources: list[str] | None = None,
    seed_documents: list[dict] | None = None,
    live_fetch: bool = False,
    user_profile: dict | None = None,
    max_items_per_source: int = 10,
) -> dict:
    registry = load_yaml("config/rules/source_registry.yaml")
    state = StateManager.new_state(
        graph_type="runtime",
        input_ref=f"schedule://{schedule_name}",
        rule_version=rule_version,
        context={
            "schedule_name": schedule_name,
            "requested_sources": requested_sources or [],
            "source_registry_version": registry.get("registry_version", "unknown"),
            "manual_corrections": [],
            "seed_documents": seed_documents or [],
            "live_fetch": live_fetch,
            "user_profile": user_profile or {},
            "max_items_per_source": max_items_per_source,
        },
    )
    graph = build_runtime_graph()
    return graph.invoke(state)


def run_live_event_cognition_cycle(
    requested_sources: list[str] | None = None,
    *,
    user_profile: dict | None = None,
    max_items_per_source: int = 8,
) -> dict:
    return run_runtime_cycle(
        schedule_name="live-event-cognition",
        rule_version="v2",
        requested_sources=requested_sources or ["cls-telegraph", "jiuyangongshe-live", "xueqiu-hot-spot"],
        live_fetch=True,
        user_profile=user_profile or {},
        max_items_per_source=max_items_per_source,
    )


def run_low_position_workbench_cycle(
    requested_sources: list[str] | None = None,
    *,
    user_profile: dict | None = None,
    max_items_per_source: int = 8,
) -> dict:
    return run_runtime_cycle(
        schedule_name="low-position-workbench",
        rule_version="v3",
        requested_sources=requested_sources or ["cls-telegraph", "jiuyangongshe-live", "xueqiu-hot-spot"],
        live_fetch=True,
        user_profile=user_profile
        or {
            "watchlist_symbols": [],
            "watchlist_themes": ["人工智能", "机器人", "算力", "低空经济", "新能源", "医药"],
        },
        max_items_per_source=max_items_per_source,
    )
