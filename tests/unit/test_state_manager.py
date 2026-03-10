from packages.state_manager import StateManager


def test_new_state_has_required_fields():
    state = StateManager.new_state(graph_type="build", input_ref="demand://init")
    assert state["task_id"].startswith("task-")
    assert state["run_id"].startswith("run-")
    assert state["metadata"]["trace_id"].startswith("trace-")
