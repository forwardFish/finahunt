from __future__ import annotations

from agents.approval import HumanApprovalCheckpoint
from agents.build import (
    ArchitectureAgent,
    BuildSummaryAgent,
    ComplianceRulesAgent,
    ContractAgent,
    DeployStagingAgent,
    DevelopmentAgent,
    FeatureOrchestratorAgent,
    ReleaseAgent,
    RequirementParsingAgent,
    ReviewAgent,
    SourceRegistryAgent,
    TestAgent,
)
from graphs._compat import END, START, StateGraph, ensure_langgraph
from packages.schema.state import GraphState


def _after_review(state: GraphState) -> str:
    review_pass = state["results"]["review"]["content"].get("review_pass", False)
    return "test" if review_pass else "development"


def _after_test(state: GraphState) -> str:
    test_pass = state["results"]["test"]["content"].get("test_pass", False)
    return "deploy_staging" if test_pass else "development"


def _after_staging(state: GraphState) -> str:
    deploy_pass = state["results"]["deploy_staging"]["content"].get("deploy_pass", False)
    return "human_approval" if deploy_pass else "development"


def _after_approval(state: GraphState) -> str:
    approved = state["results"]["human_approval"]["content"].get("approved", False)
    return "release" if approved else "development"


def _after_release(state: GraphState) -> str:
    released = state["results"]["release"]["content"].get("release_pass", False)
    return "build_summary" if released else "deploy_staging"


def build_build_graph():
    ensure_langgraph()
    graph = StateGraph(GraphState)
    graph.add_node("orchestrator", FeatureOrchestratorAgent())
    graph.add_node("requirement_parsing", RequirementParsingAgent())
    graph.add_node("compliance_rules", ComplianceRulesAgent())
    graph.add_node("source_registry", SourceRegistryAgent())
    graph.add_node("architecture", ArchitectureAgent())
    graph.add_node("contract", ContractAgent())
    graph.add_node("development", DevelopmentAgent())
    graph.add_node("review", ReviewAgent())
    graph.add_node("test", TestAgent())
    graph.add_node("deploy_staging", DeployStagingAgent())
    graph.add_node("human_approval", HumanApprovalCheckpoint())
    graph.add_node("release", ReleaseAgent())
    graph.add_node("build_summary", BuildSummaryAgent())

    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", "requirement_parsing")
    graph.add_edge("requirement_parsing", "compliance_rules")
    graph.add_edge("compliance_rules", "source_registry")
    graph.add_edge("source_registry", "architecture")
    graph.add_edge("architecture", "contract")
    graph.add_edge("contract", "development")
    graph.add_edge("development", "review")
    graph.add_conditional_edges("review", _after_review)
    graph.add_conditional_edges("test", _after_test)
    graph.add_conditional_edges("deploy_staging", _after_staging)
    graph.add_conditional_edges("human_approval", _after_approval)
    graph.add_conditional_edges("release", _after_release)
    graph.add_edge("build_summary", END)
    return graph.compile()
