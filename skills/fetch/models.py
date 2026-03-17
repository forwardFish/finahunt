from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DiscoveryItem(BaseModel):
    source_id: str
    site_name: str
    external_id: str
    list_url: str
    detail_url: str
    title: str
    summary: str = ""
    published_at: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RawContent(BaseModel):
    content_id: str
    source_id: str
    site_name: str
    list_url: str
    source_url: str
    fetched_at: str
    published_at: str = ""
    title: str
    body: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
