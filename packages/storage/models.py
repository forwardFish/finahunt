from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RuntimeRun(Base):
    __tablename__ = "runtime_runs"

    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    artifact_batch_dir: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="success")
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class RuntimeArtifact(Base):
    __tablename__ = "runtime_artifacts"
    __table_args__ = (UniqueConstraint("run_id", "filename", name="uq_runtime_artifact_run_file"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(80), ForeignKey("runtime_runs.run_id"), index=True)
    stage: Mapped[str] = mapped_column(String(120), index=True)
    filename: Mapped[str] = mapped_column(String(240), index=True)
    path: Mapped[str] = mapped_column(Text, default="")
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    payload: Mapped[Any] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RawContent(Base):
    __tablename__ = "raw_contents"

    document_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    source_id: Mapped[str] = mapped_column(String(120), default="", index=True)
    source_name: Mapped[str] = mapped_column(Text, default="")
    title: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[str] = mapped_column(String(80), default="")
    content_text: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NormalizedContent(Base):
    __tablename__ = "normalized_contents"

    document_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    source_id: Mapped[str] = mapped_column(String(120), default="", index=True)
    source_name: Mapped[str] = mapped_column(Text, default="")
    title: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[str] = mapped_column(String(80), default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(Text, default="")
    event_type: Mapped[str] = mapped_column(String(120), default="")
    event_subject: Mapped[str] = mapped_column(Text, default="")
    event_time: Mapped[str] = mapped_column(String(80), default="")
    source_name: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Theme(Base):
    __tablename__ = "themes"

    theme_key: Mapped[str] = mapped_column(String(180), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    theme_name: Mapped[str] = mapped_column(Text, default="")
    cluster_id: Mapped[str] = mapped_column(String(160), default="", index=True)
    heat_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    catalyst_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    continuity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fermentation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_position_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fermentation_stage: Mapped[str] = mapped_column(String(80), default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ThemeEvent(Base):
    __tablename__ = "theme_events"

    theme_key: Mapped[str] = mapped_column(String(180), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    relation: Mapped[str] = mapped_column(String(80), default="mentioned")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class StockThemeMatch(Base):
    __tablename__ = "stock_theme_matches"

    match_key: Mapped[str] = mapped_column(String(260), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    theme_key: Mapped[str] = mapped_column(String(180), index=True)
    stock_code: Mapped[str] = mapped_column(String(80), default="")
    stock_name: Mapped[str] = mapped_column(Text, default="")
    purity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    mapping_reason: Mapped[str] = mapped_column(Text, default="")
    is_low_position: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DailySnapshot(Base):
    __tablename__ = "daily_snapshots"
    __table_args__ = (UniqueConstraint("date", "run_id", name="uq_daily_snapshot_date_run"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(20), index=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    data_mode: Mapped[str] = mapped_column(String(40), default="postgres")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LowPositionWorkbench(Base):
    __tablename__ = "low_position_workbenches"
    __table_args__ = (UniqueConstraint("date", "run_id", name="uq_low_position_workbench_date_run"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(20), index=True)
    run_id: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    data_mode: Mapped[str] = mapped_column(String(40), default="postgres")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
