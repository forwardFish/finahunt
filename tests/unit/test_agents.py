from agents.approval import HumanApprovalCheckpoint
from agents.build.orchestrator import FeatureOrchestratorAgent
from packages.state_manager import StateManager


def test_orchestrator_and_approval_agents_produce_results():
    state = StateManager.new_state(
        graph_type="build",
        input_ref="demand://init",
        context={"user_demand": "init", "auto_approve": True},
    )
    state = FeatureOrchestratorAgent()(state)
    state = HumanApprovalCheckpoint()(state)
    assert "orchestrator" in state["results"]
    assert state["results"]["human_approval"]["content"]["approved"] is True
