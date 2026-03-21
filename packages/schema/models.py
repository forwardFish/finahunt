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
    discovery_priority: Literal["P0", "P1", "P2"] = "P1"
    discovery_role: str = "general_signal"


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
    metadata: dict[str, Any] = Field(default_factory=dict)


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
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventObject(BaseModel):
    event_id: str
    title: str
    event_type: str
    source_refs: list[str]
    evidence_refs: list[str]
    status: Literal["NEW", "VERIFIED", "RISING", "REIGNITED", "REALIZED"]
    compliance_notes: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "low"
    summary: str = ""
    event_time: str = ""
    event_subject: str = ""
    occurred_at: str = ""
    first_disclosed_at: str = ""
    canonical_key: str = ""
    related_themes: list[str] = Field(default_factory=list)
    related_industries: list[str] = Field(default_factory=list)
    involved_products: list[str] = Field(default_factory=list)
    involved_technologies: list[str] = Field(default_factory=list)
    involved_policies: list[str] = Field(default_factory=list)
    impact_direction: Literal["positive", "negative", "mixed", "neutral"] = "neutral"
    impact_scope: Literal["stock", "sector", "market", "macro", "unknown"] = "unknown"
    theme_tags: list[str] = Field(default_factory=list)
    catalyst_type: str = ""
    catalyst_strength: Literal["high", "medium", "low", "unknown"] = "unknown"
    catalyst_boundary: Literal["stock", "theme", "industry", "market", "unknown"] = "unknown"
    continuity_hint: Literal["developing", "reignited", "one_off", "unknown"] = "unknown"
    source_priority: Literal["P0", "P1", "P2", "unknown"] = "unknown"
    linked_assets: list[dict[str, Any]] = Field(default_factory=list)
    relevance_score: float = 0.0
    relevance_reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class TimelineNode(BaseModel):
    timeline_id: str
    node_type: Literal["event", "catalyst", "theme_candidate"]
    stage: str
    timestamp: str
    theme_name: str = ""
    theme_names: list[str] = Field(default_factory=list)
    event_id: str = ""
    cluster_id: str = ""
    node_title: str = ""
    node_summary: str = ""
    catalyst_type: str = ""
    catalyst_strength: str = "unknown"
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    linked_assets: list[dict[str, Any]] = Field(default_factory=list)


class WatchlistLinkageRecord(BaseModel):
    linkage_id: str
    theme_candidate_id: str = ""
    theme_name: str = ""
    cluster_id: str = ""
    watchlist_hits: list[dict[str, Any]] = Field(default_factory=list)
    watchlist_hit_count: int = 0
    watchlist_match_summary: str = ""
    source_refs: list[str] = Field(default_factory=list)
    top_evidence: list[dict[str, Any]] = Field(default_factory=list)
    candidate_stocks: list[dict[str, Any]] = Field(default_factory=list)
    linked_assets: list[dict[str, Any]] = Field(default_factory=list)


class RankedResultFeedItem(BaseModel):
    rank_position: int
    theme_candidate_id: str = ""
    cluster_id: str = ""
    theme_name: str
    relevance_score: float
    relevance_reason: str = ""
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    core_narrative: str = ""
    catalyst_summary: str = ""
    fermentation_stage: str = ""
    fermentation_phase: str = ""
    theme_heat_score: float = 0.0
    timeliness_level: str = "unknown"
    watchlist_hit_count: int = 0
    watchlist_hits: list[dict[str, Any]] = Field(default_factory=list)
    top_evidence: list[dict[str, Any]] = Field(default_factory=list)
    candidate_stocks: list[dict[str, Any]] = Field(default_factory=list)
    linked_assets: list[dict[str, Any]] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    risk_notice: str = ""


class ValuableMessage(BaseModel):
    message_id: str
    message_key: str = ""
    title: str
    summary: str = ""
    event_subject: str = ""
    event_type: str = ""
    event_time: str = ""
    source_name: str = ""
    source_url: str = ""
    source_priority: str = "unknown"
    catalyst_type: str = ""
    catalyst_strength: str = "unknown"
    impact_direction: str = "neutral"
    impact_scope: str = "unknown"
    continuity_hint: str = "unknown"
    related_themes: list[str] = Field(default_factory=list)
    related_industries: list[str] = Field(default_factory=list)
    linked_assets: list[dict[str, Any]] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    value_score: float = 0.0
    value_label: str = ""
    discard_reasons: list[str] = Field(default_factory=list)


class MessageFermentationJudgement(BaseModel):
    message_id: str
    message_title: str = ""
    fermentation_verdict: str = "reject"
    fermentation_score: float = 0.0
    why_it_may_ferment: list[str] = Field(default_factory=list)
    why_it_may_not_ferment: list[str] = Field(default_factory=list)
    freshness_signal: str = ""
    continuity_signal: str = ""
    novelty_signal: str = ""
    consensus_stage: str = ""
    rejection_reason: str = ""


class MessageImpactAnalysis(BaseModel):
    message_id: str
    message_title: str = ""
    impact_themes: list[str] = Field(default_factory=list)
    primary_theme: str = ""
    impact_direction: str = ""
    impact_scope: str = ""
    impact_horizon: str = ""
    impact_path: str = ""
    impact_summary: str = ""
    theme_confidence: float = 0.0
    counter_themes: list[str] = Field(default_factory=list)
    theme_cluster_ref: str = ""
    theme_heat_score: float = 0.0


class MessageCompanyCandidate(BaseModel):
    message_id: str
    message_title: str = ""
    primary_theme: str = ""
    companies: list[dict[str, Any]] = Field(default_factory=list)
    candidate_count: int = 0


class MessageReasoning(BaseModel):
    message_id: str
    message_title: str = ""
    primary_theme: str = ""
    companies: list[dict[str, Any]] = Field(default_factory=list)


class MessageValidationFeedback(BaseModel):
    message_id: str
    predicted_direction: str = ""
    predicted_strength: str = ""
    validation_window: str = ""
    observed_company_moves: list[dict[str, Any]] = Field(default_factory=list)
    observed_basket_move: dict[str, Any] = Field(default_factory=dict)
    observed_benchmark_move: dict[str, Any] = Field(default_factory=dict)
    excess_return: float | None = None
    validation_status: str = "unverifiable"
    prediction_gap: str = ""
    lagging_signal: bool = False
    calibration_action: str = "keep"
    calibration_reason: str = ""
    validation_summary: str = ""
    market_validation_score: float | None = None


class MessageScore(BaseModel):
    message_id: str
    message_title: str = ""
    importance_score: float = 0.0
    fermentation_score: float = 0.0
    impact_quality_score: float = 0.0
    company_discovery_score: float = 0.0
    reason_quality_score: float = 0.0
    market_validation_score: float | None = None
    initial_actionability_score: float = 0.0
    recalibrated_actionability_score: float = 0.0
    final_verdict: str = "unverifiable"
    score_summary: str = ""


class DailyMessageWorkbench(BaseModel):
    run_id: str
    status: str = "empty"
    message_count: int = 0
    messages: list[dict[str, Any]] = Field(default_factory=list)


class DailyThemeWorkbench(BaseModel):
    run_id: str
    status: str = "empty"
    theme_count: int = 0
    themes: list[dict[str, Any]] = Field(default_factory=list)


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
