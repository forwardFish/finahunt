from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from packages.schema.state import GraphState
from packages.storage import get_runtime_repository


RUNTIME_ROOT = Path("workspace/artifacts/runtime")
_DB_ARTIFACT_WRITE_DISABLED = False


def runtime_run_dir(run_id: str) -> Path:
    path = RUNTIME_ROOT / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_artifact_path(run_id: str, filename: str) -> Path:
    return runtime_run_dir(run_id) / filename


def persist_runtime_json(
    state: GraphState,
    *,
    stage: str,
    filename: str,
    payload: Any,
    record_count: int | None = None,
    summary: dict[str, Any] | None = None,
) -> Path:
    run_id = state["run_id"]
    trace_id = state["metadata"]["trace_id"]
    artifact_path = runtime_artifact_path(run_id, filename)
    artifact_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_path = runtime_artifact_path(run_id, "manifest.json")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "run_id": run_id,
            "trace_id": trace_id,
            "created_at": datetime.now(UTC).isoformat(),
            "stages": {},
        }

    manifest["updated_at"] = datetime.now(UTC).isoformat()
    stage_entry = manifest["stages"].setdefault(stage, {"artifacts": []})
    artifact_record = {
        "filename": filename,
        "path": artifact_path.as_posix(),
        "record_count": record_count,
        "summary": summary or {},
        "updated_at": datetime.now(UTC).isoformat(),
    }

    existing = next((item for item in stage_entry["artifacts"] if item["filename"] == filename), None)
    if existing:
        existing.update(artifact_record)
    else:
        stage_entry["artifacts"].append(artifact_record)

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    global _DB_ARTIFACT_WRITE_DISABLED
    if _DB_ARTIFACT_WRITE_DISABLED:
        return artifact_path
    try:
        get_runtime_repository().save_runtime_artifact(
            run_id=run_id,
            trace_id=trace_id,
            stage=stage,
            filename=filename,
            path=artifact_path.as_posix(),
            payload=payload,
            record_count=record_count,
            summary=summary or {},
        )
    except Exception:
        # JSON artifact is the transition fallback; database lane reports hard status separately.
        _DB_ARTIFACT_WRITE_DISABLED = True
        pass
    return artifact_path
