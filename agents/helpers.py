from __future__ import annotations

from typing import Any

from packages.schema.state import GraphState


def get_result(state: GraphState, stage: str) -> dict[str, Any]:
    return state.get("results", {}).get(stage, {}).get("content", {})


def get_context(state: GraphState, key: str, default: Any = None) -> Any:
    return state.get("context", {}).get(key, default)


def artifact_ref(*parts: str) -> str:
    return "artifact://" + "/".join(parts)
