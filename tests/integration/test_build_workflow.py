import pytest

langgraph = pytest.importorskip("langgraph")

from workflows.build_workflow import run_build_workflow


def test_build_workflow_reaches_build_summary():
    result = run_build_workflow("initialize agent system")
    assert "build_summary" in result["results"]
    assert "final_gate" in result["results"]
    assert result["results"]["release"]["content"]["release_pass"] is True
    assert result["results"]["final_gate"]["content"]["final_gate_decision"] == "PASS"
