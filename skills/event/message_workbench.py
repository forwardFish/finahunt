from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from packages.llm import MultiModelRouter
from packages.utils import load_yaml
from skills.event.stock_reasoning import (
    StockReasonLLMWriter,
    XueqiuEvidenceResolver,
    is_valid_candidate_stock_name,
    normalize_candidate_stock_name,
)
from skills.market import QuoteSnapshotAdapter


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
_STRENGTH_SCORE = {"high": 92.0, "medium": 70.0, "low": 46.0, "unknown": 28.0}
_SOURCE_PRIORITY_SCORE = {"P0": 92.0, "P1": 74.0, "P2": 52.0, "unknown": 35.0}
_ROLE_LABELS = {
    "core_beneficiary": "核心受益",
    "direct_link": "直接关联",
    "supply_chain_link": "产业链受益",
    "peripheral_watch": "观察项",
}
_ROLE_SCORE = {
    "core_beneficiary": 92.0,
    "direct_link": 78.0,
    "supply_chain_link": 60.0,
    "peripheral_watch": 38.0,
}
_MUNDANE_KEYWORDS = (
    "沪牌",
    "拍牌",
    "天气",
    "交通",
    "停水",
    "停电",
    "地铁",
    "演出",
    "旅游",
    "门票",
    "招生",
)
_INDUSTRY_HINTS = (
    "政策",
    "订单",
    "中标",
    "产品",
    "突破",
    "量产",
    "采购",
    "储能",
    "光伏",
    "机器人",
    "算力",
    "AI",
    "创新药",
    "军工",
    "半导体",
    "低空",
)
_CROWDING_PENALTY_HINTS = ("涨停", "连板", "爆量", "一致性", "封板", "爆发")
_STAGE_LABELS = {
    "message_processing": "消息处理",
    "fermentation_judgement": "发酵判断",
    "impact_analysis": "影响分析",
    "company_mining": "相关公司",
    "reasoning": "公司理由",
    "validation_calibration": "验证校正",
    "fermenting_theme_feed": "题材聚合",
    "low_position_orchestrator": "工作台汇总",
}

_THEME_RULES: dict[str, list[str]] | None = None


