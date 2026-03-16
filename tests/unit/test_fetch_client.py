from skills.fetch.client import _extract_json_array_by_key, fetch_documents


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_fetch_documents_parses_public_sources(monkeypatch):
    cls_html = """
    <html><script>
    window.__DATA__={"telegraphList":[
      {"id":1,"title":"政策支持机器人产业链","content":"财联社3月16日电，机器人产业链迎来政策支持。","ctime":"2026-03-16 10:00:00","shareurl":"https://www.cls.cn/detail/1","stock_list":[{"secu_code":"300024.SZ","secu_name":"机器人"}],"plate_list":[{"plate_name":"机器人"}]}
    ]};
    </script></html>
    """
    jygs_html = """
    <script>window.__NUXT__=(function(){return{data:[{list:[
      {article_id:"abc123",title:"算力链景气上修",create_time:"2026-03-16 09:00:00",content:"算力服务器需求上修，板块热度提升。",user:{},stock_list:[]}
    ],totalCount:1}]}})()</script>
    """

    def fake_get(url, headers=None, timeout=20):
        if "cls.cn" in url:
            return _FakeResponse(cls_html)
        return _FakeResponse(jygs_html)

    monkeypatch.setattr("skills.fetch.client.requests.get", fake_get)

    sources = [
        {
            "source_id": "cls-telegraph",
            "source_name": "财联社电报",
            "channel_type": "public_site",
            "base_url": "https://www.cls.cn/telegraph",
            "field_contract": {"parser_key": "cls_telegraph_html"},
        },
        {
            "source_id": "jiuyangongshe-live",
            "source_name": "韭研公社短文",
            "channel_type": "public_site",
            "base_url": "https://www.jiuyangongshe.com/live",
            "field_contract": {"parser_key": "jiuyangongshe_live_html"},
        },
    ]
    result = fetch_documents(sources, max_items_per_source=5)
    assert len(result["raw_documents"]) == 2
    assert any(item["source_id"] == "cls-telegraph" for item in result["raw_documents"])
    assert any(item["source_id"] == "jiuyangongshe-live" for item in result["raw_documents"])


def test_extract_json_array_by_key_raises_on_missing_marker():
    try:
        _extract_json_array_by_key("<html></html>", "telegraphList")
    except ValueError as exc:
        assert "marker_not_found" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected ValueError")
