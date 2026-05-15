from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from packages.storage.models import (
    Base,
    DailySnapshot,
    Event,
    LowPositionWorkbench,
    NormalizedContent,
    RawContent,
    RuntimeArtifact,
    RuntimeRun,
    StockThemeMatch,
    Theme,
    ThemeEvent,
)


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
RUNTIME_ROOT = Path("workspace/artifacts/runtime")
DEFAULT_LOCAL_POSTGRES_URL = "postgresql+psycopg://finahunt:finahunt_local@127.0.0.1:54329/finahunt"


@dataclass(slots=True)
class StorageWriteStatus:
    backend: str
    status: str
    message: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"backend": self.backend, "status": self.status, "message": self.message}


class RuntimeRepository(Protocol):
    backend: str

    def bootstrap(self) -> StorageWriteStatus: ...

    def save_runtime_artifact(
        self,
        *,
        run_id: str,
        trace_id: str,
        stage: str,
        filename: str,
        path: str,
        payload: Any,
        record_count: int | None,
        summary: dict[str, Any],
    ) -> StorageWriteStatus: ...

    def save_runtime_projection(
        self,
        *,
        run_id: str,
        trace_id: str,
        artifact_batch_dir: str,
        artifacts: dict[str, Any],
    ) -> StorageWriteStatus: ...

    def load_daily_snapshot(self, date: str | None = None) -> dict[str, Any] | None: ...

    def load_low_position_workbench(self, date: str | None = None) -> dict[str, Any] | None: ...


def get_runtime_repository() -> RuntimeRepository:
    backend = os.getenv("DATABASE_BACKEND", "postgres").strip().lower()
    if backend == "json":
        return JsonLegacyRepository(enabled=True)
    database_url = os.getenv("DATABASE_URL", "").strip() or os.getenv("FINAHUNT_LOCAL_DATABASE_URL", "").strip()
    return PostgresRepository(database_url or DEFAULT_LOCAL_POSTGRES_URL)


