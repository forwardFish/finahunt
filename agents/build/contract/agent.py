from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref
from packages.schema.state import GraphState


class ContractAgent(BaseAgent):
    agent_name = "Contract Agent"
    stage = "contract"

    def build_content(self, state: GraphState) -> dict:
        raw_document_schema = {
            "document_id": "string",
            "source_id": "string",
            "title": "string",
            "summary": "string",
            "published_at": "timestamp",
            "source_url": "string",
        }
        runtime_output_contract = {
            "document_id": "string",
            "title": "string",
            "summary": "string",
            "published_at": "timestamp",
            "source_name": "string",
            "trace_id": "string",
        }
        return {
            "raw_document_schema": raw_document_schema,
            "connector_contract": {
                "input": ["source_config", "fetch_window"],
                "output": ["raw_documents", "fetch_status_report"],
            },
            "runtime_output_contract": runtime_output_contract,
            "error_contract": {
                "error_type": "string",
                "error_msg": "string",
                "error_source": "string",
                "impact_scope": "string",
            },
            "contract_version": "v1",
            "artifact_refs": [artifact_ref("contracts", "runtime_contract.json")],
        }
