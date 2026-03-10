from __future__ import annotations

from graphs.build_graph import build_build_graph
from graphs.governance_graph import build_governance_graph
from packages.state_manager import StateManager


def run_build_workflow(user_demand: str, rule_version: str = "v1") -> dict:
    build_state = StateManager.new_state(
        graph_type="build",
        input_ref=f"demand://{user_demand}",
        rule_version=rule_version,
        context={
            "user_demand": user_demand,
            "auto_approve": True,
        },
    )
    build_graph = build_build_graph()
    build_result = build_graph.invoke(build_state)

    governance_state = StateManager.new_state(
        graph_type="governance",
        input_ref=build_result.get("output_ref", build_result["input_ref"]),
        rule_version=rule_version,
        task_id=build_result["task_id"],
        context=build_result.get("context", {}),
    )
    governance_state["results"] = dict(build_result.get("results", {}))
    governance_state["artifact_refs"] = list(build_result.get("artifact_refs", []))
    governance_state["metadata"] = dict(build_result.get("metadata", {}))

    governance_graph = build_governance_graph()
    governance_result = governance_graph.invoke(governance_state)

    return {
        **build_result,
        **governance_result,
        "results": {
            **build_result.get("results", {}),
            **governance_result.get("results", {}),
        },
        "artifact_refs": [
            *build_result.get("artifact_refs", []),
            *governance_result.get("artifact_refs", []),
        ],
    }
