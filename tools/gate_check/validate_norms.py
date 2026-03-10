from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]


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

    missing_files: list[str] = []
    import_errors: list[str] = []
    contract_errors: list[str] = []

    for _, source_path in traceability["canonical_sources"].items():
        if not _path_exists(source_path):
            missing_files.append(source_path)

    for gate in gates["gates"]:
        for required in gate.get("required_files", []):
            if not _path_exists(required):
                missing_files.append(required)

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

    report = {
        "passed": not missing_files and not import_errors and not contract_errors,
        "missing_files": sorted(set(missing_files)),
        "import_errors": import_errors,
        "contract_errors": contract_errors,
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
