from __future__ import annotations

from agents.final_gate import FinalGateAgent
from agents.governance import AuditAgent, CompliancePolicyAgent, EvaluationAgent, StandardsAgent
from graphs._compat import END, START, StateGraph, ensure_langgraph
from packages.schema.state import GraphState


def build_governance_graph():
    ensure_langgraph()
    graph = StateGraph(GraphState)
    graph.add_node("standards", StandardsAgent())
    graph.add_node("compliance_policy", CompliancePolicyAgent())
    graph.add_node("governance_audit", AuditAgent())
    graph.add_node("evaluation", EvaluationAgent())
    graph.add_node("final_gate", FinalGateAgent())

    graph.add_edge(START, "standards")
    graph.add_edge("standards", "compliance_policy")
    graph.add_edge("compliance_policy", "governance_audit")
    graph.add_edge("governance_audit", "evaluation")
    graph.add_edge("evaluation", "final_gate")
    graph.add_edge("final_gate", END)
    return graph.compile()
