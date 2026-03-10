from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState


class ArchitectureAgent(BaseAgent):
    agent_name = "Architecture Agent"
    stage = "architecture"

    def build_content(self, state: GraphState) -> dict:
        return {
            "architecture_spec": {
                "pattern": "three-plane agent architecture",
                "graphs": [
                    "graphs/build_graph.py",
                    "graphs/runtime_graph.py",
                    "graphs/governance_graph.py",
                ],
                "workflow_entrypoints": [
                    "workflows/build_workflow.py",
                    "workflows/runtime_schedule.py",
                ],
            },
            "module_boundary": {
                "build": "feature delivery and release",
                "runtime": "fetch, compliance guard, normalization, audit",
                "governance": "standards, compliance policy, audit, evaluation",
            },
            "data_flow_design": [
                "source_registry -> source_runtime",
                "raw_document -> compliance_guard -> normalize",
                "build/runtime outputs -> governance -> final_gate",
            ],
            "failure_strategy": {
                "transient": "retry",
                "deterministic": "block and record",
                "policy": "block immediately",
                "external_change": "return to source registry",
            },
            "deploy_architecture_draft": {
                "agent_runtime": "python service",
                "checkpoint_store": "filesystem dev / postgres target",
                "audit_store": "append-only local file",
            },
            "artifact_refs": [artifact_ref("build", "architecture_spec.json")],
        }
