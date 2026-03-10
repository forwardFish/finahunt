from __future__ import annotations


def evaluate_content(text: str, blocked_terms: list[str]) -> dict:
    violations = [term for term in blocked_terms if term in text]
    return {
        "passed": not violations,
        "violations": violations,
    }
