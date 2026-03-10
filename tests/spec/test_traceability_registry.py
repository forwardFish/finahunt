import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_traceability_sources_exist():
    traceability = yaml.safe_load((ROOT / "config/spec/traceability.yaml").read_text(encoding="utf-8"))
    for source in traceability["canonical_sources"].values():
        assert (ROOT / source).exists(), source


def test_agent_contract_registry_has_core_fields():
    registry = json.loads((ROOT / "config/spec/agent_contract_registry.json").read_text(encoding="utf-8"))
    assert len(registry["agents"]) >= 18
    for agent in registry["agents"]:
        assert agent["name"]
        assert agent["module"]
        assert agent["class_name"]
        assert agent["input_contract"]
        assert agent["output_contract"]
