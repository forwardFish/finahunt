from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any


EVENT_TYPE_RULES = {
    "政策催化": ["政策", "征求意见", "发改委", "证监会", "工信部", "国务院", "印发", "试点", "规划"],
    "公告催化": ["公告", "披露", "公告称", "提示性公告", "停复牌"],
    "订单催化": ["中标", "订单", "签约", "合作", "拿单", "项目落地", "量产"],
    "产品/技术突破": ["发布", "新品", "技术突破", "首创", "量产", "迭代", "商用", "验证"],
    "价格上涨链": ["涨价", "提价", "价格上涨", "现货紧张", "供需偏紧", "景气回升"],
    "国产替代": ["国产替代", "自主可控", "进口替代", "本土供应", "去美化"],
    "重组/资本运作": ["重组", "并购", "增持", "回购", "减持", "募资", "股权激励"],
    "业绩预期变化": ["业绩", "预增", "净利润", "扭亏", "超预期", "预告"],
    "行业景气拐点": ["景气", "拐点", "复苏", "供需改善", "需求回暖", "渗透率提升"],
    "老题材重新激活": ["再度活跃", "重新发酵", "重估", "再提", "旧逻辑", "二波"],
}

THEME_TO_INDUSTRY = {
    "算力": "算力基础设施",
    "人工智能": "人工智能",
    "机器人": "高端装备",
    "低空经济": "低空经济",
    "新能源": "新能源",
    "半导体": "半导体",
    "军工": "军工",
    "医药": "医药",
}

INDUSTRY_RULES = {
    "半导体": ["芯片", "半导体", "晶圆", "封测", "存储", "DRAM"],
    "低空经济": ["低空", "eVTOL", "无人机", "通航", "低空物流"],
    "新能源": ["光伏", "储能", "风电", "锂电", "充电桩"],
    "机器人": ["机器人", "人形机器人", "伺服", "减速器", "机器视觉"],
    "算力基础设施": ["算力", "服务器", "AIDC", "GPU", "液冷", "数据中心"],
}

PRODUCT_TERMS = [
    "服务器",
    "芯片",
    "无人机",
    "eVTOL",
    "电池",
    "储能",
    "液冷",
    "机器人",
    "减速器",
    "传感器",
]

TECH_TERMS = [
    "AIDC",
    "GPU",
    "DRAM",
    "HBM",
    "大模型",
    "机器视觉",
    "自动驾驶",
    "国产替代",
    "低空物流",
]

POLICY_TERMS = [
    "试点",
    "征求意见",
    "规划",
    "专项行动",
    "指导意见",
    "行动方案",
    "白名单",
    "补贴",
]

POSITIVE_WORDS = [
    "增长",
    "提升",
    "突破",
    "落地",
    "放量",
    "签约",
    "景气",
    "修复",
    "受益",
    "涨价",
]

NEGATIVE_WORDS = [
    "减持",
    "亏损",
    "下滑",
    "风险",
    "问询",
    "诉讼",
    "停产",
    "退市",
]

PURITY_KEYWORDS = {
    "uniqueness": ["唯一", "首创", "独家", "龙头", "核心", "卡位", "稀缺"],
    "elasticity": ["放量", "订单", "量产", "提价", "扩产", "业绩弹性", "渗透率"],
    "market_cap_fit": ["小盘", "中盘", "弹性", "千亿市值", "大市值"],
    "memory": ["辨识度", "龙头", "活跃", "反复活跃", "历史股性", "弹性"],
    "financial_risk": ["ST", "*ST", "退市", "减持", "审计", "问询", "诉讼", "亏损"],
}


def detect_event_type(text: str) -> str:
    for event_type, keywords in EVENT_TYPE_RULES.items():
        if any(keyword in text for keyword in keywords):
            return event_type
    return "信息更新"


