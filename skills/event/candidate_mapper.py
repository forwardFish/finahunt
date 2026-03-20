from __future__ import annotations

import json
import re
from typing import Any

from packages.llm import MultiModelRouter
from skills.event.stock_reasoning import (
    StockReasonLLMWriter,
    XueqiuEvidenceResolver,
    is_valid_candidate_stock_name,
    normalize_candidate_stock_name,
)


ACTION_KEYWORDS = ["涨停", "涨超", "连板", "触及涨停", "大涨", "走高", "新高", "活跃", "跟涨", "涨幅靠前"]
STOCK_NAME_STOPWORDS = {
    "概念",
    "题材",
    "板块",
    "财联社",
    "消息面上",
    "国家",
    "市场",
    "方向",
    "概念盘中",
    "中国",
    "方面",
    "商业航天",
    "算力租赁",
    "绿电概念",
    "创新药概念",
    "存储芯片概念",
    "热门话题",
    "雪球",
}


class ThemeCandidateLLMEnhancer:
    def __init__(
        self,
        router: MultiModelRouter,
        *,
        fallback_models: list[str] | None = None,
        max_signals_per_theme: int = 4,
        max_candidates_per_theme: int = 4,
        min_confidence: float = 0.55,
    ) -> None:
        self.router = router
        self.fallback_models = fallback_models or []
        self.max_signals_per_theme = max_signals_per_theme
        self.max_candidates_per_theme = max_candidates_per_theme
        self.min_confidence = min_confidence

    @property
    def available(self) -> bool:
        return self.router.available

    def enrich_cluster(self, cluster: dict[str, Any]) -> dict[str, Any] | None:
        if not self.available:
            return None

        known_candidates = [
            {
                "stock_name": item.get("stock_name", ""),
                "stock_code": item.get("stock_code", ""),
                "candidate_purity_score": item.get("candidate_purity_score", 0.0),
                "relation": item.get("relation", "weak"),
                "evidence": item.get("evidence", [])[:3],
            }
            for item in cluster.get("candidate_stocks", [])[:6]
        ]
        signals = [
            {
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "event_subject": item.get("event_subject", ""),
                "catalyst_type": item.get("catalyst_type", ""),
                "catalyst_strength": item.get("catalyst_strength", ""),
                "event_time": item.get("event_time", ""),
            }
            for item in cluster.get("supporting_signals", [])[: self.max_signals_per_theme]
        ]

        system_prompt = (
            "你是A股题材映射研究员。"
            "任务是根据题材、催化和证据，识别最值得持续跟踪的候选个股。"
            "只能基于提供的信息和合理金融常识，不要编造没有根据的公司。"
            "如果股票代码不确定，可以留空字符串。"
            "必须输出 JSON 对象。"
        )
        user_prompt = json.dumps(
            {
                "theme_name": cluster.get("theme_name", ""),
                "core_narrative": cluster.get("core_narrative", ""),
                "anchor_terms": cluster.get("anchor_terms", [])[:6],
                "cluster_state": cluster.get("cluster_state", "new_theme"),
                "source_count": cluster.get("source_count", 0),
                "related_events_count": cluster.get("related_events_count", 0),
                "signals": signals,
                "known_candidates": known_candidates,
                "required_output": {
                    "tracking_verdict": "keep | watch | drop",
                    "tracking_reason": "一句中文原因",
                    "candidate_stocks": [
                        {
                            "stock_name": "中文股票名",
                            "stock_code": "A股代码，无法确认可留空",
                            "mapping_level": "core_beneficiary | direct_link | supply_chain_link | peripheral_watch",
                            "purity_score": "0-100",
                            "confidence": "0-1",
                            "mapping_reason": "中文原因",
                            "llm_reason": "中文研究理由",
                            "scarcity_note": "中文稀缺性说明",
                            "risk_flags": ["中文风险标签"],
                            "should_track": True,
                        }
                    ],
                },
            },
            ensure_ascii=False,
        )
        payload = self.router.structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            fallback_models=self.fallback_models,
        )
        if not payload:
            return None
        return {
            "tracking_verdict": str(payload.get("tracking_verdict", "watch") or "watch"),
            "tracking_reason": str(payload.get("tracking_reason", "") or ""),
            "candidate_stocks": [
                item
                for item in payload.get("candidate_stocks", [])
                if isinstance(item, dict)
                and str(item.get("stock_name", "")).strip()
                and float(item.get("confidence", 0.0) or 0.0) >= self.min_confidence
            ][: self.max_candidates_per_theme],
        }


