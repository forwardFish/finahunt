from pathlib import Path

from skills.event.stock_reasoning import XueqiuEvidenceResolver, normalize_candidate_stock_name


def test_normalize_candidate_stock_name_removes_action_suffix():
    assert normalize_candidate_stock_name("江苏新能涨停") == "江苏新能"
    assert normalize_candidate_stock_name("#浙江新能#") == "浙江新能"


def test_xueqiu_evidence_resolver_prefers_runtime_post(tmp_path: Path):
    run_dir = tmp_path / "run-demo"
    run_dir.mkdir()
    (run_dir / "raw_documents.json").write_text(
        """
        [
          {
            "source_id": "xueqiu-hot-spot",
            "site_name": "雪球热点",
            "source_url": "https://xueqiu.com/demo/1",
            "title": "#绿电概念活跃，江苏新能涨停# - 热门话题 - 雪球",
            "summary": "绿电概念盘中再度活跃，江苏新能涨停。",
            "content_text": "绿电概念盘中再度活跃，江苏新能涨停。消息面上，国家明确要求国家算力枢纽节点新建数据中心的绿电占比不低于80%，推动绿电直连和源网荷储一体化加速落地。"
          }
        ]
        """,
        encoding="utf-8",
    )

    resolver = XueqiuEvidenceResolver(tmp_path)
    payload = resolver.resolve({"supporting_signals": []}, "江苏新能", "603693.SH")

    assert payload.source_site == "雪球"
    assert payload.source_url == "https://xueqiu.com/demo/1"
    assert "江苏新能" in payload.reason
    assert "绿电占比不低于80%" in payload.source_excerpt