def detect_themes(text: str, theme_rules: dict[str, list[str]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for theme_name, keywords in theme_rules.items():
        hit_keywords = [keyword for keyword in keywords if keyword in text]
        if hit_keywords:
            matches.append({"theme": theme_name, "evidence": hit_keywords[:3]})
    return matches


def classify_catalyst(text: str, catalyst_rules: dict[str, Any], source_name: str) -> dict[str, str]:
    for catalyst_type, payload in catalyst_rules.items():
        keywords = payload.get("keywords", [])
        if any(keyword in text for keyword in keywords):
            strength_keywords = payload.get("strength_keywords", {})
            if any(keyword in text for keyword in strength_keywords.get("high", [])):
                strength = "high"
            elif any(keyword in text for keyword in strength_keywords.get("medium", [])):
                strength = "medium"
            else:
                strength = "low"
            return {
                "type": catalyst_type,
                "strength": strength,
                "reason": f"{source_name} hit {catalyst_type} rule",
            }
    return {
        "type": "unknown",
        "strength": "unknown",
        "reason": "no catalyst rule hit",
    }


def extract_symbol_candidates(text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    linked_assets: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in metadata.get("stock_list", []) or []:
        code = _normalize_stock_code(item.get("secu_code") or item.get("code") or item.get("symbol"))
        name = item.get("secu_name") or item.get("name") or code
        if code and code not in seen:
            seen.add(code)
            linked_assets.append({"asset_type": "stock", "asset_id": code, "asset_name": name, "relation": "direct"})

    for item in metadata.get("stocks", []) or []:
        code = _normalize_stock_code(item.get("code") or item.get("symbol"))
        name = item.get("name") or code
        if code and code not in seen:
            seen.add(code)
            linked_assets.append({"asset_type": "stock", "asset_id": code, "asset_name": name, "relation": "direct"})

    for item in metadata.get("plate_list", []) or []:
        name = item.get("plate_name") or item.get("name")
        if name and name not in seen:
            seen.add(name)
            linked_assets.append({"asset_type": "sector", "asset_id": name, "asset_name": name, "relation": "direct"})

    for code in re.findall(r"\b\d{6}\.(?:SH|SZ)\b", text):
        if code not in seen:
            seen.add(code)
            linked_assets.append({"asset_type": "stock", "asset_id": code, "asset_name": code, "relation": "weak"})

    for code in re.findall(r"\b(?:SH|SZ)\d{6}\b", text):
        normalized_code = _normalize_stock_code(code)
        if normalized_code and normalized_code not in seen:
            seen.add(normalized_code)
            linked_assets.append(
                {"asset_type": "stock", "asset_id": normalized_code, "asset_name": normalized_code, "relation": "weak"}
            )

    return linked_assets


def extract_event_profile(
    title: str,
    summary: str,
    content_text: str,
    metadata: dict[str, Any],
    published_at: str,
    theme_rules: dict[str, list[str]],
) -> dict[str, Any]:
    merged_text = " ".join(part for part in [title, summary, content_text] if part).strip()
    theme_matches = detect_themes(merged_text, theme_rules)
    related_themes = _merge_unique(metadata.get("theme_hints", []), [match["theme"] for match in theme_matches])
    related_industries = _detect_industries(merged_text, related_themes)
    involved_products = _extract_terms(merged_text, PRODUCT_TERMS)
    involved_technologies = _extract_terms(merged_text, TECH_TERMS)
    involved_policies = _extract_terms(merged_text, POLICY_TERMS)
    event_subject = _detect_event_subject(title, merged_text, metadata, related_themes)
    occurred_at = _extract_embedded_datetime(merged_text) or published_at
    impact_direction = _detect_impact_direction(merged_text)
    impact_scope = _detect_impact_scope(merged_text, metadata, related_themes)
    narrative_terms = _build_narrative_terms(
        related_themes,
        related_industries,
        involved_products,
        involved_technologies,
        involved_policies,
    )

    return {
        "event_subject": event_subject,
        "event_type": detect_event_type(merged_text),
        "occurred_at": occurred_at,
        "first_disclosed_at": published_at,
        "related_themes": related_themes,
        "related_industries": related_industries,
        "involved_products": involved_products,
        "involved_technologies": involved_technologies,
        "involved_policies": involved_policies,
        "impact_direction": impact_direction,
        "impact_scope": impact_scope,
        "narrative_terms": narrative_terms,
    }


def build_candidate_stock_links(event: dict[str, Any]) -> list[dict[str, Any]]:
    text = _compose_event_text(event)
    theme_names = event.get("theme_tags") or event.get("related_themes") or []
    stock_assets = [item for item in event.get("linked_assets", []) if item.get("asset_type") == "stock"]
    links: list[dict[str, Any]] = []

    for asset in stock_assets:
        for theme_name in theme_names or ["未归类题材"]:
            breakdown, evidence, risk_flags = _score_purity_dimensions(asset, event, text, theme_name)
            purity_score = round(
                breakdown["theme_purity"] * 0.30
                + breakdown["uniqueness"] * 0.16
                + breakdown["business_elasticity"] * 0.18
                + breakdown["market_cap_fit"] * 0.10
                + breakdown["financial_health"] * 0.14
                + breakdown["theme_memory"] * 0.12,
                2,
            )
            links.append(
                {
                    "theme_name": theme_name,
                    "stock_code": asset.get("asset_id", ""),
                    "stock_name": asset.get("asset_name", "") or asset.get("asset_id", ""),
                    "relation": asset.get("relation", "weak"),
                    "candidate_purity_score": purity_score,
                    "purity_breakdown": breakdown,
                    "evidence": evidence,
                    "risk_flags": risk_flags,
                    "source_refs": list(event.get("source_refs", [])),
                    "event_id": event.get("event_id", ""),
                }
            )
    return links


def unify_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    list_fields = [
        "source_refs",
        "evidence_refs",
        "theme_tags",
        "related_themes",
        "related_industries",
        "involved_products",
        "involved_technologies",
        "involved_policies",
    ]

    for event in events:
        event_date = (event.get("occurred_at") or event.get("event_time", ""))[:10]
        theme_anchor = ",".join(sorted((event.get("related_themes") or event.get("theme_tags") or [])[:2]))
        subject_anchor = event.get("event_subject", "")[:24]
        fingerprint = f"{event.get('event_type','')}|{subject_anchor}|{theme_anchor}|{event_date}"
        canonical_key = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]
        if canonical_key not in grouped:
            grouped[canonical_key] = {
                **event,
                "canonical_key": canonical_key,
                "source_refs": list(event.get("source_refs", [])),
                "evidence_refs": list(event.get("evidence_refs", [])),
                "linked_assets": list(event.get("linked_assets", [])),
            }
            continue

        current = grouped[canonical_key]
        for field in list_fields:
            current[field] = _merge_unique(current.get(field, []), event.get(field, []))
        current["linked_assets"] = _merge_assets(current["linked_assets"], event.get("linked_assets", []))
        current["metadata"] = {
            **current.get("metadata", {}),
            **event.get("metadata", {}),
            "merged_count": current.get("metadata", {}).get("merged_count", 1) + 1,
        }
        current["status"] = "VERIFIED" if len(current["source_refs"]) > 1 else current.get("status", "NEW")
        current["event_time"] = _pick_latest(current.get("event_time", ""), event.get("event_time", ""))
        current["occurred_at"] = _pick_earliest(current.get("occurred_at", ""), event.get("occurred_at", ""))
        current["first_disclosed_at"] = _pick_earliest(
            current.get("first_disclosed_at", ""),
            event.get("first_disclosed_at", ""),
        )
        current["impact_direction"] = _merge_impact_direction(
            current.get("impact_direction", "neutral"),
            event.get("impact_direction", "neutral"),
        )
        current["impact_scope"] = _merge_impact_scope(current.get("impact_scope", "unknown"), event.get("impact_scope", "unknown"))
        if not current.get("event_subject"):
            current["event_subject"] = event.get("event_subject", "")
    return list(grouped.values())


def rank_events_for_user(events: list[dict[str, Any]], user_profile: dict[str, Any]) -> list[dict[str, Any]]:
    watchlist_symbols = set(user_profile.get("watchlist_symbols", []))
    watchlist_themes = set(user_profile.get("watchlist_themes", []))
    ranked: list[dict[str, Any]] = []

    for event in events:
        score = 50.0
        reasons: list[str] = []
        if event.get("catalyst_strength") == "high":
            score += 25
            reasons.append("high strength catalyst")
        elif event.get("catalyst_strength") == "medium":
            score += 15
            reasons.append("medium strength catalyst")
        elif event.get("catalyst_strength") == "low":
            score += 5
            reasons.append("weak catalyst")
        else:
            score -= 10

        source_count = len(event.get("source_refs", []))
        score += min(source_count * 5, 15)
        if source_count > 1:
            reasons.append("cross-source confirmation")

        linked_ids = {item.get("asset_id") for item in event.get("linked_assets", [])}
        if watchlist_symbols & linked_ids:
            score += 20
            reasons.append("watchlist symbol hit")

        theme_tags = set(event.get("theme_tags", []) or event.get("related_themes", []))
        if watchlist_themes & theme_tags:
            score += 10
            reasons.append("watchlist theme hit")
        elif theme_tags:
            score += 4
            reasons.append("has theme clue")
        else:
            score -= 5

        if event.get("linked_assets"):
            score += 6
            reasons.append("has asset linkage")
        else:
            score -= 5

        if event.get("impact_scope") == "sector":
            score += 6
            reasons.append("sector-level impact")
        elif event.get("impact_scope") == "stock":
            score += 3

        freshness_bonus = _freshness_bonus(event.get("event_time", ""))
        score += freshness_bonus
        if freshness_bonus > 0:
            reasons.append("fresh evidence")

        ranked.append(
            {
                **event,
                "relevance_score": round(score, 2),
                "relevance_reason": "; ".join(reasons) or "default ranking",
            }
        )

    return sorted(ranked, key=lambda item: item.get("relevance_score", 0.0), reverse=True)


def build_daily_review(ranked_events: list[dict[str, Any]]) -> dict[str, Any]:
    prioritized = [
        item
        for item in ranked_events
        if item.get("catalyst_type") != "unknown" or item.get("theme_tags") or item.get("linked_assets")
    ]
    top_events = (prioritized or ranked_events)[:5]
    focus_cards = [
        {
            "event_id": item["event_id"],
            "title": item["title"],
            "event_subject": item.get("event_subject", ""),
            "themes": item.get("theme_tags", []),
            "related_industries": item.get("related_industries", []),
            "catalyst_type": item.get("catalyst_type", ""),
            "catalyst_strength": item.get("catalyst_strength", ""),
            "relevance_score": item.get("relevance_score", 0.0),
            "source_refs": item.get("source_refs", []),
            "risk_notice": "For research only. Not investment advice.",
        }
        for item in top_events
    ]

    return {
        "today_focus_page": focus_cards,
        "watchlist_event_page": [
            {
                "event_id": item["event_id"],
                "title": item["title"],
                "linked_assets": item.get("linked_assets", []),
                "relevance_reason": item.get("relevance_reason", ""),
            }
            for item in ranked_events[:10]
        ],
        "daily_review_report": {
            "generated_at": datetime.now(UTC).isoformat(),
            "highlight_count": len(top_events),
            "summary": [item["title"] for item in top_events],
            "risk_notice": "Structured output is based on public information extraction and ranking for research use only.",
        },
    }


def _compose_event_text(event: dict[str, Any]) -> str:
    metadata = event.get("metadata", {})
    return " ".join(
        part
        for part in [
            event.get("title", ""),
            event.get("summary", ""),
            metadata.get("content_text", ""),
            " ".join(event.get("related_themes", [])),
            " ".join(event.get("related_industries", [])),
        ]
        if part
    )


def _detect_event_subject(title: str, text: str, metadata: dict[str, Any], related_themes: list[str]) -> str:
    for item in metadata.get("stock_list", []) or []:
        if item.get("secu_name"):
            return str(item["secu_name"])
    for item in metadata.get("stocks", []) or []:
        if item.get("name"):
            return str(item["name"])
    for item in metadata.get("plate_list", []) or []:
        if item.get("plate_name"):
            return str(item["plate_name"])
    stripped_title = re.sub(r"[#【】\[\]]", "", title).strip()
    if stripped_title:
        return stripped_title[:32]
    if related_themes:
        return related_themes[0]
    match = re.search(r"[\u4e00-\u9fa5A-Za-z0-9]{4,24}", text)
    return match.group(0) if match else ""


def _extract_embedded_datetime(text: str) -> str:
    patterns = [
        (r"(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)", "%Y-%m-%d %H:%M:%S"),
        (r"(20\d{2}/\d{2}/\d{2} \d{2}:\d{2}(?::\d{2})?)", "%Y/%m/%d %H:%M:%S"),
        (r"(20\d{2}-\d{2}-\d{2})", "%Y-%m-%d"),
    ]
    for pattern, default_fmt in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        value = match.group(1)
        formats = [default_fmt]
        if default_fmt.endswith("%S"):
            formats.append(default_fmt[:-3])
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=UTC).isoformat()
            except ValueError:
                continue
    return ""


def _detect_industries(text: str, related_themes: list[str]) -> list[str]:
    industries = [THEME_TO_INDUSTRY[theme] for theme in related_themes if theme in THEME_TO_INDUSTRY]
    for industry_name, keywords in INDUSTRY_RULES.items():
        if any(keyword in text for keyword in keywords):
            industries.append(industry_name)
    return _merge_unique(industries, [])


def _extract_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term in text]


