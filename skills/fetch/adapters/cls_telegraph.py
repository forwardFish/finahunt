from __future__ import annotations

from datetime import UTC, datetime

from skills.fetch.adapters.base import PublicPageAdapter
from skills.fetch.html import HtmlSnapshot, clean_text, extract_json_array_by_key
from skills.fetch.models import DiscoveryItem, RawContent


class ClsTelegraphAdapter(PublicPageAdapter):
    def parse_list(self, snapshot: HtmlSnapshot, *, max_items: int) -> list[DiscoveryItem]:
        items = extract_json_array_by_key(snapshot.html, self.profile["list_json_key"])
        discoveries: list[DiscoveryItem] = []
        for item in items[:max_items]:
            content = clean_text(item.get("content") or item.get("brief") or "")
            discoveries.append(
                DiscoveryItem(
                    source_id=self.source_id,
                    site_name=self.site_name,
                    external_id=str(item.get("id") or ""),
                    list_url=self.list_url,
                    detail_url=str(item.get("shareurl") or self.list_url),
                    title=clean_text(item.get("title") or content[:40] or self.site_name),
                    summary=content[:160],
                    published_at=self.normalize_timestamp(str(item.get("ctime") or item.get("modified_time") or "")),
                    tags=["telegraph", "fast_feed"],
                    metadata={
                        "stock_list": item.get("stock_list") or [],
                        "plate_list": item.get("plate_list") or [],
                        "list_content": content,
                    },
                )
            )
        return discoveries

    async def build_raw_content(self, discovery_item: DiscoveryItem, detail_snapshot: HtmlSnapshot | None) -> RawContent:
        fetched_at = datetime.now(UTC).isoformat()
        detail = self.profile.get("detail", {})
        body = discovery_item.metadata.get("list_content", "")
        author = discovery_item.author
        title = discovery_item.title
        tags = discovery_item.tags

        if detail_snapshot is not None:
            title = detail_snapshot.first_text(detail.get("title_selectors", [])) or title
            body = detail_snapshot.first_text(detail.get("body_selectors", [])) or body
            author = detail_snapshot.first_text(detail.get("author_selectors", [])) or author
            tags = self.normalize_tags(detail_snapshot.many_text(detail.get("tag_selectors", [])) or tags)
            published_value = detail_snapshot.first_text(detail.get("published_at_selectors", []))
            published_at = self.normalize_timestamp(published_value) if published_value else discovery_item.published_at
        else:
            published_at = discovery_item.published_at

        return RawContent(
            content_id=self.build_content_id(discovery_item),
            source_id=self.source_id,
            site_name=self.site_name,
            list_url=discovery_item.list_url,
            source_url=discovery_item.detail_url,
            fetched_at=fetched_at,
            published_at=published_at,
            title=title,
            body=body,
            author=author,
            tags=tags,
            metadata=discovery_item.metadata,
        )
