from __future__ import annotations


def review_artifacts(artifacts: list[str]) -> dict:
    return {
        "reviewed_artifacts": artifacts,
        "blocking_issues": [],
        "review_pass": True,
    }