class JsonLegacyRepository:
    backend = "json"

    def __init__(self, *, enabled: bool = True, status_message: str = "") -> None:
        self.enabled = enabled
        self.status_message = status_message

    def bootstrap(self) -> StorageWriteStatus:
        if not self.enabled:
            return StorageWriteStatus("postgres", "DOCUMENTED_BLOCKER", self.status_message)
        return StorageWriteStatus(self.backend, "PASS_WITH_LIMITATION", "Using legacy JSON runtime artifacts.")

    def save_runtime_artifact(self, **_: Any) -> StorageWriteStatus:
        if not self.enabled:
            return StorageWriteStatus("postgres", "DOCUMENTED_BLOCKER", self.status_message)
        return StorageWriteStatus(self.backend, "PASS_WITH_LIMITATION", "JSON artifact retained; database write skipped by DATABASE_BACKEND=json.")

    def save_runtime_projection(self, **_: Any) -> StorageWriteStatus:
        if not self.enabled:
            return StorageWriteStatus("postgres", "DOCUMENTED_BLOCKER", self.status_message)
        return StorageWriteStatus(self.backend, "PASS_WITH_LIMITATION", "JSON projection read mode.")

    def load_daily_snapshot(self, date: str | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        run_dir = _latest_runtime_dir()
        if run_dir is None:
            return None
        artifacts = _load_runtime_artifacts(run_dir)
        return _build_daily_snapshot(run_dir.name, "", run_dir.as_posix(), artifacts, date or _today())

    def load_low_position_workbench(self, date: str | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        run_dir = _latest_runtime_dir()
        if run_dir is None:
            return None
        artifacts = _load_runtime_artifacts(run_dir)
        return _build_low_position_workbench(run_dir.name, run_dir.as_posix(), artifacts, date or _today())


class PostgresRepository:
    backend = "postgres"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        connect_args: dict[str, Any] = {}
        if database_url.startswith("postgresql"):
            connect_args["connect_timeout"] = int(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "5"))
        self.engine: Engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def bootstrap(self) -> StorageWriteStatus:
        Base.metadata.create_all(self.engine)
        return StorageWriteStatus(self.backend, "PASS", "Postgres schema ready.")

    def save_runtime_artifact(
        self,
        *,
        run_id: str,
        trace_id: str,
        stage: str,
        filename: str,
        path: str,
        payload: Any,
        record_count: int | None,
        summary: dict[str, Any],
    ) -> StorageWriteStatus:
        self.bootstrap()
        with self.session_factory.begin() as session:
            _merge_runtime_run(session, run_id, trace_id, "")
            existing = session.execute(
                select(RuntimeArtifact).where(RuntimeArtifact.run_id == run_id, RuntimeArtifact.filename == filename)
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    RuntimeArtifact(
                        run_id=run_id,
                        stage=stage,
                        filename=filename,
                        path=path,
                        record_count=record_count,
                        summary=summary,
                        payload=payload,
                    )
                )
            else:
                existing.stage = stage
                existing.path = path
                existing.record_count = record_count
                existing.summary = summary
                existing.payload = payload
        return StorageWriteStatus(self.backend, "PASS", f"Stored {filename}.")

    def save_runtime_projection(
        self,
        *,
        run_id: str,
        trace_id: str,
        artifact_batch_dir: str,
        artifacts: dict[str, Any],
    ) -> StorageWriteStatus:
        self.bootstrap()
        date = _projection_date(artifacts)
        daily_snapshot = _build_daily_snapshot(run_id, trace_id, artifact_batch_dir, artifacts, date)
        workbench = _build_low_position_workbench(run_id, artifact_batch_dir, artifacts, date)
        with self.session_factory.begin() as session:
            _merge_runtime_run(session, run_id, trace_id, artifact_batch_dir)
            _merge_raw_contents(session, run_id, artifacts.get("raw_documents.json", []))
            _merge_normalized_contents(session, run_id, artifacts.get("normalized_documents.json", []))
            _merge_events(session, run_id, artifacts.get("canonical_events.json", []))
            _merge_themes(session, run_id, artifacts.get("theme_heat_snapshots.json", []), artifacts.get("low_position_opportunities.json", []))
            _merge_theme_events(session, run_id, artifacts.get("canonical_events.json", []))
            _merge_stock_matches(session, run_id, artifacts.get("daily_theme_workbench.json", {}).get("themes", []))
            _merge_snapshot(session, date, run_id, daily_snapshot)
            _merge_workbench(session, date, run_id, workbench)
        return StorageWriteStatus(self.backend, "PASS", "Runtime projection stored in Postgres.")

    def load_daily_snapshot(self, date: str | None = None) -> dict[str, Any] | None:
        self.bootstrap()
        with self.session_factory() as session:
            query = select(DailySnapshot)
            if date:
                query = query.where(DailySnapshot.date == date)
            row = session.execute(query.order_by(DailySnapshot.created_at.desc())).scalars().first()
            return dict(row.payload) if row is not None else None

    def load_low_position_workbench(self, date: str | None = None) -> dict[str, Any] | None:
        self.bootstrap()
        with self.session_factory() as session:
            query = select(LowPositionWorkbench)
            if date:
                query = query.where(LowPositionWorkbench.date == date)
            row = session.execute(query.order_by(LowPositionWorkbench.created_at.desc())).scalars().first()
            return dict(row.payload) if row is not None else None


def _merge_runtime_run(session: Session, run_id: str, trace_id: str, artifact_batch_dir: str) -> None:
    row = session.get(RuntimeRun, run_id)
    if row is None:
        session.add(RuntimeRun(run_id=run_id, trace_id=trace_id, artifact_batch_dir=artifact_batch_dir, status="success"))
    else:
        row.trace_id = trace_id or row.trace_id
        row.artifact_batch_dir = artifact_batch_dir or row.artifact_batch_dir
        row.status = "success"


def _merge_raw_contents(session: Session, run_id: str, rows: list[dict[str, Any]]) -> None:
    for item in rows:
        document_id = str(item.get("document_id") or item.get("id") or f"{run_id}-raw-{len(str(item))}")
        session.merge(
            RawContent(
                document_id=document_id,
                run_id=run_id,
                source_id=str(item.get("source_id", "") or ""),
                source_name=str(item.get("source_name", "") or ""),
                title=str(item.get("title", "") or ""),
                url=str(item.get("url", "") or ""),
                published_at=str(item.get("published_at", "") or ""),
                content_text=str(item.get("content_text", "") or ""),
                payload=item,
            )
        )


def _merge_normalized_contents(session: Session, run_id: str, rows: list[dict[str, Any]]) -> None:
    for item in rows:
        document_id = str(item.get("document_id") or item.get("id") or f"{run_id}-normalized-{len(str(item))}")
        session.merge(
            NormalizedContent(
                document_id=document_id,
                run_id=run_id,
                source_id=str(item.get("source_id", "") or ""),
                source_name=str(item.get("source_name", "") or ""),
                title=str(item.get("title", "") or ""),
                url=str(item.get("url", "") or ""),
                published_at=str(item.get("published_at", "") or ""),
                payload=item,
            )
        )


def _merge_events(session: Session, run_id: str, rows: list[dict[str, Any]]) -> None:
    for item in rows:
        event_id = str(item.get("event_id") or item.get("id") or f"{run_id}-event-{len(str(item))}")
        session.merge(
            Event(
                event_id=event_id,
                run_id=run_id,
                title=str(item.get("title", "") or ""),
                event_type=str(item.get("event_type", "") or ""),
                event_subject=str(item.get("event_subject", "") or ""),
                event_time=str(item.get("event_time", "") or item.get("occurred_at", "") or ""),
                source_name=str(item.get("source_name", "") or ""),
                source_url=str((item.get("source_refs") or [""])[0] if isinstance(item.get("source_refs"), list) and item.get("source_refs") else ""),
                payload=item,
            )
        )


def _merge_themes(session: Session, run_id: str, heat_rows: list[dict[str, Any]], low_rows: list[dict[str, Any]]) -> None:
    low_by_theme = {str(item.get("theme_name", "") or ""): item for item in low_rows}
    for item in heat_rows:
        name = str(item.get("theme_name", "") or "")
        low = low_by_theme.get(name, {})
        theme_key = _theme_key(run_id, name, str(item.get("cluster_id", "") or ""))
        session.merge(
            Theme(
                theme_key=theme_key,
                run_id=run_id,
                theme_name=name,
                cluster_id=str(item.get("cluster_id", "") or ""),
                heat_score=_number(item.get("heat_score") or item.get("theme_heat_score")),
                catalyst_score=_number(item.get("catalyst_score")),
                continuity_score=_number(item.get("continuity_score")),
                fermentation_score=_number(item.get("fermentation_score")),
                low_position_score=_number(low.get("low_position_score")),
                fermentation_stage=str(item.get("fermentation_stage") or item.get("fermentation_phase") or ""),
                payload={**item, "low_position": low},
            )
        )


def _merge_theme_events(session: Session, run_id: str, events: list[dict[str, Any]]) -> None:
    for event in events:
        event_id = str(event.get("event_id") or "")
        for theme_name in _strings([*event.get("related_themes", []), *event.get("theme_tags", [])]):
            theme_key = _theme_key(run_id, theme_name, "")
            session.merge(ThemeEvent(theme_key=theme_key, event_id=event_id, run_id=run_id, relation="mentioned", payload={}))


def _merge_stock_matches(session: Session, run_id: str, themes: list[dict[str, Any]]) -> None:
    for theme in themes:
        theme_name = str(theme.get("theme_name", "") or "")
        theme_key = _theme_key(run_id, theme_name, "")
        for index, stock in enumerate(theme.get("candidate_stocks", []) or []):
            stock_code = str(stock.get("stock_code") or stock.get("company_code") or stock.get("code") or "")
            stock_name = str(stock.get("stock_name") or stock.get("company_name") or stock.get("name") or "")
            match_key = f"{run_id}:{theme_key}:{stock_code or stock_name}:{index}"
            session.merge(
                StockThemeMatch(
                    match_key=match_key,
                    run_id=run_id,
                    theme_key=theme_key,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    purity_score=_number(stock.get("candidate_purity_score") or stock.get("purity_score") or stock.get("score")),
                    mapping_reason=str(stock.get("mapping_reason") or stock.get("source_reason") or ""),
                    is_low_position=True,
                    payload=stock,
                )
            )


def _merge_snapshot(session: Session, date: str, run_id: str, payload: dict[str, Any]) -> None:
    existing = session.execute(select(DailySnapshot).where(DailySnapshot.date == date, DailySnapshot.run_id == run_id)).scalar_one_or_none()
    if existing is None:
        session.add(DailySnapshot(date=date, run_id=run_id, payload=payload, data_mode="postgres"))
    else:
        existing.payload = payload
        existing.data_mode = "postgres"


def _merge_workbench(session: Session, date: str, run_id: str, payload: dict[str, Any]) -> None:
    existing = session.execute(select(LowPositionWorkbench).where(LowPositionWorkbench.date == date, LowPositionWorkbench.run_id == run_id)).scalar_one_or_none()
    if existing is None:
        session.add(LowPositionWorkbench(date=date, run_id=run_id, payload=payload, data_mode="postgres"))
    else:
        existing.payload = payload
        existing.data_mode = "postgres"


def _build_daily_snapshot(run_id: str, trace_id: str, artifact_batch_dir: str, artifacts: dict[str, Any], date: str) -> dict[str, Any]:
    raw = artifacts.get("raw_documents.json", []) or []
    events = artifacts.get("canonical_events.json", []) or []
    heat_rows = artifacts.get("theme_heat_snapshots.json", []) or []
    low_rows = artifacts.get("low_position_opportunities.json", []) or []
    low_by_theme = {str(item.get("theme_name", "") or ""): item for item in low_rows}
    sources = _source_stats(raw)
    themes = [_theme_payload(item, low_by_theme.get(str(item.get("theme_name", "") or ""), {})) for item in heat_rows]
    snapshot_events = [_event_payload(item) for item in events]
    created_at = _manifest_created_at(artifacts) or datetime.now(SHANGHAI_TZ).isoformat()
    return {
        "date": date,
        "storageTimezone": "Asia/Shanghai",
        "dataMode": "postgres" if os.getenv("DATABASE_BACKEND", "postgres").lower() != "json" else "json",
        "stats": {
            "runCount": 1,
            "sourceCount": len(sources),
            "rawDocumentCount": len(raw),
            "canonicalEventCount": len(snapshot_events),
            "themeCount": len(themes),
            "lowPositionCount": len(low_rows),
            "fermentingThemeCount": len([item for item in themes if _number(item.get("fermentationScore")) and (_number(item.get("fermentationScore")) or 0) >= 70]),
        },
        "commonRiskNotices": ["仅展示公开信息研究整理，不构成投资建议。", "数据库数据来自本地 runtime 写入，可继续核对原始 artifact。"],
        "sources": sources,
        "runs": [{"runId": run_id, "createdAt": created_at, "rawDocumentCount": len(raw), "eventCount": len(snapshot_events), "themeCount": len(themes)}],
        "themes": themes,
        "events": snapshot_events,
        "traceId": trace_id,
        "artifactBatchDir": artifact_batch_dir,
    }


def _build_low_position_workbench(run_id: str, artifact_batch_dir: str, artifacts: dict[str, Any], date: str) -> dict[str, Any]:
    message = artifacts.get("daily_message_workbench.json", {}) or {}
    theme = artifacts.get("daily_theme_workbench.json", {}) or {}
    raw_themes = theme.get("themes", []) or []
    themes = [_workbench_theme_payload(item) for item in raw_themes]
    messages = message.get("messages", []) or []
    validated = [item for item in themes if str(item.get("validation_bucket", "")).lower() == "validated"]
    watch = [item for item in themes if item not in validated and str(item.get("validation_bucket", "")).lower() != "downgraded"]
    downgraded = [item for item in themes if str(item.get("validation_bucket", "")).lower() == "downgraded"]
    created_at = _manifest_created_at(artifacts) or datetime.now(SHANGHAI_TZ).isoformat()
    state = str(message.get("status") or theme.get("status") or ("success" if themes else "empty"))
    if state not in {"success", "partial", "empty"}:
        state = "partial" if themes else "empty"
    return {
        "date": date,
        "runId": run_id,
        "createdAt": created_at,
        "latestAvailableDate": date,
        "dataMode": "postgres" if os.getenv("DATABASE_BACKEND", "postgres").lower() != "json" else "json",
        "state": state,
        "messageCount": int(message.get("message_count") or len(messages)),
        "themeCount": int(theme.get("theme_count") or len(themes)),
        "stages": [
            {"stage": "source", "label": "公开来源接入", "status": "pass"},
            {"stage": "theme", "label": "主题聚合", "status": "pass" if themes else "partial"},
            {"stage": "validation", "label": "观察验证", "status": "pass" if messages else "partial"},
        ],
        "messages": messages,
        "themes": themes,
        "validatedThemes": validated,
        "watchThemes": watch,
        "downgradedThemes": downgraded,
        "artifactBatchDir": artifact_batch_dir,
    }


def _theme_payload(item: dict[str, Any], low: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("theme_name", "") or low.get("theme_name", "") or "未命名题材")
    latest_time = str(item.get("latest_event_time") or "")
    return {
        "key": str(item.get("theme_candidate_id") or item.get("cluster_id") or name),
        "themeName": name,
        "clusterId": str(item.get("cluster_id") or ""),
        "coreNarrative": str(low.get("low_position_reason") or item.get("cluster_state") or "主题仍需继续核验。"),
        "firstSeenTime": latest_time,
        "latestSeenTime": latest_time,
        "relatedEventsCount": int(item.get("mention_count") or 0),
        "sourceCount": int(item.get("source_count") or 0),
        "heatScore": _number(item.get("heat_score") or item.get("theme_heat_score")) or 0,
        "catalystScore": _number(item.get("catalyst_score")) or 0,
        "continuityScore": _number(item.get("continuity_score")) or 0,
        "fermentationScore": _number(item.get("fermentation_score")) or 0,
        "lowPositionScore": _number(low.get("low_position_score")),
        "lowPositionReason": str(low.get("low_position_reason") or ""),
        "fermentationStage": str(item.get("fermentation_stage") or item.get("fermentation_phase") or ""),
        "riskNotice": str(low.get("risk_notice") or "仅供研究观察，不构成投资建议。"),
        "genericRiskNotices": [str(low.get("risk_notice") or "证据仍需继续核验。")],
        "candidateStocks": [_candidate_payload(stock) for stock in (low.get("candidate_stocks") or [])],
        "topEvidence": [{"title": name, "summary": str(low.get("low_position_reason") or "主题证据待补充。"), "eventTime": latest_time}],
        "firstSourceUrl": "",
        "topCandidatePurityScore": _number((low.get("candidate_stocks") or [{}])[0].get("candidate_purity_score") if low.get("candidate_stocks") else None),
        "researchPositioningNote": str(low.get("low_position_reason") or ""),
        "referenceType": "runtime",
        "futureWatchSignals": [],
        "riskFlags": [],
        "similarCases": [],
        "latestCatalysts": [{"title": name, "summary": str(low.get("low_position_reason") or "继续观察公开证据。"), "eventTime": latest_time}],
    }


def _event_payload(item: dict[str, Any]) -> dict[str, Any]:
    source_refs = _strings(item.get("source_refs", []))
    themes = _strings([*item.get("related_themes", []), *item.get("theme_tags", [])])
    return {
        "key": str(item.get("event_id") or item.get("canonical_key") or item.get("title") or ""),
        "eventId": str(item.get("event_id") or ""),
        "title": str(item.get("title") or "未命名事件"),
        "eventType": str(item.get("event_type") or "事件"),
        "eventSubject": str(item.get("event_subject") or ""),
        "eventTime": str(item.get("event_time") or item.get("occurred_at") or ""),
        "impactDirection": str(item.get("impact_direction") or "观察"),
        "impactScope": str(item.get("impact_scope") or "公开信息"),
        "summary": str(item.get("summary") or ""),
        "themes": themes,
        "industries": _strings(item.get("related_industries", [])),
        "sourceRefs": source_refs,
        "sourceId": str(item.get("metadata", {}).get("source_id") or ""),
        "sourceName": str(item.get("source_name") or item.get("metadata", {}).get("source_id") or "公开来源"),
    }


def _workbench_theme_payload(item: dict[str, Any]) -> dict[str, Any]:
    stocks = []
    for stock in item.get("candidate_stocks", []) or []:
        normalized = dict(stock)
        normalized.setdefault("company_name", stock.get("stock_name") or stock.get("name") or "")
        normalized.setdefault("company_code", stock.get("stock_code") or stock.get("code") or "")
        normalized.setdefault("purity_score", stock.get("candidate_purity_score") or stock.get("score"))
        stocks.append(normalized)
    return {**item, "candidate_stocks": stocks}


def _candidate_payload(stock: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(stock.get("stock_name") or stock.get("company_name") or stock.get("name") or ""),
        "code": str(stock.get("stock_code") or stock.get("company_code") or stock.get("code") or ""),
        "score": _number(stock.get("candidate_purity_score") or stock.get("purity_score") or stock.get("score")),
        "mappingReason": str(stock.get("mapping_reason") or ""),
        "sourceReason": str(stock.get("source_reason") or ""),
        "sourceReasonSourceSite": str(stock.get("source_reason_source_site") or ""),
        "sourceReasonSourceUrl": str(stock.get("source_reason_source_url") or ""),
        "sourceReasonTitle": str(stock.get("source_reason_title") or ""),
        "sourceReasonExcerpt": str(stock.get("source_reason_excerpt") or ""),
        "llmReason": str(stock.get("llm_reason") or ""),
        "scarcityNote": str(stock.get("scarcity_note") or ""),
        "judgeExplanation": str(stock.get("judge_explanation") or ""),
        "riskFlags": _strings(stock.get("risk_flags", [])),
    }


def _source_stats(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for item in raw:
        source_id = str(item.get("source_id") or "unknown")
        bucket = buckets.setdefault(source_id, {"sourceId": source_id, "sourceName": str(item.get("source_name") or source_id), "documentCount": 0})
        bucket["documentCount"] += 1
    return list(buckets.values())


def _load_runtime_artifacts(run_dir: Path) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for path in run_dir.glob("*.json"):
        try:
            artifacts[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return artifacts


def _latest_runtime_dir() -> Path | None:
    if not RUNTIME_ROOT.exists():
        return None
    dirs = [path for path in RUNTIME_ROOT.iterdir() if path.is_dir() and (path / "manifest.json").exists()]
    if not dirs:
        return None
    return max(dirs, key=lambda item: item.stat().st_mtime)


def _manifest_created_at(artifacts: dict[str, Any]) -> str:
    manifest = artifacts.get("manifest.json", {})
    if isinstance(manifest, dict):
        return str(manifest.get("created_at") or "")
    return ""


def _projection_date(artifacts: dict[str, Any]) -> str:
    created_at = _manifest_created_at(artifacts)
    if created_at:
        try:
            return datetime.fromisoformat(created_at).astimezone(SHANGHAI_TZ).date().isoformat()
        except ValueError:
            pass
    return _today()


def _today() -> str:
    return datetime.now(SHANGHAI_TZ).date().isoformat()


def _theme_key(run_id: str, theme_name: str, cluster_id: str) -> str:
    return f"{run_id}:{cluster_id or theme_name or 'unknown'}"


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item) for item in values if str(item or "").strip()]
