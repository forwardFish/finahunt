from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from skills.fetch.models import RawContent


class RawContentRepository:
    def __init__(self, base_dir: str | Path = "workspace/artifacts/source_fetch") -> None:
        self.base_dir = Path(base_dir)
        self.index_dir = self.base_dir / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def filter_incremental(self, source_id: str, items: list[RawContent]) -> tuple[list[RawContent], int]:
        index = self._load_index(source_id)
        fresh_items: list[RawContent] = []
        skipped = 0
        for item in items:
            fingerprint = self._fingerprint(item)
            if fingerprint in index:
                skipped += 1
                continue
            index[fingerprint] = item.fetched_at
            fresh_items.append(item)
        self._save_index(source_id, index)
        return fresh_items, skipped

    def store_batch(self, run_id: str, items: list[RawContent]) -> dict[str, Any]:
        batch_dir = self.base_dir / run_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        payload_path = batch_dir / "raw_contents.jsonl"
        manifest_path = batch_dir / "manifest.json"

        with payload_path.open("w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")

        by_source: dict[str, int] = {}
        for item in items:
            by_source[item.source_id] = by_source.get(item.source_id, 0) + 1

        manifest = {
            "run_id": run_id,
            "content_count": len(items),
            "sources": by_source,
            "raw_contents_path": str(payload_path),
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"batch_dir": str(batch_dir), "manifest": manifest}

    def _index_path(self, source_id: str) -> Path:
        return self.index_dir / f"{source_id}.json"

    def _load_index(self, source_id: str) -> dict[str, str]:
        path = self._index_path(source_id)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _save_index(self, source_id: str, index: dict[str, str]) -> None:
        self._index_path(source_id).write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    def _fingerprint(self, item: RawContent) -> str:
        published_at = item.published_at or ""
        return f"{item.source_id}|{item.source_url}|{published_at}|{item.title}"
