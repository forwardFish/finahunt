from tools.gate_check import build_validation_report


def test_gate_validation_report_passes():
    report = build_validation_report()
    assert report["passed"] is True
    assert report["agent_count"] >= 18
    assert report["gate_count"] == 4
