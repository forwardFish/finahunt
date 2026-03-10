from __future__ import annotations


def normalize_document(raw_document: dict) -> dict:
    return {
        "document_id": raw_document.get("document_id", ""),
        "title": str(raw_document.get("title", "")).strip(),
        "summary": str(raw_document.get("summary", "")).strip(),
        "published_at": raw_document.get("published_at", ""),
        "source_name": raw_document.get("source_name", ""),
        "source_url": raw_document.get("source_url", ""),
    }
