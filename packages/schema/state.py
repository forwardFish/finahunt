from __future__ import annotations

from typing import Any, Literal, TypedDict


class GraphMetadata(TypedDict, total=False):
    trace_id: str
    created_at: str
    updated_at: str
    last_agent: str
    last_stage: str
    source_registry_version: str
    final_gate_decision: str


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
    source_registry_snapshot: dict[str, Any]
    raw_documents: list[dict[str, Any]]
    allowed_documents: list[dict[str, Any]]
    blocked_documents: list[dict[str, Any]]
    normalized_documents: list[dict[str, Any]]
    runtime_trace_matrix: list[dict[str, Any]]
    manual_corrections: list[dict[str, Any]]
    final_gate_artifacts: list[dict[str, Any]]