def _build_narrative_terms(
    related_themes: list[str],
    related_industries: list[str],
    involved_products: list[str],
    involved_technologies: list[str],
    involved_policies: list[str],
) -> list[str]:
    terms: list[str] = []
    for chunk in [related_themes, related_industries, involved_products, involved_technologies, involved_policies]:
        terms.extend(chunk)
    return list(dict.fromkeys(terms))[:8]


def _detect_impact_direction(text: str) -> str:
    positive_hits = sum(1 for word in POSITIVE_WORDS if word in text)
    negative_hits = sum(1 for word in NEGATIVE_WORDS if word in text)
    if positive_hits and negative_hits:
        return "mixed"
    if positive_hits:
        return "positive"
    if negative_hits:
        return "negative"
    return "neutral"


def _detect_impact_scope(text: str, metadata: dict[str, Any], related_themes: list[str]) -> str:
    stock_count = len(metadata.get("stock_list", []) or []) + len(metadata.get("stocks", []) or [])
    if related_themes or metadata.get("plate_list"):
        return "sector"
    if stock_count == 1:
        return "stock"
    if any(keyword in text for keyword in ["全行业", "板块", "产业链", "市场", "全市场"]):
        return "market"
    return "unknown"


def _score_purity_dimensions(
    asset: dict[str, Any],
    event: dict[str, Any],
    text: str,
    theme_name: str,
) -> tuple[dict[str, float], list[str], list[str]]:
    relation = asset.get("relation", "weak")
    theme_evidence = event.get("metadata", {}).get("theme_evidence", [])
    theme_keywords = next((item.get("evidence", []) for item in theme_evidence if item.get("theme") == theme_name), [])

    theme_purity = 88.0 if relation == "direct" else 62.0
    theme_purity += min(len(theme_keywords) * 4, 8)
    if theme_name in text:
        theme_purity += 6

    uniqueness = 55.0 + min(_keyword_hit_count(text, PURITY_KEYWORDS["uniqueness"]) * 10, 35)
    business_elasticity = 52.0 + min(_keyword_hit_count(text, PURITY_KEYWORDS["elasticity"]) * 9, 30)
    market_cap_fit = 52.0
    if any(keyword in text for keyword in ["小盘", "中盘", "弹性"]):
        market_cap_fit += 14
    if any(keyword in text for keyword in ["千亿市值", "大市值"]):
        market_cap_fit -= 10

    financial_health = 86.0
    risk_flags = [keyword for keyword in PURITY_KEYWORDS["financial_risk"] if keyword in text or keyword in asset.get("stock_name", "")]
    financial_health -= min(len(risk_flags) * 14, 56)

    theme_memory = 50.0 + min(_keyword_hit_count(text, PURITY_KEYWORDS["memory"]) * 10, 30)
    if relation == "direct":
        theme_memory += 6

    breakdown = {
        "theme_purity": round(max(0.0, min(theme_purity, 100.0)), 2),
        "uniqueness": round(max(0.0, min(uniqueness, 100.0)), 2),
        "business_elasticity": round(max(0.0, min(business_elasticity, 100.0)), 2),
        "market_cap_fit": round(max(0.0, min(market_cap_fit, 100.0)), 2),
        "financial_health": round(max(0.0, min(financial_health, 100.0)), 2),
        "theme_memory": round(max(0.0, min(theme_memory, 100.0)), 2),
    }

    evidence = [theme_name, *theme_keywords[:2]]
    if relation == "direct":
        evidence.append("direct_source_link")
    return breakdown, list(dict.fromkeys([item for item in evidence if item])), risk_flags


