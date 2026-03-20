from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.llm import MultiModelRouter


RUNTIME_ROOT = Path("workspace/artifacts/runtime")
XUEQIU_SOURCE_HINTS = ("xueqiu-hot-spot", "雪球", "xueqiu.com")
ACTION_SUFFIX_RE = re.compile(r"(涨停|涨超\d+%?|连板|回封|大涨|走高|新高|活跃|领涨|跟涨|异动)$")
PUNCT_RE = re.compile(r"[#【】（）()\[\]《》“”\"'：:，,。；;、/\\|]")
NAME_RE = re.compile(r"^[A-Za-z\u4e00-\u9fff]{2,10}$")
STOPWORDS = {
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
    "热门话题",
    "雪球",
    "绿电概念",
    "创新药概念",
    "存储芯片概念",
    "算力租赁",
}
RATIONALE_KEYWORDS = (
    "消息面上",
    "受益于",
    "受益",
    "因为",
    "核心",
    "驱动",
    "催化",
    "政策",
    "订单",
    "商业模式",
    "落地",
    "国家明确要求",
    "推动",
    "加速",
    "放量",
    "直连",
    "一体化",
)


def normalize_candidate_stock_name(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = PUNCT_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = ACTION_SUFFIX_RE.sub("", cleaned).strip()
    cleaned = cleaned.replace("涨停股", "").replace("概念股", "").strip()
    return cleaned


def is_valid_candidate_stock_name(value: str) -> bool:
    cleaned = normalize_candidate_stock_name(value)
    if not cleaned or cleaned in STOPWORDS:
        return False
    if any(stop in cleaned for stop in ("概念", "题材", "板块", "消息面")):
        return False
    if not NAME_RE.fullmatch(cleaned):
        return False
    return True


@dataclass(slots=True)
class SourceReasonPayload:
    reason: str
    source_site: str
    source_url: str
    source_title: str
    source_excerpt: str

    def as_dict(self) -> dict[str, str]:
        return {
            "source_reason": self.reason,
            "source_reason_source_site": self.source_site,
            "source_reason_source_url": self.source_url,
            "source_reason_title": self.source_title,
            "source_reason_excerpt": self.source_excerpt,
        }


class XueqiuEvidenceResolver:
    def __init__(self, runtime_root: str | Path = RUNTIME_ROOT, *, max_runs: int = 12) -> None:
        self.runtime_root = Path(runtime_root)
        self.max_runs = max_runs

    def resolve(self, cluster: dict[str, Any], stock_name: str, stock_code: str = "") -> SourceReasonPayload:
        normalized_name = normalize_candidate_stock_name(stock_name)
        if not normalized_name:
            return SourceReasonPayload("", "", "", "", "")

        signal = self._pick_cluster_signal(cluster, normalized_name)
        runtime_post = self._pick_runtime_post(normalized_name, stock_code)
        chosen = runtime_post if runtime_post and runtime_post["score"] >= (signal or {}).get("score", -1) else signal
        if not chosen:
            return SourceReasonPayload("", "", "", "", "")

        title = self._clean_title(str(chosen.get("title", "") or ""))
        body = str(chosen.get("body", "") or chosen.get("summary", "") or "")
        excerpt = self._build_excerpt(body, normalized_name)
        if normalized_name not in title and normalized_name not in body[:160]:
            return SourceReasonPayload("", "", "", "", "")
        reason = self._compose_reason(normalized_name, title, excerpt)
        return SourceReasonPayload(
            reason=reason,
            source_site="雪球",
            source_url=str(chosen.get("source_url", "") or ""),
            source_title=title,
            source_excerpt=excerpt,
        )

    def _pick_cluster_signal(self, cluster: dict[str, Any], stock_name: str) -> dict[str, Any] | None:
        best: dict[str, Any] | None = None
        best_score = -1
        for signal in cluster.get("supporting_signals", []):
            refs = [str(item) for item in signal.get("source_refs", []) if str(item).strip()]
            if not any("xueqiu.com" in ref for ref in refs):
                continue
            title = str(signal.get("title", "") or "")
            summary = str(signal.get("summary", "") or "")
            text = f"{title} {summary}"
            if stock_name not in text:
                continue
            score = 0
            if stock_name in title:
                score += 8
            score += min(len(summary) // 40, 5)
            score += sum(1 for keyword in RATIONALE_KEYWORDS if keyword in summary)
            if score > best_score:
                best_score = score
                best = {
                    "title": title,
                    "summary": summary,
                    "body": summary,
                    "source_url": next((ref for ref in refs if "xueqiu.com" in ref), refs[0] if refs else ""),
                    "score": score,
                }
        return best

    def _pick_runtime_post(self, stock_name: str, stock_code: str) -> dict[str, Any] | None:
        if not self.runtime_root.exists():
            return None

        best: dict[str, Any] | None = None
        best_score = -1
        run_dirs = sorted(
            (item for item in self.runtime_root.iterdir() if item.is_dir()),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[: self.max_runs]

        for run_dir in run_dirs:
            raw_documents_path = run_dir / "raw_documents.json"
            if not raw_documents_path.exists():
                continue
            try:
                documents = json.loads(raw_documents_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            for item in documents:
                if not isinstance(item, dict):
                    continue
                source_id = str(item.get("source_id", "") or "")
                site_name = str(item.get("site_name", "") or "")
                source_url = str(item.get("source_url", "") or "")
                if not any(hint in f"{source_id} {site_name} {source_url}" for hint in XUEQIU_SOURCE_HINTS):
                    continue
                title = str(item.get("title", "") or "")
                summary = str(item.get("summary", "") or "")
                body = str(item.get("content_text", "") or item.get("body", "") or summary)
                haystack = f"{title}\n{summary}\n{body}"
                if stock_name not in haystack and stock_code and stock_code.split(".")[0] not in haystack:
                    continue

                score = 0
                if stock_name in title:
                    score += 10
                if stock_name in summary:
                    score += 6
                score += min(len(body) // 80, 8)
                score += sum(1 for keyword in RATIONALE_KEYWORDS if keyword in haystack)

                if score > best_score:
                    best_score = score
                    best = {
                        "title": title,
                        "summary": summary,
                        "body": body,
                        "source_url": source_url,
                        "score": score,
                    }
        return best

    @staticmethod
    def _clean_title(value: str) -> str:
        cleaned = str(value or "").strip()
        cleaned = re.sub(r"\s*-\s*热门话题\s*-\s*雪球$", "", cleaned)
        cleaned = re.sub(r"\s*-\s*雪球$", "", cleaned)
        cleaned = cleaned.strip("# ").strip()
        return cleaned

    @staticmethod
    def _build_excerpt(text: str, stock_name: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
        if not cleaned:
            return ""

        sentences = [part.strip() for part in re.split(r"[。！？!?；;]", cleaned) if part.strip()]
        preferred = [part for part in sentences if stock_name in part and any(keyword in part for keyword in RATIONALE_KEYWORDS)]
        if preferred:
            return preferred[0][:120]

        for index, sentence in enumerate(sentences):
            if stock_name not in sentence:
                continue
            next_sentence = sentences[index + 1] if index + 1 < len(sentences) else ""
            if next_sentence and any(keyword in next_sentence for keyword in RATIONALE_KEYWORDS):
                return next_sentence[:120]

        named = [part for part in sentences if stock_name in part]
        if named:
            return named[0][:120]

        rationale = [part for part in sentences if any(keyword in part for keyword in RATIONALE_KEYWORDS)]
        if rationale:
            return rationale[0][:120]

        return cleaned[:120]

    @staticmethod
    def _compose_reason(stock_name: str, title: str, excerpt: str) -> str:
        if title and excerpt:
            return f"雪球帖子《{title}》提到{stock_name}，核心依据是：{excerpt}。"
        if title:
            return f"雪球帖子《{title}》把{stock_name}列入观察范围，后续需要继续跟踪催化兑现。"
        if excerpt:
            return f"雪球讨论里提到{stock_name}，核心依据是：{excerpt}。"
        return ""


class StockReasonLLMWriter:
    def __init__(
        self,
        router: MultiModelRouter,
        *,
        fallback_models: list[str] | None = None,
    ) -> None:
        self.router = router
        self.fallback_models = fallback_models or []

    @property
    def available(self) -> bool:
        return self.router.available

    def build_reason(
        self,
        cluster: dict[str, Any],
        stock: dict[str, Any],
        source_payload: SourceReasonPayload,
    ) -> str:
        if not self.available:
            return ""

        stock_name = str(stock.get("stock_name", "") or stock.get("stock_code", "") or "").strip()
        if not stock_name:
            return ""

        text = self.router.text_completion(
            system_prompt=(
                "你是A股个股研究助理。"
                "请基于公开证据，输出2到3句中文总结，解释市场为什么会把这只股票与当前主线联系起来。"
                "如果题材标签与证据不一致，要直接指出，不要硬说它是核心受益。"
                "不要写成买卖指令，不要夸张，不要编造公司信息。"
            ),
            user_prompt=json.dumps(
                {
                    "theme_name": cluster.get("theme_name", ""),
                    "core_narrative": cluster.get("core_narrative", ""),
                    "stock_name": stock_name,
                    "stock_code": stock.get("stock_code", ""),
                    "mapping_level": stock.get("mapping_level", ""),
                    "purity_score": stock.get("candidate_purity_score", 0),
                    "source_evidence": {
                        "title": source_payload.source_title,
                        "excerpt": source_payload.source_excerpt,
                        "url": source_payload.source_url,
                    },
                    "other_evidence": stock.get("evidence", [])[:4],
                    "judge_explanation": stock.get("judge_explanation", ""),
                    "scarcity_note": stock.get("scarcity_note", ""),
                    "required_output": "直接输出2到3句中文，不要加项目符号，不要返回JSON。",
                },
                ensure_ascii=False,
            ),
            fallback_models=self.fallback_models,
            temperature=0.2,
        )
        cleaned = str(text or "").strip()
        cleaned = cleaned.strip("`")
        cleaned = re.sub(r"^\s*\[|\]\s*$", "", cleaned)
        cleaned = cleaned.replace("\\n", " ").strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if not cleaned:
            return ""
        return cleaned
