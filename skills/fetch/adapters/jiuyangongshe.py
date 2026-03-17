from __future__ import annotations

import re
from datetime import UTC, datetime

from skills.fetch.adapters.base import PublicPageAdapter
from skills.fetch.html import HtmlSnapshot, clean_text, decode_js_string
from skills.fetch.models import DiscoveryItem, RawContent


class JiuyangongsheAdapter(PublicPageAdapter):
    ARTICLE_PATTERN = re.compile(
        r'article_id:"(?P<article_id>[^"]+)".*?'
        r'title:"(?P<title>[^"]*)".*?'
        r'create_time:"(?P<create_time>[^"]+)".*?'
        r'content:"(?P<content>.*?)",user:\{',
        re.S,
    )

    def parse_list(self, snapshot: HtmlSnapshot, *, max_items: int) -> list[DiscoveryItem]:
        discoveries: list[DiscoveryItem] = []
        for match in self.ARTICLE_PATTERN.finditer(snapshot.html):
            article_id = match.group("article_id")
            title = decode_js_string(match.group("title"))
            content = decode_js_string(match.group("content"))
            discoveries.append(
                DiscoveryItem(
                    source_id=self.source_id,
                    site_name=self.site_name,
                    external_id=article_id,
                    list_url=self.list_url,
                    detail_url=f"{self.list_url}#{article_id}",
                    title=clean_text(title or content[:40] or self.site_name),
                    summary=clean_text(content)[:160],
                    published_at=self.normalize_timestamp(match.group("create_time")),
                    tags=["community", "live"],
                    metadata={
                        "article_id": article_id,
                        "list_content": clean_text(content),
                    },
                )
            )
            if len(discoveries) >= max_items:
                break
        return discoveries

    async def build_raw_content(self, discovery_item: DiscoveryItem, detail_snapshot: HtmlSnapshot | None) -> RawContent:
        fetched_at = datetime.now(UTC).isoformat()
        detail = self.profile.get("detail", {})
        body = discovery_item.metadata.get("list_content", "")
        title = discovery_item.title
        author = discovery_item.author
        tags = discovery_item.tags
        published_at = discovery_item.published_at

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
