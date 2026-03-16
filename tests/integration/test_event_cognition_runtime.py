from workflows.runtime_schedule import run_runtime_cycle


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_event_cognition_runtime_produces_ranked_outputs(monkeypatch):
    cls_html = """
    <html><script>
    window.__DATA__={"telegraphList":[
      {"id":1,"title":"工信部发文支持机器人产业创新","content":"财联社3月16日电，工信部发文支持机器人产业创新发展，机器人板块关注度提升。","ctime":"2026-03-16 10:00:00","shareurl":"https://www.cls.cn/detail/1","stock_list":[{"secu_code":"300024.SZ","secu_name":"机器人"}],"plate_list":[{"plate_name":"机器人"}]},
      {"id":2,"title":"多家公司签署算力服务器订单","content":"财联社3月16日电，多家公司披露算力服务器订单进展。","ctime":"2026-03-16 11:00:00","shareurl":"https://www.cls.cn/detail/2","stock_list":[{"secu_code":"000063.SZ","secu_name":"中兴通讯"}],"plate_list":[{"plate_name":"算力"}]}
    ]};
    </script></html>
    """
    jygs_html = """
    <script>window.__NUXT__=(function(){return{data:[{list:[
      {article_id:"abc123",title:"算力链景气上修",create_time:"2026-03-16 09:00:00",content:"算力服务器需求上修，板块热度提升。",user:{},stock_list:[]},
      {article_id:"def456",title:"晚安啦",create_time:"2026-03-16 08:00:00",content:"晚安啦大家早点休息。",user:{},stock_list:[]}
    ],totalCount:2}]}})()</script>
    """

    def fake_get(url, headers=None, timeout=20):
        if "cls.cn" in url:
            return _FakeResponse(cls_html)
        return _FakeResponse(jygs_html)

    monkeypatch.setattr("skills.fetch.client.requests.get", fake_get)

    result = run_runtime_cycle(
        "event-cognition-test",
        rule_version="v2",
        requested_sources=["cls-telegraph", "jiuyangongshe-live"],
        live_fetch=True,
        user_profile={"watchlist_symbols": ["300024.SZ"], "watchlist_themes": ["机器人", "算力"]},
        max_items_per_source=5,
    )

    runtime = result["results"]["source_runtime"]["content"]
    normalize = result["results"]["normalize"]["content"]
    extract = result["results"]["event_extract"]["content"]
    theme = result["results"]["theme_detection"]["content"]
    catalyst = result["results"]["catalyst_classification"]["content"]
    linkage = result["results"]["stock_linkage"]["content"]
    ranking = result["results"]["relevance_ranking"]["content"]
    review = result["results"]["daily_review"]["content"]

    assert runtime["fetch_status_report"]["live_fetch"] is True
    assert len(runtime["raw_documents"]) >= 3
    assert len(normalize["normalized_documents"]) >= 2
    assert len(normalize["dropped_documents"]) >= 1
    assert len(extract["candidate_events"]) >= 2
    assert all(event["event_id"] for event in extract["candidate_events"])
    assert any(event["theme_tags"] for event in theme["theme_enriched_events"])
    assert any(event["catalyst_type"] != "unknown" for event in catalyst["catalyst_events"])
    assert any(event["linked_assets"] for event in linkage["linked_events"])
    assert ranking["ranked_events"][0]["relevance_score"] >= ranking["ranked_events"][-1]["relevance_score"]
    assert review["today_focus_page"]
    assert "风险" in review["daily_review_report"]["risk_notice"]
