from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAIL = "fail"
    BLOCKED = "blocked"
    NEEDS_APPROVAL = "needs_approval"


class AgentError(BaseModel):
    error_type: str
    error_msg: str
    error_source: str
    impact_scope: str


class AgentOutput(BaseModel):
    task_id: str
    run_id: str
    stage: str
    agent_name: str
    agent_version: str
    rule_version: str
    status: AgentStatus
    content: dict[str, Any]
    error: AgentError | None = None
    artifact_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GlobalStateModel(BaseModel):
    task_id: str
    run_id: str
    graph_type: Literal["build", "runtime", "governance"]
    stage: str
    status: AgentStatus
    input_ref: str
    output_ref: str = ""
    error: AgentError | None = None
    retry_count: int = 0
    rule_version: str
    artifact_refs: list[str] = Field(default_factory=list)
    approval_required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    results: dict[str, Any] = Field(default_factory=dict)