def map_theme_clusters_to_candidates(
    theme_clusters: list[dict[str, Any]],
    llm_enhancer: ThemeCandidateLLMEnhancer | None = None,
    source_reason_resolver: XueqiuEvidenceResolver | None = None,
    llm_reason_writer: StockReasonLLMWriter | None = None,
) -> list[dict[str, Any]]:
    mapped_clusters: list[dict[str, Any]] = []
    source_reason_resolver = source_reason_resolver or XueqiuEvidenceResolver()

    for cluster in theme_clusters:
        seeded_candidates = _merge_candidate_lists(
            _seed_candidates_from_linked_assets(cluster),
            _seed_candidates_from_signal_text(cluster),
        )
        heuristic_candidates = _merge_candidate_lists(cluster.get("candidate_stocks", []), seeded_candidates)
        llm_payload = llm_enhancer.enrich_cluster({**cluster, "candidate_stocks": heuristic_candidates}) if llm_enhancer else None
        enriched_candidates = _merge_llm_candidates(cluster, heuristic_candidates, llm_payload)

        mapped_candidates: list[dict[str, Any]] = []
        dropped_candidates: list[dict[str, Any]] = []

        for stock in enriched_candidates:
            stock_name = normalize_candidate_stock_name(str(stock.get("stock_name", "") or ""))
            if stock_name:
                stock = {**stock, "stock_name": stock_name}
            if stock_name and not is_valid_candidate_stock_name(stock_name):
                dropped_candidates.append(
                    {
                        "stock_code": stock.get("stock_code", ""),
                        "stock_name": stock.get("stock_name", ""),
                        "drop_reason": "invalid_candidate_name",
                    }
                )
                continue
            mapping_level = _derive_mapping_level(stock)
            if mapping_level is None:
                dropped_candidates.append(
                    {
                        "stock_code": stock.get("stock_code", ""),
                        "stock_name": stock.get("stock_name", ""),
                        "drop_reason": stock.get("drop_reason", "insufficient_mapping_evidence"),
                    }
                )
                continue

            source_payload = source_reason_resolver.resolve(
                cluster,
                str(stock.get("stock_name", "") or stock.get("stock_code", "") or ""),
                str(stock.get("stock_code", "") or ""),
            )
            llm_reason = ""
            should_write_llm_reason = (
                llm_reason_writer is not None
                and mapping_level in {"core_beneficiary", "direct_link"}
                and bool(source_payload.reason)
            )
            if should_write_llm_reason:
                llm_reason = llm_reason_writer.build_reason(cluster, stock, source_payload)
            if not llm_reason:
                llm_reason = str(stock.get("llm_reason", "") or "").strip()

            mapped = {
                **stock,
                "mapping_level": mapping_level,
                "mapping_reason": stock.get("mapping_reason") or _build_mapping_reason(cluster, stock, mapping_level),
                "source_reason": stock.get("source_reason") or source_payload.reason or _build_source_reason(cluster, stock, mapping_level),
                "source_reason_source_site": stock.get("source_reason_source_site") or source_payload.source_site or _detect_reason_source_site(cluster, stock),
                "source_reason_source_url": stock.get("source_reason_source_url") or source_payload.source_url or _detect_reason_source_url(cluster, stock),
                "source_reason_title": stock.get("source_reason_title") or source_payload.source_title or _detect_reason_title(cluster, stock),
                "source_reason_excerpt": stock.get("source_reason_excerpt") or source_payload.source_excerpt or _detect_reason_excerpt(cluster, stock),
                "llm_reason": llm_reason,
                "mapping_confidence": _derive_mapping_confidence(stock, mapping_level),
                "evidence_source_count": len(stock.get("source_refs", [])),
            }
            mapped_candidates.append(mapped)

        core_candidates = [item for item in mapped_candidates if item["mapping_level"] == "core_beneficiary"]
        direct_candidates = [item for item in mapped_candidates if item["mapping_level"] == "direct_link"]
        supply_chain_candidates = [item for item in mapped_candidates if item["mapping_level"] == "supply_chain_link"]
        peripheral_candidates = [item for item in mapped_candidates if item["mapping_level"] == "peripheral_watch"]

        prioritized_candidates = core_candidates + direct_candidates + supply_chain_candidates + peripheral_candidates
        tracking_verdict = _resolve_tracking_verdict(cluster, llm_payload, prioritized_candidates)
        tracking_reason = _resolve_tracking_reason(cluster, llm_payload, prioritized_candidates, tracking_verdict)

        mapped_clusters.append(
            {
                **cluster,
                "candidate_stocks": prioritized_candidates,
                "candidate_pool": prioritized_candidates,
                "core_candidates": core_candidates,
                "direct_candidates": direct_candidates,
                "supply_chain_candidates": supply_chain_candidates,
                "peripheral_candidates": peripheral_candidates,
                "dropped_candidates": dropped_candidates,
                "tracking_verdict": tracking_verdict,
                "tracking_reason": tracking_reason,
                "llm_mapping_used": bool(llm_payload),
                "llm_tracking_payload": llm_payload or {},
                "mapping_summary": {
                    "candidate_count": len(prioritized_candidates),
                    "core_count": len(core_candidates),
                    "direct_count": len(direct_candidates),
                    "supply_chain_count": len(supply_chain_candidates),
                    "peripheral_count": len(peripheral_candidates),
                    "dropped_count": len(dropped_candidates),
                    "tracking_verdict": tracking_verdict,
                },
            }
        )

    return sorted(
        mapped_clusters,
        key=lambda item: (
            item.get("tracking_verdict") == "keep",
            item.get("mapping_summary", {}).get("core_count", 0),
            item.get("mapping_summary", {}).get("direct_count", 0),
            item.get("related_events_count", 0),
            item.get("source_count", 0),
        ),
        reverse=True,
    )


