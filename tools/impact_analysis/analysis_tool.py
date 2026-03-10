from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = ROOT / "config/spec/impact_analysis_template.json"
REGISTRY_PATH = ROOT / "config/spec/agent_contract_registry.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def analyze_impact(payload: dict[str, Any]) -> dict[str, Any]:
    template = _load_json(TEMPLATE_PATH)
    registry = _load_json(REGISTRY_PATH)
    valid_agents = {agent["name"] for agent in registry["agents"]}

    missing_keys = [key for key in template.keys() if key not in payload]
    unknown_agents = [agent for agent in payload.get("impacted_agents", []) if agent not in valid_agents]
    requires_block = bool(
        missing_keys
        or unknown_agents
        or payload.get("break_mvp_boundary", False)
        or payload.get("change_compliance_assumption", False)
    )

    return {
        "valid": not requires_block,
        "missing_keys": missing_keys,
        "unknown_agents": unknown_agents,
        "requires_block": requires_block,
    }


def main() -> int:
    sample = _load_json(TEMPLATE_PATH)
    result = analyze_impact(sample)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
