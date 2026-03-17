import json
from pathlib import Path

from skills.fetch.client import extract_js_object_by_assignment, extract_json_array_by_key, fetch_documents
from skills.fetch.models import RawContent
from skills.fetch.storage import RawContentRepository


def test_fetch_documents_maps_raw_content_into_raw_news_items(monkeypatch, tmp_path):
    def fake_pipeline(sources, *, max_items_per_source, timeout, run_id):
        item = RawContent(
            content_id="rawc-001",
            source_id="xueqiu-hot-spot",
            site_name="雪球热点",
            list_url="https://xueqiu.com/hot/spot",
            source_url="https://xueqiu.com/hashtag/demo",
            fetched_at="2026-03-16T10:00:00+00:00",
            published_at="2026-03-16T09:50:00+00:00",
            title="低空物流试点推进",
            body="低空物流试点推进，无人机配送与eVTOL商业化叙事升温。",
            author="雪球编辑",
            tags=["community", "hot_spot"],
            metadata={"stocks": [{"code": "300696.SZ", "name": "爱乐达"}]},
        )
        return {
            "raw_contents": [item.model_dump(mode="json")],
            "execution_log": [{"source_id": "xueqiu-hot-spot", "status": "success", "stored_count": 1}],
            "storage_summary": {"batch_dir": str(tmp_path), "manifest": {"content_count": 1}},
        }

    monkeypatch.setattr("skills.fetch.client.crawl_public_page_sources_sync", fake_pipeline)
    result = fetch_documents(
        [
            {
                "source_id": "xueqiu-hot-spot",
                "source_name": "雪球热点",
                "channel_type": "public_site",
                "base_url": "https://xueqiu.com/hot/spot",
                "field_contract": {"parser_key": "xueqiu_hot_spot_html"},
            }
        ],
        run_id="run-test",
    )

    assert len(result["raw_documents"]) == 1
    assert result["raw_documents"][0]["document_id"] == "rawc-001"
    assert result["raw_documents"][0]["metadata"]["stock_list"][0]["code"] == "300696.SZ"
    assert result["storage_summary"]["manifest"]["content_count"] == 1


def test_extract_json_array_by_key_raises_on_missing_marker():
    try:
        extract_json_array_by_key("<html></html>", "telegraphList")
    except ValueError as exc:
        assert "marker_not_found" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError")


def test_extract_js_object_by_assignment_supports_undefined_values():
    html = """
    <script>
    window.__INITIAL_STORE__ = {"initStore":{"timeLineData":[{"id":1}]},"isLogin":undefined};
    </script>
    """
    payload = extract_js_object_by_assignment(html, "window.__INITIAL_STORE__ = ")
    assert payload["initStore"]["timeLineData"][0]["id"] == 1
    assert payload["isLogin"] is None


def test_raw_content_repository_filters_incremental_duplicates(tmp_path):
    repository = RawContentRepository(base_dir=tmp_path / "source_fetch")
    item = RawContent(
        content_id="rawc-001",
        source_id="cls-telegraph",
        site_name="财联社快讯",
        list_url="https://www.cls.cn/telegraph",
        source_url="https://www.cls.cn/detail/1",
        fetched_at="2026-03-16T10:00:00+00:00",
        published_at="2026-03-16T09:50:00+00:00",
        title="工信部支持机器人产业创新",
        body="机器人产业政策支持落地。",
    )

    first_batch, first_skipped = repository.filter_incremental("cls-telegraph", [item])
    second_batch, second_skipped = repository.filter_incremental("cls-telegraph", [item])
    summary = repository.store_batch("run-demo", first_batch)

    assert len(first_batch) == 1
    assert first_skipped == 0
    assert len(second_batch) == 0
    assert second_skipped == 1
    payload = (Path(summary["batch_dir"]) / "raw_contents.jsonl").read_text(encoding="utf-8").strip()
    assert json.loads(payload)["title"] == "工信部支持机器人产业创新"
