from __future__ import annotations

from typing import Any, Literal, TypedDict


class GraphMetadata(TypedDict, total=False):
    trace_id: str
    created_at: str
    updated_at: str
    last_agent: str
    last_stage: str


class GraphState(TypedDict, total=False):
    task_id: str
    run_id: str
    graph_type: Literal["build", "runtime", "governance"]
    stage: str
    status: str
    input_ref: str
    output_ref: str
    error: dict[str, Any] | None
    retry_count: int
    rule_version: str
    artifact_refs: list[str]
    approval_required: bool
    metadata: GraphMetadata
    context: dict[str, Any]
    results: dict[str, Any]
