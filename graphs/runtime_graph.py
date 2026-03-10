from __future__ import annotations

from agents.runtime import NormalizeAgent, SourceAuditAgent, SourceComplianceGuardAgent, SourceRuntimeAgent
from graphs._compat import END, START, StateGraph, ensure_langgraph
from packages.schema.state import GraphState


def build_runtime_graph():
    ensure_langgraph()
    graph = StateGraph(GraphState)
    graph.add_node("source_runtime", SourceRuntimeAgent())
    graph.add_node("compliance_guard", SourceComplianceGuardAgent())
    graph.add_node("normalize", NormalizeAgent())
    graph.add_node("source_audit", SourceAuditAgent())

    graph.add_edge(START, "source_runtime")
    graph.add_edge("source_runtime", "compliance_guard")
    graph.add_edge("compliance_guard", "normalize")
    graph.add_edge("normalize", "source_audit")
    graph.add_edge("source_audit", END)
    return graph.compile()
