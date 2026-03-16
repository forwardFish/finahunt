from agents.final_gate import FinalGateAgent
from packages.state_manager import StateManager


def test_final_gate_blocks_when_evaluation_fails():
    state = StateManager.new_state(graph_type="governance", input_ref="governance://init")
    state["results"] = {
        "evaluation": {
            "content": {"evaluation_report": {"result": "fail"}},
            "status": "success",
        },
        "governance_audit": {
            "content": {"risk_findings": [{"stage": "test", "risk_level": "high"}]},
            "status": "success",
        },
    }
    result = FinalGateAgent()(state)
    assert result["results"]["final_gate"]["content"]["final_gate_decision"] == "BLOCKED"


def test_final_gate_requires_manual_record_for_high_risk_runtime():
    state = StateManager.new_state(graph_type="governance", input_ref="governance://init")
    state["results"] = {
        "evaluation": {
            "content": {"evaluation_report": {"result": "pass"}},
            "status": "success",
        },
        "governance_audit": {
            "content": {"risk_findings": [{"stage": "runtime", "risk_level": "high"}]},
            "status": "success",
        },
        "compliance_guard": {
            "content": {"manual_review_required": True},
            "status": "success",
        },
        "source_audit": {
            "content": {"runtime_exception_summary": []},
            "status": "success",
        },
    }
    result = FinalGateAgent()(state)
    assert result["results"]["final_gate"]["content"]["final_gate_decision"] == "BLOCKED"