def build_valuable_messages(
    canonical_events: list[dict[str, Any]],
    normalized_documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    document_map = {
        str(item.get("url", "") or item.get("source_url", "") or ""): item
        for item in normalized_documents
        if str(item.get("url", "") or item.get("source_url", "") or "")
    }
    messages: list[dict[str, Any]] = []

    for event in canonical_events:
        primary_url = next((ref for ref in event.get("source_refs", []) if str(ref).startswith("http")), "")
        source_doc = document_map.get(str(primary_url), {})
        title = str(event.get("title", "") or source_doc.get("title", "") or "").strip()
        summary = str(event.get("summary", "") or source_doc.get("summary", "") or "").strip()
        content_text = _extract_document_text(source_doc)
        message_text = _message_text(title, summary, str(event.get("event_subject", "") or ""), content_text)
        related_themes = _message_theme_matches(message_text, [*event.get("related_themes", []), *event.get("theme_tags", [])])
        linked_assets = _normalize_linked_assets(event.get("linked_assets", []))
        value_score = _message_value_score(event, related_themes, message_text, linked_assets)
        discard_reasons = _message_discard_reasons(message_text, related_themes, linked_assets, value_score)

        if discard_reasons:
            continue

        messages.append(
            {
                "message_id": str(event.get("event_id", "") or ""),
                "message_key": str(event.get("canonical_key", "") or event.get("event_id", "") or ""),
                "title": title,
                "summary": summary,
                "event_subject": str(event.get("event_subject", "") or ""),
                "event_type": str(event.get("event_type", "") or ""),
                "event_time": str(event.get("event_time", "") or event.get("first_disclosed_at", "") or ""),
                "occurred_at": str(event.get("occurred_at", "") or ""),
                "source_name": str(source_doc.get("source_name", "") or source_doc.get("site_name", "") or ""),
                "source_url": str(primary_url or source_doc.get("url", "") or source_doc.get("source_url", "") or ""),
                "source_priority": str(event.get("source_priority", "unknown") or "unknown"),
                "catalyst_type": str(event.get("catalyst_type", "") or ""),
                "catalyst_strength": str(event.get("catalyst_strength", "unknown") or "unknown"),
                "impact_direction": str(event.get("impact_direction", "neutral") or "neutral"),
                "impact_scope": str(event.get("impact_scope", "unknown") or "unknown"),
                "continuity_hint": str(event.get("continuity_hint", "unknown") or "unknown"),
                "related_themes": related_themes,
                "related_industries": _unique_strings(event.get("related_industries", [])),
                "linked_assets": linked_assets,
                "source_refs": _unique_strings(event.get("source_refs", [])),
                "evidence_refs": _unique_strings(event.get("evidence_refs", [])),
                "message_text": message_text,
                "value_score": round(value_score, 2),
                "value_label": _message_value_label(value_score),
                "discard_reasons": discard_reasons,
            }
        )

    return sorted(messages, key=lambda item: (item.get("value_score", 0.0), item.get("event_time", "")), reverse=True)


def build_message_fermentation_judgements(
    valuable_messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for message in valuable_messages:
        freshness = _freshness_score(message.get("event_time", ""))
        continuity = _continuity_hint_score(message.get("continuity_hint", "unknown"))
        novelty = _novelty_score(message)
        crowding_penalty = _crowding_penalty(message.get("message_text", ""))
        catalyst_strength = _STRENGTH_SCORE.get(str(message.get("catalyst_strength", "unknown")), 28.0)
        fermentation_score = round(
            (catalyst_strength * 0.35)
            + (freshness * 0.24)
            + (continuity * 0.2)
            + (novelty * 0.21)
            - crowding_penalty,
            2,
        )
        verdict = _fermentation_verdict(fermentation_score, message)
        outputs.append(
            {
                "message_id": message.get("message_id", ""),
                "message_title": message.get("title", ""),
                "fermentation_verdict": verdict,
                "fermentation_score": fermentation_score,
                "why_it_may_ferment": _why_it_may_ferment(message, freshness, continuity, novelty),
                "why_it_may_not_ferment": _why_it_may_not_ferment(message, crowding_penalty),
                "freshness_signal": _freshness_signal(freshness),
                "continuity_signal": _continuity_signal(continuity),
                "novelty_signal": _novelty_signal(novelty),
                "consensus_stage": _consensus_stage(message, crowding_penalty),
                "rejection_reason": _rejection_reason(verdict, message, crowding_penalty),
            }
        )
    return outputs


def build_message_impact_analysis(
    valuable_messages: list[dict[str, Any]],
    message_fermentation_judgements: list[dict[str, Any]],
    theme_clusters: list[dict[str, Any]],
    theme_heat_snapshots: list[dict[str, Any]],
    low_position_opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fermentation_by_id = {str(item.get("message_id", "")): item for item in message_fermentation_judgements}
    cluster_by_theme = {str(item.get("theme_name", "") or ""): item for item in theme_clusters if item.get("theme_name")}
    heat_by_theme = {str(item.get("theme_name", "") or ""): item for item in theme_heat_snapshots if item.get("theme_name")}
    low_by_theme = {str(item.get("theme_name", "") or ""): item for item in low_position_opportunities if item.get("theme_name")}
    outputs: list[dict[str, Any]] = []

    for message in valuable_messages:
        fermentation = fermentation_by_id.get(message.get("message_id", ""), {})
        themes = _impact_themes_for_message(message)
        primary_theme = themes[0] if themes else ""
        cluster = cluster_by_theme.get(primary_theme, {})
        heat = heat_by_theme.get(primary_theme, {})
        low = low_by_theme.get(primary_theme, {})
        theme_confidence = _theme_confidence(message, fermentation, cluster, heat, low)
        outputs.append(
            {
                "message_id": message.get("message_id", ""),
                "message_title": message.get("title", ""),
                "impact_themes": themes,
                "primary_theme": primary_theme,
                "impact_direction": _impact_direction_label(message.get("impact_direction", "neutral")),
                "impact_scope": _impact_scope_label(message.get("impact_scope", "unknown")),
                "impact_horizon": _impact_horizon(message, fermentation),
                "impact_path": _impact_path(message, primary_theme),
                "impact_summary": _impact_summary(message, primary_theme, fermentation, cluster),
                "theme_confidence": round(theme_confidence, 2),
                "counter_themes": _counter_themes(message, themes),
                "theme_cluster_ref": cluster.get("cluster_id", ""),
                "theme_heat_score": _safe_float(heat.get("theme_heat_score")) or _safe_float(low.get("low_position_score")) or 0.0,
            }
        )
    return outputs


def build_workbench_stage_statuses(state: dict[str, Any]) -> list[dict[str, str]]:
    stages = [
        "message_processing",
        "fermentation_judgement",
        "impact_analysis",
        "company_mining",
        "reasoning",
        "validation_calibration",
        "fermenting_theme_feed",
        "low_position_orchestrator",
    ]
    results = state.get("results", {})
    statuses: list[dict[str, str]] = []
    for stage in stages:
        payload = results.get(stage, {})
        status = str(payload.get("status", "pending") or "pending")
        statuses.append({"stage": stage, "label": _STAGE_LABELS.get(stage, stage), "status": status})
    return statuses


def _theme_rules() -> dict[str, list[str]]:
    global _THEME_RULES
    if _THEME_RULES is None:
        standards = load_yaml("config/rules/standards.yaml")
        _THEME_RULES = {
            str(theme): [str(item) for item in keywords]
            for theme, keywords in (standards.get("theme_rules", {}) or {}).items()
            if isinstance(keywords, list)
        }
    return _THEME_RULES


def _message_text(*parts: str) -> str:
    return " ".join(str(part or "").strip() for part in parts if str(part or "").strip())


def _extract_document_text(document: dict[str, Any]) -> str:
    metadata = document.get("metadata", {})
    if isinstance(metadata, dict):
        return str(metadata.get("content_text", "") or "")
    return str(document.get("content_text", "") or "")


def _message_theme_matches(message_text: str, extra_theme_tags: list[str]) -> list[str]:
    text = message_text.lower()
    matches: list[str] = []
    for theme_name, keywords in _theme_rules().items():
        if theme_name in extra_theme_tags:
            matches.append(theme_name)
            continue
        if any(str(keyword).lower() in text for keyword in keywords):
            matches.append(theme_name)
    return _unique_strings(matches)


def _normalize_linked_assets(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for item in assets or []:
        if not isinstance(item, dict):
            continue
        code = str(item.get("asset_code", "") or item.get("code", "") or "").strip()
        name = str(item.get("asset_name", "") or item.get("name", "") or "").strip()
        if not code and not name:
            continue
        outputs.append({"asset_code": code, "asset_name": name})
    return outputs


def _message_value_score(
    event: dict[str, Any],
    related_themes: list[str],
    message_text: str,
    linked_assets: list[dict[str, Any]],
) -> float:
    score = 0.0
    score += _STRENGTH_SCORE.get(str(event.get("catalyst_strength", "unknown")), 28.0) * 0.35
    score += _SOURCE_PRIORITY_SCORE.get(str(event.get("source_priority", "unknown")), 35.0) * 0.18
    score += min(len(related_themes) * 12.0, 18.0)
    score += min(len(linked_assets) * 8.0, 16.0)
    score += 10.0 if any(keyword in message_text for keyword in _INDUSTRY_HINTS) else 0.0
    score -= 24.0 if any(keyword in message_text for keyword in _MUNDANE_KEYWORDS) else 0.0
    return max(0.0, min(100.0, score))


def _message_discard_reasons(
    message_text: str,
    related_themes: list[str],
    linked_assets: list[dict[str, Any]],
    value_score: float,
) -> list[str]:
    reasons: list[str] = []
    if any(keyword in message_text for keyword in _MUNDANE_KEYWORDS) and not related_themes and not linked_assets:
        reasons.append("非产业相关日常资讯")
    if value_score < 34 and not linked_assets:
        reasons.append("催化和关联度过弱")
    if not related_themes and not linked_assets:
        reasons.append("缺少题材和公司线索")
    return reasons


def _message_value_label(value_score: float) -> str:
    if value_score >= 78:
        return "高价值消息"
    if value_score >= 58:
        return "可跟踪消息"
    return "观察消息"


def _freshness_score(event_time: str) -> float:
    dt = _parse_dt(event_time)
    if not dt:
        return 45.0
    hours = max(0.0, (datetime.now(UTC) - dt).total_seconds() / 3600)
    if hours <= 6:
        return 92.0
    if hours <= 24:
        return 78.0
    if hours <= 72:
        return 62.0
    return 44.0


def _continuity_hint_score(value: str) -> float:
    mapping = {"developing": 82.0, "reignited": 74.0, "one_off": 38.0, "unknown": 52.0}
    return mapping.get(str(value or "unknown"), 52.0)


def _novelty_score(message: dict[str, Any]) -> float:
    score = 45.0
    if message.get("catalyst_type") in {"policy", "order", "product", "announcement"}:
        score += 18.0
    if message.get("source_priority") == "P0":
        score += 12.0
    if message.get("linked_assets"):
        score += 8.0
    if len(message.get("related_themes", [])) == 1:
        score += 7.0
    return min(100.0, score)


def _crowding_penalty(message_text: str) -> float:
    if not message_text:
        return 0.0
    return 12.0 if any(keyword in message_text for keyword in _CROWDING_PENALTY_HINTS) else 0.0


def _fermentation_verdict(score: float, message: dict[str, Any]) -> str:
    if not message.get("related_themes") and not message.get("linked_assets"):
        return "reject"
    if score >= 78:
        return "high"
    if score >= 60:
        return "medium"
    if score >= 45:
        return "low"
    return "reject"


def _parse_dt(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    outputs: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        outputs.append(text)
    return outputs


def build_message_company_candidates(
    valuable_messages: list[dict[str, Any]],
    message_impact_analysis: list[dict[str, Any]],
    mapped_theme_clusters: list[dict[str, Any]],
    judged_theme_clusters: list[dict[str, Any]],
    low_position_opportunities: list[dict[str, Any]],
    symbol_catalog: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    impact_by_id = {str(item.get("message_id", "")): item for item in message_impact_analysis}
    mapped_by_theme = {str(item.get("theme_name", "") or ""): item for item in mapped_theme_clusters if item.get("theme_name")}
    judged_by_theme = {str(item.get("theme_name", "") or ""): item for item in judged_theme_clusters if item.get("theme_name")}
    low_by_theme = {str(item.get("theme_name", "") or ""): item for item in low_position_opportunities if item.get("theme_name")}
    outputs: list[dict[str, Any]] = []

    for message in valuable_messages:
        impact = impact_by_id.get(message.get("message_id", ""), {})
        primary_theme = str(impact.get("primary_theme", "") or "")
        mapped_cluster = mapped_by_theme.get(primary_theme, {})
        judged_cluster = judged_by_theme.get(primary_theme, {})
        low_theme = low_by_theme.get(primary_theme, {})
        candidates: dict[str, dict[str, Any]] = {}

        for asset in message.get("linked_assets", []):
            company = _company_from_direct_asset(message, asset, primary_theme)
            if not company:
                continue
            key = company.get("company_code") or company.get("company_name")
            candidates[str(key)] = company

        candidate_sources = [
            *mapped_cluster.get("candidate_pool", []),
            *judged_cluster.get("candidate_pool", []),
            *low_theme.get("candidate_stocks", []),
        ]
        for item in candidate_sources:
            company = _company_from_theme_candidate(message, impact, item, symbol_catalog or {})
            if not company:
                continue
            key = company.get("company_code") or company.get("company_name")
            existing = candidates.get(str(key))
            if existing:
                company = _merge_company_candidate(existing, company)
            candidates[str(key)] = company

        companies = sorted(
            candidates.values(),
            key=lambda item: (
                item.get("candidate_status") == "confirmed",
                item.get("relevance_score", 0.0),
                item.get("purity_score") or 0.0,
            ),
            reverse=True,
        )[:6]
        outputs.append(
            {
                "message_id": message.get("message_id", ""),
                "message_title": message.get("title", ""),
                "primary_theme": primary_theme,
                "companies": companies,
                "candidate_count": len(companies),
            }
        )

    return outputs


def build_symbol_catalog(
    canonical_events: list[dict[str, Any]],
    normalized_documents: list[dict[str, Any]],
) -> dict[str, str]:
    catalog: dict[str, str] = {}

    for event in canonical_events:
        for asset in event.get("linked_assets", []) or []:
            code = str(asset.get("asset_code", "") or asset.get("code", "") or "").strip()
            name = normalize_candidate_stock_name(str(asset.get("asset_name", "") or asset.get("name", "") or ""))
            if code and name:
                catalog[name] = code

    for document in normalized_documents:
        metadata = document.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        stock_rows = []
        for key in ("stock_list", "stocks", "symbol_list"):
            value = metadata.get(key)
            if isinstance(value, list):
                stock_rows.extend(value)
        for row in stock_rows:
            if not isinstance(row, dict):
                continue
            code = str(row.get("secu_code", "") or row.get("code", "") or row.get("stock_code", "") or "").strip()
            name = normalize_candidate_stock_name(str(row.get("secu_name", "") or row.get("name", "") or row.get("stock_name", "") or ""))
            if code and name:
                catalog[name] = code

    return catalog


def build_message_reasoning(
    message_company_candidates: list[dict[str, Any]],
    message_impact_analysis: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    impact_by_id = {str(item.get("message_id", "")): item for item in message_impact_analysis}
    evidence_resolver = XueqiuEvidenceResolver()
    router = MultiModelRouter(agent_id="stock_reason_writer")
    llm_writer = StockReasonLLMWriter(router, fallback_models=["moonshot/kimi-k2.5", "deepseek/deepseek-chat"])
    outputs: list[dict[str, Any]] = []

    for message in message_company_candidates:
        impact = impact_by_id.get(message.get("message_id", ""), {})
        cluster_stub = {
            "theme_name": message.get("primary_theme", ""),
            "core_narrative": impact.get("impact_summary", ""),
            "supporting_signals": [],
        }
        companies: list[dict[str, Any]] = []
        for company in message.get("companies", []):
            stock_name = str(company.get("company_name", "") or "")
            stock_code = str(company.get("company_code", "") or "")
            evidence_items = _merge_evidence_items(
                company.get("source_evidence_items", []),
                _build_runtime_evidence_items(evidence_resolver, cluster_stub, stock_name, stock_code),
            )
            primary_reason = _primary_source_reason(evidence_items)
            source_reason = primary_reason["source_reason"] or "pending_source_evidence"
            llm_reason = str(company.get("llm_reason", "") or "").strip()
            if not llm_reason and source_reason != "pending_source_evidence":
                payload = evidence_resolver.resolve(cluster_stub, stock_name, stock_code)
                llm_reason = llm_writer.build_reason(cluster_stub, company, payload)
            companies.append(
                {
                    **company,
                    **primary_reason,
                    "source_reason": source_reason,
                    "source_evidence_items": evidence_items[:3],
                    "llm_reason": llm_reason,
                    "crosscheck_status": _reasoning_crosscheck_status(source_reason, llm_reason),
                    "reason_summary": _company_reason_summary(company, source_reason, llm_reason),
                }
            )
        outputs.append(
            {
                "message_id": message.get("message_id", ""),
                "message_title": message.get("message_title", ""),
                "primary_theme": message.get("primary_theme", ""),
                "companies": companies,
            }
        )
    return outputs


def build_message_validation_feedback(
    valuable_messages: list[dict[str, Any]],
    message_fermentation_judgements: list[dict[str, Any]],
    message_impact_analysis: list[dict[str, Any]],
    message_company_candidates: list[dict[str, Any]],
    message_reasoning: list[dict[str, Any]],
    *,
    quote_adapter: QuoteSnapshotAdapter | None = None,
) -> list[dict[str, Any]]:
    fermentation_by_id = {str(item.get("message_id", "")): item for item in message_fermentation_judgements}
    impact_by_id = {str(item.get("message_id", "")): item for item in message_impact_analysis}
    companies_by_id = {str(item.get("message_id", "")): item.get("companies", []) for item in message_company_candidates}
    reasoning_by_id = {str(item.get("message_id", "")): item.get("companies", []) for item in message_reasoning}
    adapter = quote_adapter or QuoteSnapshotAdapter()
    outputs: list[dict[str, Any]] = []

    for message in valuable_messages:
        message_id = str(message.get("message_id", ""))
        impact = impact_by_id.get(message_id, {})
        fermentation = fermentation_by_id.get(message_id, {})
        reasoning_companies = reasoning_by_id.get(message_id, companies_by_id.get(message_id, []))
        tracked = [
            item
            for item in reasoning_companies
            if item.get("company_code") and item.get("role") in {"core_beneficiary", "direct_link", "supply_chain_link"}
        ][:4]
        snapshot = adapter.fetch_validation_snapshot(
            codes=[str(item.get("company_code", "")) for item in tracked if item.get("company_code")],
            event_time=str(message.get("event_time", "") or ""),
        )
        validation = _evaluate_market_validation(message, fermentation, impact, tracked, snapshot)
        outputs.append(
            {
                "message_id": message_id,
                "predicted_direction": impact.get("impact_direction", "-"),
                "predicted_strength": fermentation.get("fermentation_verdict", "reject"),
                "validation_window": validation["validation_window"],
                "observed_company_moves": validation["observed_company_moves"],
                "observed_basket_move": validation["observed_basket_move"],
                "observed_benchmark_move": validation["observed_benchmark_move"],
                "excess_return": validation["excess_return"],
                "validation_status": validation["validation_status"],
                "prediction_gap": validation["prediction_gap"],
                "lagging_signal": validation["lagging_signal"],
                "calibration_action": validation["calibration_action"],
                "calibration_reason": validation["calibration_reason"],
                "validation_summary": validation["validation_summary"],
                "market_validation_score": validation["market_validation_score"],
            }
        )

    return outputs


def build_message_scores(
    valuable_messages: list[dict[str, Any]],
    message_fermentation_judgements: list[dict[str, Any]],
    message_impact_analysis: list[dict[str, Any]],
    message_company_candidates: list[dict[str, Any]],
    message_reasoning: list[dict[str, Any]],
    message_validation_feedback: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fermentation_by_id = {str(item.get("message_id", "")): item for item in message_fermentation_judgements}
    impact_by_id = {str(item.get("message_id", "")): item for item in message_impact_analysis}
    companies_by_id = {str(item.get("message_id", "")): item.get("companies", []) for item in message_company_candidates}
    reasoning_by_id = {str(item.get("message_id", "")): item.get("companies", []) for item in message_reasoning}
    validation_by_id = {str(item.get("message_id", "")): item for item in message_validation_feedback}
    outputs: list[dict[str, Any]] = []

    for message in valuable_messages:
        message_id = str(message.get("message_id", ""))
        fermentation = fermentation_by_id.get(message_id, {})
        impact = impact_by_id.get(message_id, {})
        companies = companies_by_id.get(message_id, [])
        reasoning = reasoning_by_id.get(message_id, [])
        validation = validation_by_id.get(message_id, {})
        importance_score = round(_safe_float(message.get("value_score")) or 0.0, 2)
        fermentation_score = round(_safe_float(fermentation.get("fermentation_score")) or 0.0, 2)
        impact_quality_score = round(
            min(100.0, ((_safe_float(impact.get("theme_confidence")) or 0.0) * 0.7) + (len(impact.get("impact_themes", [])) * 8.0)),
            2,
        )
        company_discovery_score = round(_company_discovery_score(companies), 2)
        reason_quality_score = round(_reason_quality_score(reasoning), 2)
        market_validation_score = validation.get("market_validation_score")
        initial_actionability_score = round(
            (importance_score * 0.24)
            + (fermentation_score * 0.22)
            + (impact_quality_score * 0.22)
            + (company_discovery_score * 0.18)
            + (reason_quality_score * 0.14),
            2,
        )
        recalibrated_actionability_score = _recalibrated_score(initial_actionability_score, market_validation_score, validation)
        outputs.append(
            {
                "message_id": message_id,
                "message_title": message.get("title", ""),
                "importance_score": importance_score,
                "fermentation_score": fermentation_score,
                "impact_quality_score": impact_quality_score,
                "company_discovery_score": company_discovery_score,
                "reason_quality_score": reason_quality_score,
                "market_validation_score": market_validation_score,
                "initial_actionability_score": initial_actionability_score,
                "recalibrated_actionability_score": recalibrated_actionability_score,
                "final_verdict": validation.get("validation_status", "unverifiable"),
                "score_summary": _score_summary(initial_actionability_score, recalibrated_actionability_score, validation),
            }
        )

    return outputs


def build_daily_message_workbench(
    valuable_messages: list[dict[str, Any]],
    message_fermentation_judgements: list[dict[str, Any]],
    message_impact_analysis: list[dict[str, Any]],
    message_reasoning: list[dict[str, Any]],
    message_validation_feedback: list[dict[str, Any]],
    message_scores: list[dict[str, Any]],
    *,
    run_id: str,
) -> dict[str, Any]:
    fermentation_by_id = {str(item.get("message_id", "")): item for item in message_fermentation_judgements}
    impact_by_id = {str(item.get("message_id", "")): item for item in message_impact_analysis}
    reasoning_by_id = {str(item.get("message_id", "")): item for item in message_reasoning}
    validation_by_id = {str(item.get("message_id", "")): item for item in message_validation_feedback}
    score_by_id = {str(item.get("message_id", "")): item for item in message_scores}
    rows = []

    for message in valuable_messages:
        rows.append(
            {
                "message": message,
                "fermentation": fermentation_by_id.get(message.get("message_id", ""), {}),
                "impact": impact_by_id.get(message.get("message_id", ""), {}),
                "companies": reasoning_by_id.get(message.get("message_id", ""), {}).get("companies", []),
                "validation": validation_by_id.get(message.get("message_id", ""), {}),
                "score": score_by_id.get(message.get("message_id", ""), {}),
            }
        )

    rows.sort(key=lambda item: item.get("score", {}).get("recalibrated_actionability_score", 0.0), reverse=True)
    status = "success" if rows else "empty"
    if any((row.get("validation", {}).get("validation_status") == "unverifiable") for row in rows):
        status = "partial" if rows else "empty"
    return {
        "run_id": run_id,
        "status": status,
        "message_count": len(rows),
        "messages": rows,
    }


def build_daily_theme_workbench(
    daily_message_workbench: dict[str, Any],
    low_position_opportunities: list[dict[str, Any]],
    fermenting_theme_feed: list[dict[str, Any]],
    *,
    run_id: str,
) -> dict[str, Any]:
    theme_index: dict[str, dict[str, Any]] = {}

    for item in low_position_opportunities:
        theme_name = str(item.get("theme_name", "") or "")
        if not theme_name:
            continue
        theme_index[theme_name] = {
            "theme_name": theme_name,
            "low_position_score": item.get("low_position_score"),
            "low_position_reason": item.get("low_position_reason", ""),
            "fermentation_phase": item.get("fermentation_phase", ""),
            "risk_notice": item.get("risk_notice", ""),
            "candidate_stocks": item.get("candidate_stocks", []),
            "messages": [],
            "validation_bucket": "观察中题材",
        }

    for item in fermenting_theme_feed:
        theme_name = str(item.get("theme_name", "") or "")
        if not theme_name:
            continue
        current = theme_index.setdefault(
            theme_name,
            {
                "theme_name": theme_name,
                "low_position_score": None,
                "low_position_reason": "",
                "fermentation_phase": item.get("fermentation_phase", ""),
                "risk_notice": item.get("risk_notice", ""),
                "candidate_stocks": item.get("candidate_stocks", []),
                "messages": [],
                "validation_bucket": "观察中题材",
            },
        )
        if not current.get("candidate_stocks"):
            current["candidate_stocks"] = item.get("candidate_stocks", [])
        current["fermentation_phase"] = current.get("fermentation_phase") or item.get("fermentation_phase", "")

    for row in daily_message_workbench.get("messages", []):
        impact = row.get("impact", {})
        validation = row.get("validation", {})
        bucket = _theme_validation_bucket(str(validation.get("validation_status", "")))
        for theme_name in impact.get("impact_themes", []):
            current = theme_index.setdefault(
                theme_name,
                {
                    "theme_name": theme_name,
                    "low_position_score": None,
                    "low_position_reason": "",
                    "fermentation_phase": impact.get("impact_horizon", ""),
                    "risk_notice": "",
                    "candidate_stocks": [],
                    "messages": [],
                    "validation_bucket": bucket,
                },
            )
            current["validation_bucket"] = _merge_theme_validation_bucket(current.get("validation_bucket", "观察中题材"), bucket)
            current["messages"].append(
                {
                    "message_id": row.get("message", {}).get("message_id", ""),
                    "title": row.get("message", {}).get("title", ""),
                    "summary": row.get("message", {}).get("summary", ""),
                    "event_time": row.get("message", {}).get("event_time", ""),
                    "score": row.get("score", {}).get("recalibrated_actionability_score"),
                    "validation_status": validation.get("validation_status", "unverifiable"),
                }
            )

    themes = sorted(
        theme_index.values(),
        key=lambda item: ((item.get("low_position_score") or 0.0), len(item.get("messages", []))),
        reverse=True,
    )
    validated = [item for item in themes if item.get("validation_bucket") == "验证通过题材"]
    watching = [item for item in themes if item.get("validation_bucket") == "观察中题材"]
    downgraded = [item for item in themes if item.get("validation_bucket") == "被校正降级题材"]
    return {
        "run_id": run_id,
        "status": "success" if themes else "empty",
        "theme_count": len(themes),
        "themes": themes,
        "validated_themes": validated,
        "watch_themes": watching,
        "downgraded_themes": downgraded,
    }


def _why_it_may_ferment(message: dict[str, Any], freshness: float, continuity: float, novelty: float) -> list[str]:
    reasons: list[str] = []
    if _STRENGTH_SCORE.get(str(message.get("catalyst_strength", "unknown")), 28.0) >= 68:
        reasons.append("催化强度较高")
    if freshness >= 70:
        reasons.append("消息仍处于新鲜窗口")
    if continuity >= 70:
        reasons.append("后续仍有持续发酵空间")
    if novelty >= 68:
        reasons.append("叙事具备扩散潜力")
    if message.get("linked_assets"):
        reasons.append("已出现可映射的公司线索")
    return reasons or ["具备基础研究价值，但仍需更多市场证据确认"]


def _why_it_may_not_ferment(message: dict[str, Any], crowding_penalty: float) -> list[str]:
    reasons: list[str] = []
    if message.get("continuity_hint") == "one_off":
        reasons.append("当前更像单次消息，持续性偏弱")
    if crowding_penalty > 0:
        reasons.append("消息中已有拥挤信号，继续扩散空间可能有限")
    if not message.get("related_themes"):
        reasons.append("题材归因仍不够稳定")
    return reasons


def _freshness_signal(score: float) -> str:
    if score >= 80:
        return "新近披露"
    if score >= 60:
        return "仍在有效窗口"
    return "偏滞后"


def _continuity_signal(score: float) -> str:
    if score >= 80:
        return "连续催化"
    if score >= 60:
        return "具备延续性"
    return "连续性偏弱"


def _novelty_signal(score: float) -> str:
    if score >= 80:
        return "新逻辑窗口"
    if score >= 60:
        return "旧逻辑再强化"
    return "新意有限"


def _consensus_stage(message: dict[str, Any], crowding_penalty: float) -> str:
    if crowding_penalty > 0:
        return "中后段共识"
    if message.get("source_priority") == "P0":
        return "早期认知区间"
    return "观察阶段"


def _rejection_reason(verdict: str, message: dict[str, Any], crowding_penalty: float) -> str:
    if verdict != "reject":
        return ""
    if not message.get("related_themes") and not message.get("linked_assets"):
        return "没有形成可追踪的题材和公司线索"
    if crowding_penalty > 0:
        return "消息已明显拥挤，不再适合作为低位研究信号"
    return "催化和延续性不足"


def _impact_themes_for_message(message: dict[str, Any]) -> list[str]:
    return _unique_strings(message.get("related_themes", []))[:3]


def _theme_confidence(
    message: dict[str, Any],
    fermentation: dict[str, Any],
    cluster: dict[str, Any],
    heat: dict[str, Any],
    low: dict[str, Any],
) -> float:
    score = (_safe_float(fermentation.get("fermentation_score")) or 0.0) * 0.42
    score += (_safe_float(message.get("value_score")) or 0.0) * 0.26
    score += (_safe_float(heat.get("theme_heat_score")) or 0.0) * 0.14
    score += (_safe_float(low.get("low_position_score")) or 0.0) * 0.1
    if cluster.get("cluster_id"):
        score += 8.0
    if message.get("linked_assets"):
        score += 6.0
    return min(100.0, score)


def _impact_direction_label(value: str) -> str:
    return {
        "positive": "正向扩散",
        "negative": "负向扰动",
        "mixed": "双向影响",
        "neutral": "中性观察",
    }.get(str(value or "neutral"), "中性观察")


def _impact_scope_label(value: str) -> str:
    return {
        "stock": "单股影响",
        "sector": "板块影响",
        "industry": "产业链影响",
        "market": "市场影响",
        "macro": "宏观影响",
        "unknown": "范围待确认",
    }.get(str(value or "unknown"), "范围待确认")


def _impact_horizon(message: dict[str, Any], fermentation: dict[str, Any]) -> str:
    if fermentation.get("fermentation_verdict") == "high":
        return "1-3个交易日"
    if message.get("continuity_hint") == "developing":
        return "2-5个交易日"
    if message.get("continuity_hint") == "reignited":
        return "1周内观察"
    return "当日到1个交易日"


def _impact_path(message: dict[str, Any], primary_theme: str) -> str:
    if not primary_theme:
        return "消息先影响单点认知，再决定是否扩散"
    if message.get("linked_assets"):
        return "消息催化 -> 核心公司验证 -> 题材扩散"
    return "题材催化 -> 产业链扩散 -> 资金确认"


def _impact_summary(
    message: dict[str, Any],
    primary_theme: str,
    fermentation: dict[str, Any],
    cluster: dict[str, Any],
) -> str:
    if not primary_theme:
        return "当前更适合作为消息观察样本，尚未形成稳定题材归因。"
    narrative = str(cluster.get("core_narrative", "") or "").strip()
    if narrative:
        return f"{primary_theme} 当前围绕“{narrative}”形成影响预期，消息更适合作为前置研究信号继续跟踪。"
    if fermentation.get("fermentation_verdict") in {"high", "medium"}:
        return f"{primary_theme} 正在形成早期预期，当前消息更适合作为前置研究信号继续跟踪。"
    return f"{primary_theme} 目前只有初步影响线索，仍需等待更多催化确认。"


def _counter_themes(message: dict[str, Any], themes: list[str]) -> list[str]:
    text = message.get("message_text", "")
    counters: list[str] = []
    for theme_name, keywords in _theme_rules().items():
        if theme_name in themes:
            continue
        if any(keyword in text for keyword in keywords):
            continue
        counters.append(f"{theme_name} 缺少直接文本命中")
    return counters[:3]


def _company_from_direct_asset(message: dict[str, Any], asset: dict[str, Any], primary_theme: str) -> dict[str, Any] | None:
    stock_code = str(asset.get("asset_code", "") or "").strip()
    stock_name = normalize_candidate_stock_name(str(asset.get("asset_name", "") or ""))
    if not stock_code and not stock_name:
        return None
    evidence_items = _build_message_source_evidence_items(message, stock_name, stock_code)
    primary_reason = _primary_source_reason(evidence_items)
    return {
        "company_name": stock_name or stock_code,
        "company_code": stock_code,
        "role": "direct_link",
        "role_label": _ROLE_LABELS["direct_link"],
        "relevance_score": 82.0,
        "purity_score": None,
        "scarcity_score": None,
        "mapping_reason": "消息原文或事件对象已直接提到该公司。",
        "candidate_status": "confirmed",
        "source_evidence_items": evidence_items,
        **primary_reason,
        "llm_reason": "",
        "risk_flags": [],
        "theme_name": primary_theme,
        "evidence_refs": message.get("evidence_refs", []),
    }


def _company_from_theme_candidate(
    message: dict[str, Any],
    impact: dict[str, Any],
    item: dict[str, Any],
    symbol_catalog: dict[str, str],
) -> dict[str, Any] | None:
    stock_name = normalize_candidate_stock_name(str(item.get("stock_name", "") or item.get("name", "") or ""))
    stock_code = str(item.get("stock_code", "") or item.get("code", "") or "").strip()
    if not stock_code and stock_name:
        stock_code = str(symbol_catalog.get(stock_name, "") or "")
    if not stock_name and not stock_code:
        return None
    if stock_name and not is_valid_candidate_stock_name(stock_name):
        return None
    if not _candidate_matches_message(message, impact, item, stock_name, stock_code):
        return None
    role = str(item.get("mapping_level", "") or item.get("role", "") or "peripheral_watch")
    mapping_confidence = _normalize_score(item.get("mapping_confidence"))
    purity_score = _safe_float(item.get("candidate_purity_score"))
    scarcity_score = _safe_float(item.get("judge_breakdown", {}).get("scarcity_score"))
    evidence_items = _merge_evidence_items(
        _build_message_source_evidence_items(message, stock_name, stock_code),
        _build_candidate_evidence_items(message, item),
    )
    primary_reason = _primary_source_reason(evidence_items)
    candidate_status = "confirmed" if role in {"core_beneficiary", "direct_link"} and (purity_score or 0) >= 60 else "watch"
    if not stock_code:
        candidate_status = "pending_code_resolution"
    return {
        "company_name": stock_name or stock_code,
        "company_code": stock_code,
        "role": role,
        "role_label": _ROLE_LABELS.get(role, "观察项"),
        "relevance_score": round(max(_ROLE_SCORE.get(role, 38.0), mapping_confidence or 0.0), 2),
        "purity_score": purity_score,
        "scarcity_score": scarcity_score,
        "mapping_reason": str(item.get("mapping_reason", "") or "该公司与当前消息主影响题材存在业务关联。"),
        "candidate_status": candidate_status,
        "source_evidence_items": evidence_items,
        **primary_reason,
        "llm_reason": str(item.get("llm_reason", "") or ""),
        "risk_flags": _unique_strings(item.get("risk_flags", [])),
        "theme_name": impact.get("primary_theme", ""),
        "evidence_refs": _unique_strings([*message.get("evidence_refs", []), *item.get("evidence", []), *item.get("source_refs", [])]),
    }


def _candidate_matches_message(
    message: dict[str, Any],
    impact: dict[str, Any],
    item: dict[str, Any],
    stock_name: str,
    stock_code: str,
) -> bool:
    text = _message_text(message.get("title", ""), message.get("summary", ""), message.get("message_text", ""))
    primary_theme = str(impact.get("primary_theme", "") or "")
    if not primary_theme:
        return False
    if stock_name and stock_name in text:
        return True
    if stock_code and stock_code.split(".")[0] in text:
        return True
    source_refs = " ".join(str(ref) for ref in message.get("source_refs", []))
    item_refs = " ".join(str(ref) for ref in [*item.get("source_refs", []), *item.get("evidence", [])])
    if source_refs and item_refs and any(ref in item_refs for ref in message.get("source_refs", []) if str(ref)):
        return True
    purity_score = _safe_float(item.get("candidate_purity_score")) or 0.0
    mapping_level = str(item.get("mapping_level", "") or item.get("role", "") or "")
    if purity_score >= 70 and mapping_level in {"core_beneficiary", "direct_link"} and item.get("theme_name", primary_theme) == primary_theme:
        return True
    return False


def _merge_company_candidate(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    better = right if (right.get("relevance_score", 0.0), right.get("purity_score") or 0.0) >= (
        left.get("relevance_score", 0.0),
        left.get("purity_score") or 0.0,
    ) else left
    return {
        **left,
        **right,
        **better,
        "source_evidence_items": _merge_evidence_items(left.get("source_evidence_items", []), right.get("source_evidence_items", [])),
        "evidence_refs": _unique_strings([*left.get("evidence_refs", []), *right.get("evidence_refs", [])]),
        "risk_flags": _unique_strings([*left.get("risk_flags", []), *right.get("risk_flags", [])]),
        "candidate_status": better.get("candidate_status", left.get("candidate_status", "watch")),
    }


def _build_message_source_evidence_items(message: dict[str, Any], stock_name: str, stock_code: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    text = _message_text(message.get("title", ""), message.get("summary", ""), message.get("message_text", ""))
    if stock_name and stock_name in text:
        items.append(
            {
                "source_site": str(message.get("source_name", "") or ""),
                "source_url": str(message.get("source_url", "") or ""),
                "source_title": str(message.get("title", "") or ""),
                "source_excerpt": _excerpt_for_keyword(text, stock_name),
                "reason": f"消息原文直接提到 {stock_name}",
            }
        )
    elif stock_code and stock_code.split(".")[0] in text:
        items.append(
            {
                "source_site": str(message.get("source_name", "") or ""),
                "source_url": str(message.get("source_url", "") or ""),
                "source_title": str(message.get("title", "") or ""),
                "source_excerpt": _excerpt_for_keyword(text, stock_code.split(".")[0]),
                "reason": f"消息原文直接提到证券代码 {stock_code}",
            }
        )
    return items


def _build_candidate_evidence_items(message: dict[str, Any], candidate: dict[str, Any]) -> list[dict[str, str]]:
    mapping_reason = str(candidate.get("mapping_reason", "") or "")
    source_url = next((str(item) for item in candidate.get("source_refs", []) if str(item).startswith("http")), "")
    if not mapping_reason and not source_url:
        return []
    return [
        {
            "source_site": "题材映射",
            "source_url": source_url,
            "source_title": str(message.get("title", "") or "题材映射依据"),
            "source_excerpt": mapping_reason[:120],
            "reason": "题材候选映射规则命中",
        }
    ]


def _build_runtime_evidence_items(
    resolver: XueqiuEvidenceResolver,
    cluster_stub: dict[str, Any],
    stock_name: str,
    stock_code: str,
) -> list[dict[str, str]]:
    payload = resolver.resolve(cluster_stub, stock_name, stock_code)
    if not payload.reason:
        return []
    return [
        {
            "source_site": payload.source_site,
            "source_url": payload.source_url,
            "source_title": payload.source_title,
            "source_excerpt": payload.source_excerpt,
            "reason": payload.reason,
        }
    ]


def _merge_evidence_items(*groups: list[dict[str, Any]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for group in groups:
        for item in group or []:
            normalized = {
                "source_site": str(item.get("source_site", "") or item.get("site_name", "") or ""),
                "source_url": str(item.get("source_url", "") or ""),
                "source_title": str(item.get("source_title", "") or item.get("title", "") or ""),
                "source_excerpt": str(item.get("source_excerpt", "") or item.get("quote", "") or item.get("excerpt", "") or ""),
                "reason": str(item.get("reason", "") or item.get("source_reason", "") or ""),
            }
            key = (normalized["source_url"], normalized["source_title"], normalized["source_excerpt"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(normalized)
    return merged


def _primary_source_reason(evidence_items: list[dict[str, Any]]) -> dict[str, str]:
    if not evidence_items:
        return {
            "source_reason": "",
            "source_reason_title": "",
            "source_reason_url": "",
            "source_reason_excerpt": "",
        }
    first = evidence_items[0]
    source_excerpt = str(first.get("source_excerpt", "") or "")
    source_reason = str(first.get("reason", "") or source_excerpt or "").strip()
    return {
        "source_reason": source_reason,
        "source_reason_title": str(first.get("source_title", "") or ""),
        "source_reason_url": str(first.get("source_url", "") or ""),
        "source_reason_excerpt": source_excerpt,
    }


def _reasoning_crosscheck_status(source_reason: str, llm_reason: str) -> str:
    if source_reason and source_reason != "pending_source_evidence" and llm_reason:
        return "evidence_and_llm"
    if source_reason and source_reason != "pending_source_evidence":
        return "evidence_only"
    if llm_reason:
        return "llm_only"
    return "pending"


def _company_reason_summary(company: dict[str, Any], source_reason: str, llm_reason: str) -> str:
    company_name = str(company.get("company_name", "") or "该公司")
    role_label = str(company.get("role_label", "") or "候选公司")
    if source_reason and source_reason != "pending_source_evidence":
        return f"{company_name} 当前以{role_label}身份进入跟踪池，已有公开证据可核对。"
    if llm_reason:
        return f"{company_name} 当前以{role_label}身份进入跟踪池，但公开证据仍需继续补强。"
    return f"{company_name} 当前先保留在{role_label}名单，后续需补证据再提高权重。"


def _evaluate_market_validation(
    message: dict[str, Any],
    fermentation: dict[str, Any],
    impact: dict[str, Any],
    tracked_companies: list[dict[str, Any]],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    status = str(snapshot.get("status", "unverifiable") or "unverifiable")
    company_moves = snapshot.get("company_moves", []) if isinstance(snapshot.get("company_moves"), list) else []
    basket_move = snapshot.get("basket_move", {}) if isinstance(snapshot.get("basket_move"), dict) else {}
    benchmark_move = snapshot.get("benchmark_move", {}) if isinstance(snapshot.get("benchmark_move"), dict) else {}
    basket_t0 = _safe_float(basket_move.get("T0_CLOSE")) or 0.0
    basket_t1 = _safe_float(basket_move.get("T1_CLOSE")) or 0.0
    basket_t3 = _safe_float(basket_move.get("T3_CLOSE")) or 0.0
    benchmark_t1 = _safe_float(benchmark_move.get("T1_CLOSE")) or 0.0
    excess_return = basket_t1 - benchmark_t1
    predicted_positive = impact.get("impact_direction") != "负向扰动"
    validation_status = "unverifiable"
    market_validation_score: float | None = None
    calibration_action = "keep"
    lagging_signal = False

    if status == "ok" and tracked_companies:
        if predicted_positive:
            if (basket_t0 >= 2.0 or basket_t1 >= 3.0) and excess_return >= 1.0:
                validation_status = "confirmed"
                market_validation_score = 88.0
            elif basket_t3 >= 3.0 and basket_t1 < 1.0:
                validation_status = "delayed_reaction"
                market_validation_score = 58.0
                lagging_signal = True
            elif basket_t1 <= -2.0 or excess_return <= -2.0:
                validation_status = "inverse_reaction"
                market_validation_score = 14.0
            elif max(basket_t0, basket_t1, basket_t3) < 1.0 and abs(excess_return) < 1.0:
                validation_status = "no_reaction"
                market_validation_score = 32.0
            else:
                validation_status = "partial"
                market_validation_score = 62.0
        else:
            if basket_t0 <= -2.0 or basket_t1 <= -3.0:
                validation_status = "confirmed"
                market_validation_score = 86.0
            elif min(basket_t0, basket_t1, basket_t3) > -1.0:
                validation_status = "no_reaction"
                market_validation_score = 32.0
            else:
                validation_status = "partial"
                market_validation_score = 60.0

    if validation_status == "no_reaction":
        calibration_action = "downgrade_importance"
    elif validation_status == "inverse_reaction":
        calibration_action = "suppress_from_priority_feed"
    elif validation_status == "delayed_reaction":
        calibration_action = "mark_delayed_watch"
    elif validation_status == "partial":
        calibration_action = "downgrade_theme_confidence"

    return {
        "validation_window": snapshot.get("validation_window", "T1_CLOSE"),
        "observed_company_moves": company_moves,
        "observed_basket_move": basket_move,
        "observed_benchmark_move": benchmark_move,
        "excess_return": round(excess_return, 2) if status == "ok" and tracked_companies else None,
        "validation_status": validation_status,
        "prediction_gap": _prediction_gap(validation_status, fermentation, impact),
        "lagging_signal": lagging_signal,
        "calibration_action": calibration_action,
        "calibration_reason": _calibration_reason(validation_status),
        "validation_summary": _validation_summary(validation_status, tracked_companies, basket_t1),
        "market_validation_score": market_validation_score,
    }


def _prediction_gap(validation_status: str, fermentation: dict[str, Any], impact: dict[str, Any]) -> str:
    if validation_status == "confirmed":
        return "初始判断与市场反应基本一致。"
    if validation_status == "delayed_reaction":
        return "消息的市场兑现偏滞后，短线反应不强，但后续出现了跟随性反馈。"
    if validation_status == "inverse_reaction":
        return "初始判断偏乐观，但市场给出了相反反馈。"
    if validation_status == "no_reaction":
        return "初始判断较强，但市场在主要观察窗口没有给出明显反馈。"
    if validation_status == "partial":
        return "只有部分公司兑现了预期，影响并未完全扩散。"
    if fermentation.get("fermentation_verdict") in {"high", "medium"} and impact.get("primary_theme"):
        return "暂时无法拿到价格验证数据，保留初始判断并继续观察。"
    return "当前缺少足够验证数据。"


def _calibration_reason(validation_status: str) -> str:
    mapping = {
        "confirmed": "保留当前优先级，继续跟踪后续扩散。",
        "partial": "保留消息，但下调题材置信度和公司覆盖评价。",
        "no_reaction": "下调消息重要性，避免把弱反馈消息继续推到高优先级。",
        "inverse_reaction": "强制降级，避免错误主题继续占用研究注意力。",
        "delayed_reaction": "改为滞后观察，等待后续验证窗口继续确认。",
        "unverifiable": "价格数据暂缺，保留初始判断并标记待验证。",
    }
    return mapping.get(validation_status, "维持观察。")


def _validation_summary(validation_status: str, tracked_companies: list[dict[str, Any]], basket_t1: float) -> str:
    if validation_status == "confirmed":
        return f"当前候选池已有明确反馈，T1 收盘篮子涨幅为 {basket_t1:.2f}% 。"
    if validation_status == "no_reaction":
        return "核心候选公司在主要观察窗口未给出明显正反馈，消息研究优先级已被下调。"
    if validation_status == "inverse_reaction":
        return "核心候选公司整体给出负反馈，初始判断已被强制校正。"
    if validation_status == "delayed_reaction":
        return "消息短线反应一般，但后续窗口开始出现滞后兑现。"
    if validation_status == "partial":
        return f"当前识别到 {len(tracked_companies)} 家跟踪公司，其中只有部分公司兑现预期。"
    return "当前还没有足够价格数据来完成验证。"


def _company_discovery_score(companies: list[dict[str, Any]]) -> float:
    if not companies:
        return 0.0
    base = min(100.0, len(companies) * 18.0)
    purity = [_safe_float(item.get("purity_score")) for item in companies]
    purity = [item for item in purity if item is not None]
    if purity:
        base += min(18.0, max(purity) * 0.2)
    confirmed = sum(1 for item in companies if item.get("candidate_status") == "confirmed")
    base += min(12.0, confirmed * 4.0)
    return min(100.0, base)


def _reason_quality_score(reasoning_companies: list[dict[str, Any]]) -> float:
    if not reasoning_companies:
        return 0.0
    evidence_ready = sum(1 for item in reasoning_companies if item.get("source_reason") and item.get("source_reason") != "pending_source_evidence")
    llm_ready = sum(1 for item in reasoning_companies if item.get("llm_reason"))
    evidence_items = sum(len(item.get("source_evidence_items", []) or []) for item in reasoning_companies)
    score = (evidence_ready * 20.0) + (llm_ready * 10.0) + min(20.0, evidence_items * 3.0)
    return min(100.0, score)


def _recalibrated_score(
    initial_actionability_score: float,
    market_validation_score: float | None,
    validation: dict[str, Any],
) -> float:
    if market_validation_score is None:
        return initial_actionability_score
    action = str(validation.get("calibration_action", "keep") or "keep")
    if action == "suppress_from_priority_feed":
        return round(max(0.0, (initial_actionability_score * 0.45) + (market_validation_score * 0.25)), 2)
    if action == "downgrade_importance":
        return round((initial_actionability_score * 0.55) + (market_validation_score * 0.45), 2)
    if action == "downgrade_theme_confidence":
        return round((initial_actionability_score * 0.65) + (market_validation_score * 0.35), 2)
    if action == "mark_delayed_watch":
        return round((initial_actionability_score * 0.72) + (market_validation_score * 0.28), 2)
    return round((initial_actionability_score * 0.6) + (market_validation_score * 0.4), 2)


def _score_summary(initial_score: float, final_score: float, validation: dict[str, Any]) -> str:
    status = str(validation.get("validation_status", "unverifiable") or "unverifiable")
    if status == "confirmed":
        return f"初始研究优先级为 {initial_score:.1f}，市场反馈确认后提升为 {final_score:.1f}。"
    if status == "unverifiable":
        return f"初始研究优先级为 {initial_score:.1f}，当前还没有足够市场数据完成验证。"
    return f"初始研究优先级为 {initial_score:.1f}，经市场验证校正后调整为 {final_score:.1f}。"


def _theme_validation_bucket(validation_status: str) -> str:
    if validation_status == "confirmed":
        return "验证通过题材"
    if validation_status in {"no_reaction", "inverse_reaction"}:
        return "被校正降级题材"
    return "观察中题材"


def _merge_theme_validation_bucket(current: str, incoming: str) -> str:
    order = {"验证通过题材": 3, "观察中题材": 2, "被校正降级题材": 1}
    if incoming == "被校正降级题材" and current != "验证通过题材":
        return incoming
    return incoming if order.get(incoming, 0) > order.get(current, 0) else current


def _excerpt_for_keyword(text: str, keyword: str) -> str:
    cleaned = str(text or "").replace("\n", " ").strip()
    if not cleaned or not keyword:
        return cleaned[:120]
    index = cleaned.find(keyword)
    if index < 0:
        return cleaned[:120]
    start = max(0, index - 26)
    end = min(len(cleaned), index + len(keyword) + 60)
    return cleaned[start:end]


def _normalize_score(value: Any) -> float | None:
    score = _safe_float(value)
    if score is None:
        return None
    if score <= 1.0:
        return round(score * 100.0, 2)
    return round(min(score, 100.0), 2)