def _seed_candidates_from_linked_assets(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    seeded: list[dict[str, Any]] = []
    theme_name = str(cluster.get("theme_name", "") or "")
    anchor_terms = [str(item) for item in cluster.get("anchor_terms", [])[:4]]

    for asset in cluster.get("linked_assets", []):
        if asset.get("asset_type") != "stock":
            continue
        stock_name = str(asset.get("asset_name", "") or "").strip()
        stock_code = str(asset.get("asset_id", "") or "").strip()
        if not stock_name and not stock_code:
            continue
        seeded.append(
            {
                "stock_code": stock_code,
                "stock_name": stock_name or stock_code,
                "candidate_purity_score": 62.0,
                "relation": "direct" if stock_name and stock_name in theme_name else "weak",
                "purity_breakdown": {},
                "mention_count": 1,
                "direct_signal_count": 1 if stock_name and stock_name in " ".join(anchor_terms) else 0,
                "evidence": anchor_terms[:2] or [theme_name],
                "risk_flags": [],
                "source_refs": list(cluster.get("source_refs", [])),
                "evidence_event_ids": [],
            }
        )
    return seeded


def _seed_candidates_from_signal_text(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    seeded: list[dict[str, Any]] = []
    evidence_fallback = [str(item) for item in cluster.get("anchor_terms", [])[:2]] or [str(cluster.get("theme_name", ""))]
    seen: set[str] = set()

    for signal in cluster.get("supporting_signals", [])[:6]:
        text = " ".join(
            part
            for part in [
                str(signal.get("title", "") or ""),
                str(signal.get("summary", "") or ""),
                str(signal.get("event_subject", "") or ""),
            ]
            if part
        )
        for name in _extract_stock_like_names(text):
            normalized_name = normalize_candidate_stock_name(name)
            if not is_valid_candidate_stock_name(normalized_name):
                continue
            key = normalized_name.lower()
            if key in seen:
                continue
            seen.add(key)
            seeded.append(
                {
                    "stock_code": "",
                    "stock_name": normalized_name,
                    "candidate_purity_score": 60.0,
                    "relation": "direct" if normalized_name in str(signal.get("title", "")) else "weak",
                    "purity_breakdown": {},
                    "mention_count": 1,
                    "direct_signal_count": 1 if normalized_name in str(signal.get("title", "")) else 0,
                    "evidence": [*evidence_fallback, f"{name}在题材相关资讯中被直接提及"][:4],
                    "risk_flags": [],
                    "source_refs": list(dict.fromkeys(signal.get("source_refs", []) or cluster.get("source_refs", []))),
                    "evidence_event_ids": [str(signal.get("event_id", "") or "")] if signal.get("event_id") else [],
                }
            )
    return seeded


def _merge_candidate_lists(
    existing_candidates: list[dict[str, Any]],
    supplemental_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in [*existing_candidates, *supplemental_candidates]:
        key = _candidate_key(item.get("stock_code", ""), item.get("stock_name", ""))
        current = merged.get(key)
        if current is None:
            merged[key] = {
                **item,
                "risk_flags": list(dict.fromkeys(item.get("risk_flags", []))),
                "evidence": list(dict.fromkeys(item.get("evidence", []))),
                "source_refs": list(dict.fromkeys(item.get("source_refs", []))),
            }
            continue
        current["candidate_purity_score"] = max(
            float(current.get("candidate_purity_score", 0.0) or 0.0),
            float(item.get("candidate_purity_score", 0.0) or 0.0),
        )
        current["direct_signal_count"] = max(
            int(current.get("direct_signal_count", 0) or 0),
            int(item.get("direct_signal_count", 0) or 0),
        )
        current["mention_count"] = max(int(current.get("mention_count", 0) or 0), int(item.get("mention_count", 0) or 0))
        current["relation"] = _prefer_relation(str(current.get("relation", "weak")), str(item.get("relation", "weak")))
        current["risk_flags"] = list(dict.fromkeys([*current.get("risk_flags", []), *item.get("risk_flags", [])]))
        current["evidence"] = list(dict.fromkeys([*current.get("evidence", []), *item.get("evidence", [])]))
        current["source_refs"] = list(dict.fromkeys([*current.get("source_refs", []), *item.get("source_refs", [])]))
    return list(merged.values())


def _merge_llm_candidates(
    cluster: dict[str, Any],
    candidates: list[dict[str, Any]],
    llm_payload: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    merged = _merge_candidate_lists(candidates, [])
    if not llm_payload:
        return merged

    enriched: dict[str, dict[str, Any]] = {
        _candidate_key(item.get("stock_code", ""), item.get("stock_name", "")): {**item} for item in merged
    }

    for item in llm_payload.get("candidate_stocks", []):
        stock_name = normalize_candidate_stock_name(str(item.get("stock_name", "") or "").strip())
        if stock_name and not is_valid_candidate_stock_name(stock_name):
            continue
        stock_code = _normalize_stock_code(str(item.get("stock_code", "") or "").strip())
        key = _candidate_key(stock_code, stock_name)
        if key not in enriched and stock_name:
            for existing_key, existing_value in enriched.items():
                if str(existing_value.get("stock_name", "") or "").strip() == stock_name:
                    key = existing_key
                    break
        relation = "direct" if item.get("mapping_level") in {"core_beneficiary", "direct_link"} else "weak"
        scarcity_note = str(item.get("scarcity_note", "") or "").strip()
        mapping_reason = str(item.get("mapping_reason", "") or "").strip()
        llm_reason = str(item.get("llm_reason", "") or mapping_reason).strip()
        llm_score = float(item.get("purity_score", 0.0) or 0.0)
        confidence = float(item.get("confidence", 0.0) or 0.0)
        risk_flags = [str(flag).strip() for flag in item.get("risk_flags", []) if str(flag).strip()]

        existing = enriched.get(key, {})
        evidence = list(
            dict.fromkeys(
                [
                    *existing.get("evidence", []),
                    *(cluster.get("anchor_terms", [])[:2] or [cluster.get("theme_name", "")]),
                    mapping_reason,
                    scarcity_note,
                ]
            )
        )
        enriched[key] = {
            **existing,
            "stock_code": stock_code or existing.get("stock_code", "") or "",
            "stock_name": stock_name or existing.get("stock_name", ""),
            "candidate_purity_score": max(float(existing.get("candidate_purity_score", 0.0) or 0.0), llm_score),
            "relation": _prefer_relation(str(existing.get("relation", "weak")), relation),
            "mention_count": max(int(existing.get("mention_count", 0) or 0), 1),
            "direct_signal_count": max(
                int(existing.get("direct_signal_count", 0) or 0),
                1 if relation == "direct" else 0,
            ),
            "evidence": evidence[:6],
            "risk_flags": list(dict.fromkeys([*existing.get("risk_flags", []), *risk_flags])),
            "source_refs": list(dict.fromkeys([*existing.get("source_refs", []), *cluster.get("source_refs", [])])),
            "llm_mapping_level": str(item.get("mapping_level", "") or ""),
            "mapping_reason": mapping_reason,
            "llm_reason": llm_reason,
            "scarcity_note": scarcity_note,
            "llm_confidence": round(confidence * 100, 2),
            "llm_should_track": bool(item.get("should_track", True)),
        }
    return list(enriched.values())


def _candidate_key(stock_code: str, stock_name: str) -> str:
    normalized_code = str(stock_code or "").strip().upper()
    if normalized_code:
        return normalized_code
    return normalize_candidate_stock_name(str(stock_name or "").strip()).lower()


def _normalize_stock_code(value: str) -> str:
    raw = str(value or "").strip().upper()
    if not raw:
        return ""
    if raw.startswith(("SH", "SZ")) and len(raw) == 8:
        return f"{raw[2:]}.{raw[:2]}"
    if "." in raw:
        return raw
    if raw.isdigit() and len(raw) == 6:
        suffix = "SH" if raw.startswith(("6", "9")) else "SZ"
        return f"{raw}.{suffix}"
    return raw


def _extract_stock_like_names(text: str) -> list[str]:
    names: list[str] = []
    cleaned = re.sub(r"[#【】\(\)（）]", " ", text)
    segments = re.split(r"[，。；：]", cleaned)
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        for keyword in ACTION_KEYWORDS:
            if keyword not in segment:
                continue
            head = segment.split(keyword, 1)[0].strip()
            for token in re.split(r"[、/\s]", head):
                candidate = token.strip(" -")
                candidate = re.sub(r"(?:20CM|10CM)?涨停|涨超\d+%?|连板|触及涨停|大涨|走高|新高|活跃|跟涨|涨幅靠前", "", candidate, flags=re.IGNORECASE)
                candidate = re.sub(r"(?:回封|续创历史新高|创历史新高|续创历史|创新高|涨幅靠前|等)$", "", candidate)
                candidate = candidate.strip(" -")
                if _looks_like_stock_name(candidate):
                    names.append(candidate)
    return list(dict.fromkeys(names))[:6]


def _looks_like_stock_name(value: str) -> bool:
    candidate = normalize_candidate_stock_name(str(value or "").strip())
    if candidate in STOCK_NAME_STOPWORDS:
        return False
    return is_valid_candidate_stock_name(candidate)


def _prefer_relation(left: str, right: str) -> str:
    ranking = {"direct": 3, "weak": 2, "indirect": 1}
    return left if ranking.get(left, 0) >= ranking.get(right, 0) else right


def _derive_mapping_level(stock: dict[str, Any]) -> str | None:
    llm_level = str(stock.get("llm_mapping_level", "") or "").strip()
    if llm_level in {"core_beneficiary", "direct_link", "supply_chain_link", "peripheral_watch"}:
        return llm_level

    purity = float(stock.get("candidate_purity_score", 0.0) or 0.0)
    relation = stock.get("relation", "weak")
    direct_signal_count = int(stock.get("direct_signal_count", 0) or 0)
    evidence_count = len(stock.get("evidence", []))

    if relation == "direct" and (purity >= 70 or direct_signal_count >= 1):
        return "core_beneficiary"
    if relation == "direct" and evidence_count >= 1:
        return "direct_link"
    if purity >= 64 and evidence_count >= 2:
        return "supply_chain_link"
    if purity >= 58 and evidence_count >= 1:
        return "peripheral_watch"
    return None


def _derive_mapping_confidence(stock: dict[str, Any], mapping_level: str) -> float:
    purity = float(stock.get("candidate_purity_score", 0.0) or 0.0)
    source_count = len(stock.get("source_refs", []))
    evidence_count = len(stock.get("evidence", []))
    level_bonus = {
        "core_beneficiary": 10.0,
        "direct_link": 6.0,
        "supply_chain_link": 2.0,
        "peripheral_watch": -2.0,
    }[mapping_level]
    llm_confidence = float(stock.get("llm_confidence", 0.0) or 0.0)
    return round(min(100.0, max(purity + source_count * 3 + evidence_count * 2 + level_bonus, llm_confidence)), 2)


def _build_mapping_reason(theme_name: str, stock: dict[str, Any], mapping_level: str) -> str:
    evidence = " / ".join(stock.get("evidence", [])[:2]) or theme_name
    mapping_label = {
        "core_beneficiary": "核心受益标的",
        "direct_link": "直接映射标的",
        "supply_chain_link": "产业链映射标的",
        "peripheral_watch": "边缘观察标的",
    }[mapping_level]
    return f"{stock.get('stock_name', stock.get('stock_code', '候选标的'))}被判定为{theme_name}的{mapping_label}，主要依据为{evidence}。"


def _build_mapping_reason(cluster: dict[str, Any], stock: dict[str, Any], mapping_level: str) -> str:
    theme_name = str(cluster.get("theme_name", "") or "该题材")
    stock_name = str(stock.get("stock_name", "") or stock.get("stock_code", "") or "候选标的")
    mapping_label = {
        "core_beneficiary": "核心跟踪候选",
        "direct_link": "直接映射候选",
        "supply_chain_link": "产业链映射候选",
        "peripheral_watch": "边缘观察候选",
    }[mapping_level]
    best_signal = _select_best_signal_for_stock(cluster, stock_name)
    evidence = _clean_reason_fragment(" / ".join(str(item) for item in stock.get("evidence", [])[:2] if str(item).strip()))

    if best_signal:
        title = _clean_signal_title(str(best_signal.get("title", "") or ""))
        summary = _clean_reason_fragment(str(best_signal.get("summary", "") or ""))
        if title and stock_name and stock_name in title:
            return f"{stock_name}在《{title}》这条{theme_name}线索中被直接点名，当前归入{mapping_label}。"
        if summary and stock_name and stock_name in summary:
            return f"{stock_name}在{theme_name}相关异动描述中被直接提及，当前归入{mapping_label}。"
        if title:
            return f"{stock_name}与《{title}》这条{theme_name}线索存在联动，当前归入{mapping_label}。"

    if evidence:
        return f"{stock_name}被纳入{theme_name}的{mapping_label}，当前主要依据是：{evidence}。"
    return f"{stock_name}已进入{theme_name}的{mapping_label}，后续需继续观察催化是否扩散。"

def _clean_signal_title(value: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    cleaned = cleaned.split(" - ", 1)[0].strip()
    cleaned = re.sub(r"^#+", "", cleaned).strip()
    return cleaned


def _clean_reason_fragment(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = cleaned.replace(" / ", "、")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip("，,。.;； ")


def _build_source_reason(cluster: dict[str, Any], stock: dict[str, Any], mapping_level: str) -> str:
    theme_name = str(cluster.get("theme_name", "") or "该题材")
    stock_name = str(stock.get("stock_name", "") or stock.get("stock_code", "") or "候选标的")
    signal = _select_best_signal_for_stock(cluster, stock_name, preferred_domain="xueqiu.com")
    label = {
        "core_beneficiary": "核心跟踪候选",
        "direct_link": "直接映射候选",
        "supply_chain_link": "产业链映射候选",
        "peripheral_watch": "边缘观察候选",
    }[mapping_level]
    if signal:
        title = _clean_signal_title(str(signal.get("title", "") or ""))
        summary = _clean_reason_fragment(_extract_reason_excerpt(str(signal.get("summary", "") or ""), stock_name))
        if title and stock_name and stock_name in title:
            return f"雪球线索显示，{stock_name}在《{title}》中被直接点名，当前归入{theme_name}的{label}。"
        if summary:
            return f"雪球线索显示，{stock_name}在{theme_name}相关讨论中被提及：{summary}。"
        if title:
            return f"雪球线索显示，{stock_name}与《{title}》这条{theme_name}主线存在联动，当前归入{label}。"
    return _build_mapping_reason(cluster, stock, mapping_level)


def _detect_reason_source_site(cluster: dict[str, Any], stock: dict[str, Any]) -> str:
    signal = _select_best_signal_for_stock(cluster, str(stock.get("stock_name", "") or stock.get("stock_code", "") or ""), preferred_domain="xueqiu.com")
    if not signal:
        return ""
    for url in signal.get("source_refs", []) or []:
        if "xueqiu.com" in str(url):
            return "雪球"
    return _domain_label(next(iter(signal.get("source_refs", []) or []), ""))


def _detect_reason_source_url(cluster: dict[str, Any], stock: dict[str, Any]) -> str:
    signal = _select_best_signal_for_stock(cluster, str(stock.get("stock_name", "") or stock.get("stock_code", "") or ""), preferred_domain="xueqiu.com")
    if not signal:
        return ""
    refs = [str(item) for item in signal.get("source_refs", []) if str(item).strip()]
    for url in refs:
        if "xueqiu.com" in url:
            return url
    return refs[0] if refs else ""


def _detect_reason_title(cluster: dict[str, Any], stock: dict[str, Any]) -> str:
    signal = _select_best_signal_for_stock(cluster, str(stock.get("stock_name", "") or stock.get("stock_code", "") or ""), preferred_domain="xueqiu.com")
    return _clean_signal_title(str(signal.get("title", "") or "")) if signal else ""


def _detect_reason_excerpt(cluster: dict[str, Any], stock: dict[str, Any]) -> str:
    stock_name = str(stock.get("stock_name", "") or stock.get("stock_code", "") or "")
    signal = _select_best_signal_for_stock(cluster, stock_name, preferred_domain="xueqiu.com")
    return _extract_reason_excerpt(str(signal.get("summary", "") or ""), stock_name) if signal else ""


def _select_best_signal_for_stock(
    cluster: dict[str, Any],
    stock_name: str,
    *,
    preferred_domain: str | None = None,
) -> dict[str, Any] | None:
    fallback: dict[str, Any] | None = None
    preferred: dict[str, Any] | None = None
    for signal in cluster.get("supporting_signals", []):
        title = str(signal.get("title", "") or "")
        summary = str(signal.get("summary", "") or "")
        refs = [str(item) for item in signal.get("source_refs", []) if str(item).strip()]
        matches_stock = bool(stock_name and (stock_name in title or stock_name in summary))
        matches_domain = bool(preferred_domain and any(preferred_domain in ref for ref in refs))
        if matches_stock and matches_domain:
            return signal
        if matches_stock and preferred is None:
            preferred = signal
        if fallback is None:
            fallback = signal
    return preferred or fallback


def _extract_reason_excerpt(summary: str, stock_name: str) -> str:
    cleaned = _clean_reason_fragment(summary)
    if not cleaned:
        return ""
    if not stock_name or stock_name not in cleaned:
        return cleaned[:70]
    sentences = re.split(r"[；。!?]", cleaned)
    for sentence in sentences:
        sentence = sentence.strip()
        if stock_name in sentence:
            return sentence[:70]
    return cleaned[:70]


def _domain_label(url: str) -> str:
    raw = str(url or "")
    if "xueqiu.com" in raw:
        return "雪球"
    if "cls.cn" in raw:
        return "财联社"
    if "jiuyangongshe.com" in raw:
        return "韭研公社"
    return "公开来源"


def _resolve_tracking_verdict(
    cluster: dict[str, Any],
    llm_payload: dict[str, Any] | None,
    prioritized_candidates: list[dict[str, Any]],
) -> str:
    llm_verdict = str((llm_payload or {}).get("tracking_verdict", "") or "").strip()
    if llm_verdict in {"keep", "watch", "drop"}:
        if llm_verdict == "drop" and prioritized_candidates:
            return "watch"
        return llm_verdict
    if prioritized_candidates:
        return "keep"
    if cluster.get("cluster_noise_level") == "high":
        return "drop"
    return "watch"


def _resolve_tracking_reason(
    cluster: dict[str, Any],
    llm_payload: dict[str, Any] | None,
    prioritized_candidates: list[dict[str, Any]],
    tracking_verdict: str,
) -> str:
    if llm_payload and llm_payload.get("tracking_reason") and tracking_verdict == str(llm_payload.get("tracking_verdict", tracking_verdict)):
        return str(llm_payload["tracking_reason"])
    if tracking_verdict == "drop":
        return "当前题材证据稀薄且噪音偏高，建议暂时过滤。"
    if prioritized_candidates:
        return "当前题材已经找到可跟踪的候选个股，建议继续观察催化兑现与扩散路径。"
    if cluster.get("cluster_noise_level") == "high":
        return "当前题材证据偏弱且噪音较高，建议先观察，不进入重点跟踪。"
    return "当前题材仍需继续补充候选个股与更强证据。"
