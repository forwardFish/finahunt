from __future__ import annotations

from datetime import UTC, datetime

from skills.fetch.adapters.base import PublicPageAdapter
from skills.fetch.html import HtmlSnapshot, clean_text, decode_js_string, extract_js_object_by_assignment
from skills.fetch.models import DiscoveryItem, RawContent


class XueqiuHotSpotAdapter(PublicPageAdapter):
    def parse_list(self, snapshot: HtmlSnapshot, *, max_items: int) -> list[DiscoveryItem]:
        try:
            payload = extract_js_object_by_assignment(snapshot.html, self.profile["list_assignment"])
        except ValueError:
            return self._parse_dom_list(snapshot, max_items=max_items)

        items = payload.get("initStore", {}).get("timeLineData", [])
        discoveries: list[DiscoveryItem] = []
        for item in items[:max_items]:
            discoveries.append(
                DiscoveryItem(
                    source_id=self.source_id,
                    site_name=self.site_name,
                    external_id=str(item.get("id") or ""),
                    list_url=self.list_url,
                    detail_url=decode_js_string(item.get("url") or self.list_url),
                    title=clean_text(str(item.get("title") or "").strip("#") or self.site_name),
                    summary=clean_text(item.get("content") or "")[:180],
                    published_at="",
                    tags=["community", "hot_spot"],
                    metadata={
                        "reason": clean_text(item.get("reason") or ""),
                        "status_count": item.get("statusCount", 0),
                        "stocks": [
                            {
                                "code": self.normalize_stock_code(stock.get("code")),
                                "name": stock.get("name") or self.normalize_stock_code(stock.get("code")),
                                "percentage": stock.get("percentage", 0),
                            }
                            for stock in item.get("stocks", []) or []
                            if self.normalize_stock_code(stock.get("code"))
                        ],
                        "list_content": clean_text(item.get("content") or ""),
                    },
                )
            )
        return discoveries

    async def build_raw_content(self, discovery_item: DiscoveryItem, detail_snapshot: HtmlSnapshot | None) -> RawContent:
        fetched_at = datetime.now(UTC).isoformat()
        detail = self.profile.get("detail", {})
        title = discovery_item.title
        body = discovery_item.metadata.get("list_content", "")
        author = discovery_item.author
        tags = discovery_item.tags
        published_at = discovery_item.published_at or fetched_at

        if detail_snapshot is not None:
            title = detail_snapshot.first_text(detail.get("title_selectors", [])) or title
            body = detail_snapshot.first_text(detail.get("body_selectors", [])) or body
            author = detail_snapshot.first_text(detail.get("author_selectors", [])) or author
            tags = self.normalize_tags(detail_snapshot.many_text(detail.get("tag_selectors", [])) or tags)
            published_value = detail_snapshot.first_text(detail.get("published_at_selectors", []))
            if published_value:
                published_at = self.normalize_timestamp(published_value)

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

    def _parse_dom_list(self, snapshot: HtmlSnapshot, *, max_items: int) -> list[DiscoveryItem]:
        discoveries: list[DiscoveryItem] = []
        soup = snapshot._soup
        for index, anchor in enumerate(soup.select('a[href*="/hashtag/"]')[:max_items], start=1):
            texts = [clean_text(part) for part in anchor.stripped_strings if clean_text(part)]
            href = anchor.get("href") or self.list_url
            detail_url = href if href.startswith("http") else f"https://xueqiu.com{href}"
            title = next((text for text in texts if text.startswith("#") and text.endswith("#")), "")
            stock_name = texts[2] if len(texts) >= 3 else ""
            heat_reason = next((text for text in texts if "热度值" in text), "")
            discoveries.append(
                DiscoveryItem(
                    source_id=self.source_id,
                    site_name=self.site_name,
                    external_id=f"dom-{index}",
                    list_url=self.list_url,
                    detail_url=detail_url,
                    title=title.strip("#") or stock_name or self.site_name,
                    summary=" | ".join(texts[1:4]),
                    published_at="",
                    tags=["community", "hot_spot"],
                    metadata={
                        "reason": heat_reason,
                        "stocks": [{"code": "", "name": stock_name}] if stock_name else [],
                        "list_content": " | ".join(texts),
                    },
                )
            )
        return discoveries
