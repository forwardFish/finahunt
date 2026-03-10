from tools.impact_analysis import analyze_impact


def test_impact_analysis_template_is_valid():
    payload = {
        "new_feature_name": "feature-x",
        "impacted_document_items": ["docs/04_规范/Agent体系 - 完整规范手册.md"],
        "impacted_agents": ["Feature Orchestrator Agent"],
        "break_mvp_boundary": False,
        "change_compliance_assumption": False,
        "clarification_required": False,
        "clarification_content": ""
    }
    result = analyze_impact(payload)
    assert result["valid"] is True
    assert result["requires_block"] is False


def test_impact_analysis_blocks_unknown_agents():
    payload = {
        "new_feature_name": "feature-y",
        "impacted_document_items": [],
        "impacted_agents": ["Unknown Agent"],
        "break_mvp_boundary": False,
        "change_compliance_assumption": False,
        "clarification_required": False,
        "clarification_content": ""
    }
    result = analyze_impact(payload)
    assert result["valid"] is False
    assert result["requires_block"] is True
