from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


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


class RefreshStrategy(BaseModel):
    cron: str
    timezone: str = "Asia/Shanghai"
    retry_policy: str = "exponential_backoff"
    max_retries: int = 3


class FieldContract(BaseModel):
    required_fields: list[str]
    optional_fields: list[str] = Field(default_factory=list)
    parser_key: str


class SourceAccessProfile(BaseModel):
    robots_respected: bool = True
    auth_mode: Literal["public", "api_key", "cookie"]
    rate_limit: str
    notes: str = ""


class SourceRegistryEntry(BaseModel):
    source_id: str
    source_name: str
    channel_type: Literal["exchange", "regulator", "authorized_feed", "public_site"]
    status: Literal["active", "paused", "deprecated"] = "active"
    in_mvp_chain: bool = True
    description: str
    base_url: HttpUrl
    refresh_strategy: RefreshStrategy
    field_contract: FieldContract
    legality_evidence: str
    access_profile: SourceAccessProfile
    risk_level: Literal["low", "medium", "high"] = "low"


class EvidenceSnippet(BaseModel):
    evidence_id: str
    quote: str
    source_url: HttpUrl
    source_title: str
    published_at: str


class RawNewsItem(BaseModel):
    document_id: str
    source_id: str
    title: str
    summary: str
    published_at: str
    url: HttpUrl
    source_name: str
    content_text: str
    evidence_snippet: str
    source_type: str
    tags: list[str] = Field(default_factory=list)


class NormalizedNewsItem(BaseModel):
    document_id: str
    source_id: str
    title: str
    summary: str
    published_at: str
    url: HttpUrl
    source_name: str
    evidence_snippets: list[EvidenceSnippet]
    normalized_fields: dict[str, Any] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)


class EventObject(BaseModel):
    event_id: str
    title: str
    event_type: str
    source_refs: list[str]
    evidence_refs: list[str]
    status: Literal["NEW", "VERIFIED", "RISING", "REIGNITED", "REALIZED"]
    compliance_notes: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "low"


class ManualCorrectionRecord(BaseModel):
    correction_id: str
    target_stage: str
    target_field: str
    original_value: Any
    corrected_value: Any
    operator: str
    reason: str
    approved: bool = False


class FinalGateArtifact(BaseModel):
    gate_id: str
    decision: Literal["PASS", "PASS_WITH_NOTES", "BLOCKED"]
    requires_human_review: bool
    risk_notes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    manual_correction_refs: list[str] = Field(default_factory=list)


class RuntimeGraphInput(BaseModel):
    schedule_name: str
    source_registry_version: str
    requested_sources: list[str] = Field(default_factory=list)
    auto_approve: bool = True


class RuntimeGraphOutput(BaseModel):
    raw_documents: list[RawNewsItem] = Field(default_factory=list)
    allowed_documents: list[RawNewsItem] = Field(default_factory=list)
    normalized_documents: list[NormalizedNewsItem] = Field(default_factory=list)
    blocked_documents: list[dict[str, Any]] = Field(default_factory=list)
    trace_report: dict[str, Any] = Field(default_factory=dict)
    runtime_exception_summary: list[dict[str, Any]] = Field(default_factory=list)
    final_gate_artifact: FinalGateArtifact | None = None


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
