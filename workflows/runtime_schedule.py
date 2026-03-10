from __future__ import annotations

from graphs.runtime_graph import build_runtime_graph
from packages.state_manager import StateManager


def run_runtime_cycle(schedule_name: str = "hourly", rule_version: str = "v1") -> dict:
    state = StateManager.new_state(
        graph_type="runtime",
        input_ref=f"schedule://{schedule_name}",
        rule_version=rule_version,
        context={"schedule_name": schedule_name},
    )
    graph = build_runtime_graph()
    return graph.invoke(state)
