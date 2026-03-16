from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from packages.utils import load_yaml


class SourceAuditAgent(BaseAgent):
    agent_name = "Source Audit Agent"
    stage = "source_audit"

    def build_content(self, state: GraphState) -> dict:
        traceability = load_yaml("config/spec/traceability.yaml")
        gates = load_yaml("config/spec/gate_registry.yaml")
        source_runtime = get_result(state, "source_runtime")
        compliance_guard = get_result(state, "compliance_guard")
        normalize = get_result(state, "normalize")

        trace_report = {
            "trace_id": state["metadata"]["trace_id"],
            "registry_version": source_runtime.get("registry_snapshot", {}).get("registry_version", "unknown"),
            "stages": ["source_runtime", "compliance_guard", "normalize", "source_audit"],
            "documents_seen": len(source_runtime.get("raw_documents", [])),
            "documents_allowed": len(compliance_guard.get("allowed_documents", [])),
            "documents_normalized": len(normalize.get("normalized_documents", [])),
        }

        return {
            "runtime_audit_log": artifact_ref("audit", "runtime_audit.log"),
            "trace_report": trace_report,
            "runtime_exception_summary": normalize.get("normalize_failure_record", []),
            "trace_matrix": [
                {
                    "goal": goal_id,
                    "config_refs": payload.get("config_refs", []),
                    "test_refs": payload.get("test_refs", []),
                }
                for goal_id, payload in traceability.get("goals", {}).items()
            ],
            "gate_registry_snapshot": [gate["gate_id"] for gate in gates.get("gates", [])],
            "artifact_refs": [artifact_ref("audit", "runtime_audit.log")],
        }
