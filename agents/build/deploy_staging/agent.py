from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState


class DeployStagingAgent(BaseAgent):
    agent_name = "Deploy Staging Agent"
    stage = "deploy_staging"

    def build_content(self, state: GraphState) -> dict:
        return {
            "staging_deploy_report": {
                "environment": "staging",
                "deployment_status": "ready",
            },
            "smoke_test_result": "passed",
            "monitor_config": {
                "logs": "workspace/logs",
                "audit": "workspace/audit",
            },
            "deploy_pass": True,
            "artifact_refs": [artifact_ref("deploy", "staging_report.json")],
        }
