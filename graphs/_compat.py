from __future__ import annotations

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - optional until deps installed
    END = "__end__"
    START = "__start__"
    StateGraph = None


def ensure_langgraph() -> None:
    if StateGraph is None:  # pragma: no cover - runtime guard
        raise RuntimeError("langgraph is required. Install dependencies with `pip install -e .`.")
