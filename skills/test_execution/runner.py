from __future__ import annotations


def run_test_suite(test_targets: list[str]) -> dict:
    return {
        "targets": test_targets,
        "passed": True,
        "reports": [f"report://{target}" for target in test_targets],
    }
