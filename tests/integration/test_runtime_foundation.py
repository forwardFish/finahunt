from workflows.runtime_schedule import run_runtime_cycle


def test_runtime_cycle_produces_structured_outputs():
    result = run_runtime_cycle("foundation-check")
    runtime = result["results"]["source_runtime"]["content"]
    compliance = result["results"]["compliance_guard"]["content"]
    normalize = result["results"]["normalize"]["content"]
    extract = result["results"]["event_extract"]["content"]
    unify = result["results"]["event_unify"]["content"]
    ranking = result["results"]["relevance_ranking"]["content"]
    review = result["results"]["daily_review"]["content"]
    audit = result["results"]["source_audit"]["content"]

    assert runtime["registry_snapshot"]["registry_version"] == "2026.03.16"
    assert len(runtime["raw_documents"]) >= 1
    assert compliance["compliance_summary"]["allowed_count"] >= 1
    assert normalize["format_validation_report"]["valid"] is True
    assert len(extract["candidate_events"]) >= 1
    assert len(unify["canonical_events"]) >= 1
    assert len(ranking["ranked_events"]) >= 1
    assert "daily_review_report" in review
    assert audit["trace_report"]["documents_normalized"] == len(normalize["normalized_documents"])


def test_runtime_cycle_supports_manual_source_subset():
    result = run_runtime_cycle("subset-check")
    assert result["results"]["source_runtime"]["content"]["fetch_status_report"]["sources"]
