from pathlib import Path

from workflows.runtime_schedule import run_runtime_cycle


def test_runtime_cycle_produces_structured_outputs():
    result = run_runtime_cycle("foundation-check")
    runtime = result["results"]["source_runtime"]["content"]
    compliance = result["results"]["compliance_guard"]["content"]
    normalize = result["results"]["normalize"]["content"]
    extract = result["results"]["event_extract"]["content"]
    unify = result["results"]["event_unify"]["content"]
    theme_candidates = result["results"]["theme_candidate_aggregation"]["content"]
    result_cards = result["results"]["structured_result_cards"]["content"]
    warehouse = result["results"]["result_warehouse"]["content"]
    theme_heat = result["results"]["theme_heat_snapshot"]["content"]
    theme_feed = result["results"]["fermenting_theme_feed"]["content"]
    ranking = result["results"]["relevance_ranking"]["content"]
    review = result["results"]["daily_review"]["content"]
    audit = result["results"]["source_audit"]["content"]

    assert runtime["registry_snapshot"]["registry_version"] == "2026.03.16"
    assert len(runtime["raw_documents"]) >= 1
    assert compliance["compliance_summary"]["allowed_count"] >= 1
    assert normalize["format_validation_report"]["valid"] is True
    assert len(extract["candidate_events"]) >= 1
    assert len(unify["canonical_events"]) >= 1
    assert len(theme_candidates["theme_candidates"]) >= 1
    assert len(result_cards["structured_result_cards"]) >= 1
    assert warehouse["artifact_batch_dir"]
    assert len(theme_heat["theme_heat_snapshots"]) >= 1
    assert len(theme_feed["fermenting_theme_feed"]) >= 1
    assert len(ranking["ranked_events"]) >= 1
    assert "daily_review_report" in review
    assert audit["trace_report"]["documents_normalized"] == len(normalize["normalized_documents"])
    assert audit["trace_report"]["fermenting_theme_count"] == len(theme_feed["fermenting_theme_feed"])

    batch_dir = Path(warehouse["artifact_batch_dir"])
    assert (batch_dir / "manifest.json").exists()
    assert (batch_dir / "raw_documents.json").exists()
    assert (batch_dir / "normalized_documents.json").exists()
    assert (batch_dir / "canonical_events.json").exists()
    assert (batch_dir / "theme_candidates.json").exists()
    assert (batch_dir / "structured_result_cards.json").exists()
    assert (batch_dir / "theme_heat_snapshots.json").exists()
    assert (batch_dir / "fermenting_theme_feed.json").exists()


def test_runtime_cycle_supports_manual_source_subset():
    result = run_runtime_cycle("subset-check")
    assert result["results"]["source_runtime"]["content"]["fetch_status_report"]["sources"]