def _keyword_hit_count(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _merge_assets(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {(item.get("asset_type"), item.get("asset_id")): item for item in existing}
    for item in incoming:
        key = (item.get("asset_type"), item.get("asset_id"))
        if key not in merged:
            merged[key] = item
    return list(merged.values())


def _merge_unique(left: list[Any], right: list[Any]) -> list[Any]:
    return list(dict.fromkeys([*left, *right]))


def _pick_latest(left: str, right: str) -> str:
    return max([item for item in [left, right] if item], default="")


def _pick_earliest(left: str, right: str) -> str:
    return min([item for item in [left, right] if item], default="")


def _merge_impact_direction(left: str, right: str) -> str:
    if left == right:
        return left
    if "mixed" in {left, right}:
        return "mixed"
    if "positive" in {left, right} and "negative" in {left, right}:
        return "mixed"
    return left if left != "neutral" else right


def _merge_impact_scope(left: str, right: str) -> str:
    rank = {"macro": 4, "market": 3, "sector": 2, "stock": 1, "unknown": 0}
    return left if rank.get(left, 0) >= rank.get(right, 0) else right


def _normalize_stock_code(value: Any) -> str:
    code = str(value or "").strip().upper()
    if not code:
        return ""
    if re.fullmatch(r"\d{6}\.(?:SH|SZ)", code):
        return code
    match = re.fullmatch(r"(SH|SZ)(\d{6})", code)
    if match:
        return f"{match.group(2)}.{match.group(1)}"
    if re.fullmatch(r"\d{6}", code):
        suffix = "SH" if code.startswith("6") else "SZ"
        return f"{code}.{suffix}"
    return code


def _freshness_bonus(event_time: str) -> float:
    if not event_time:
        return 0.0
    try:
        dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
        age_hours = (datetime.now(UTC) - dt.astimezone(UTC)).total_seconds() / 3600
        if age_hours <= 6:
            return 10
        if age_hours <= 24:
            return 5
    except ValueError:
        return 0.0
    return 0.0


def most_common_terms(values: list[str], limit: int = 3) -> list[str]:
    counter = Counter(item for item in values if item)
    return [term for term, _ in counter.most_common(limit)]
