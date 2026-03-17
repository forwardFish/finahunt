from skills.event.intake import derive_catalyst_boundary, derive_continuity_hint, scout_early_catalyst_inputs


def test_source_scout_prioritizes_early_catalyst_documents():
    documents = [
        {
            "document_id": "doc-001",
            "source_id": "cls-telegraph",
            "title": "工信部发布低空试点政策",
            "summary": "政策试点推进低空物流落地。",
            "content_text": "工信部发布指导意见，推进低空物流试点落地。",
            "published_at": "2026-03-17T10:00:00+00:00",
            "metadata": {"stock_list": [{"secu_code": "300001.SZ"}], "plate_list": [{"plate_name": "低空经济"}]},
        },
        {
            "document_id": "doc-002",
            "source_id": "xueqiu-hot-spot",
            "title": "热议机器人段子",
            "summary": "大家在闲聊情绪。",
            "content_text": "热议，闲聊，情绪很高。",
            "published_at": "2026-03-17T10:05:00+00:00",
            "metadata": {},
        },
    ]
    registry_map = {
        "cls-telegraph": {"discovery_priority": "P0", "discovery_role": "early_catalyst_wire"},
        "xueqiu-hot-spot": {"discovery_priority": "P1", "discovery_role": "hotspot_theme_signal"},
    }

    result = scout_early_catalyst_inputs(documents, registry_map)

    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["document_id"] == "doc-001"
    assert result["candidates"][0]["metadata"]["source_priority"] == "P0"
    assert "policy" in result["candidates"][0]["metadata"]["catalyst_clue_types"]
    assert result["dropped"][0]["document_id"] == "doc-002"


def test_derive_catalyst_boundary_and_continuity_hint():
    boundary = derive_catalyst_boundary(
        related_themes=["低空经济"],
        related_industries=[],
        linked_assets=[{"asset_type": "stock", "asset_id": "300001.SZ"}],
        impact_scope="sector",
    )
    continuity = derive_continuity_hint("老题材重新发酵并持续推进", "老题材重新激活", "P1")

    assert boundary == "theme"
    assert continuity == "reignited"
