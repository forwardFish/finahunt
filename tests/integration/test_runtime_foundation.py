from workflows.runtime_schedule import run_runtime_cycle


def test_runtime_cycle_produces_structured_outputs():
    result = run_runtime_cycle("foundation-check")
    runtime = result["results"]["source_runtime"]["content"]
    compliance = result["results"]["compliance_guard"]["content"]
    normalize = result["results"]["normalize"]["content"]
    audit = result["results"]["source_audit"]["content"]

    assert runtime["registry_snapshot"]["registry_version"] == "2026.03"
    assert len(runtime["raw_documents"]) >= 3
    assert compliance["compliance_summary"]["allowed_count"] >= 1
    assert normalize["format_validation_report"]["valid"] is True
    assert audit["trace_report"]["documents_normalized"] == len(normalize["normalized_documents"])


def test_runtime_cycle_supports_manual_source_subset():
    result = run_runtime_cycle("subset-check")
    assert result["results"]["source_runtime"]["content"]["fetch_status_report"]["sources"]
