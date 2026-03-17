from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from skills.fetch.html import HtmlSnapshot, clean_text
from skills.fetch.models import DiscoveryItem, RawContent


class PublicPageAdapter(ABC):
    def __init__(self, source: dict[str, Any], profile: dict[str, Any]) -> None:
        self.source = source
        self.profile = profile
        self.source_id = source["source_id"]
        self.site_name = profile.get("site_name") or source["source_name"]
        self.list_url = profile.get("list_url") or source["base_url"]

    @abstractmethod
    def parse_list(self, snapshot: HtmlSnapshot, *, max_items: int) -> list[DiscoveryItem]:
        raise NotImplementedError

    @abstractmethod
    async def build_raw_content(
        self,
        discovery_item: DiscoveryItem,
        detail_snapshot: HtmlSnapshot | None,
    ) -> RawContent:
        raise NotImplementedError

    def build_content_id(self, discovery_item: DiscoveryItem) -> str:
        seed = f"{self.source_id}|{discovery_item.detail_url}|{discovery_item.external_id}|{discovery_item.title}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
        return f"rawc-{digest}"

    def normalize_timestamp(self, value: str) -> str:
        value = clean_text(value)
        if not value:
            return datetime.now(UTC).isoformat()
        if value.isdigit():
            if len(value) >= 13:
                return datetime.fromtimestamp(int(value) / 1000, tz=UTC).isoformat()
            return datetime.fromtimestamp(int(value), tz=UTC).isoformat()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=UTC).isoformat()
            except ValueError:
                continue
        return value

    def normalize_stock_code(self, value: Any) -> str:
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

    def normalize_tags(self, values: list[str]) -> list[str]:
        return list(dict.fromkeys([clean_text(value).strip("#") for value in values if clean_text(value)]))
