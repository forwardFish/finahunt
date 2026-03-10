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
