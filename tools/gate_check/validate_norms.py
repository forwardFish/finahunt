from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.schema.models import SourceRegistryEntry


def _load_yaml(path: str) -> dict[str, Any]:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def _load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _path_exists(path: str) -> bool:
    return (ROOT / path).exists()


def build_validation_report() -> dict[str, Any]:
    traceability = _load_yaml("config/spec/traceability.yaml")
    gates = _load_yaml("config/spec/gate_registry.yaml")
    registry = _load_json("config/spec/agent_contract_registry.json")
    source_registry = _load_yaml("config/rules/source_registry.yaml")

    missing_files: list[str] = []
    import_errors: list[str] = []
    contract_errors: list[str] = []
    registry_errors: list[str] = []

    for _, source_path in traceability["canonical_sources"].items():
        if not _path_exists(source_path):
            missing_files.append(source_path)

    for gate in gates["gates"]:
        for required in gate.get("required_files", []):
            if not _path_exists(required):
                missing_files.append(required)
        if not gate.get("gate_id"):
            contract_errors.append("gate_id missing")
        if not gate.get("blocking_conditions"):
            contract_errors.append(f"{gate.get('gate_id', 'unknown')}: blocking_conditions missing")

    for agent in registry["agents"]:
        module_name = agent["module"]
        class_name = agent["class_name"]
        for path in agent.get("config_refs", []):
            if not _path_exists(path):
                missing_files.append(path)
        for path in agent.get("test_refs", []):
            if not _path_exists(path):
                missing_files.append(path)
        if not agent.get("input_contract") or not agent.get("output_contract"):
            contract_errors.append(agent["name"])
        try:
            module = importlib.import_module(module_name)
            getattr(module, class_name)
        except Exception as exc:  # pragma: no cover - defensive
            import_errors.append(f"{module_name}.{class_name}: {exc}")

    for item in source_registry.get("sources", []):
        try:
            SourceRegistryEntry.model_validate(item)
        except Exception as exc:  # pragma: no cover - defensive
            registry_errors.append(f"{item.get('source_id', 'unknown')}: {exc}")

    report = {
        "passed": not missing_files and not import_errors and not contract_errors and not registry_errors,
        "missing_files": sorted(set(missing_files)),
        "import_errors": import_errors,
        "contract_errors": contract_errors,
        "registry_errors": registry_errors,
        "agent_count": len(registry["agents"]),
        "gate_count": len(gates["gates"]),
    }
    return report


def main() -> int:
    report = build_validation_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
