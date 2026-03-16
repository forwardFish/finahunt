from __future__ import annotations

from agents.runtime import (
    CatalystClassificationAgent,
    DailyReviewAgent,
    EventExtractAgent,
    EventUnifyAgent,
    NormalizeAgent,
    RelevanceRankingAgent,
    SourceAuditAgent,
    SourceComplianceGuardAgent,
    SourceRuntimeAgent,
    StockLinkageAgent,
    ThemeDetectionAgent,
)
from graphs._compat import END, START, StateGraph, ensure_langgraph
from packages.schema.state import GraphState


def build_runtime_graph():
    ensure_langgraph()
    graph = StateGraph(GraphState)
    graph.add_node("source_runtime", SourceRuntimeAgent())
    graph.add_node("compliance_guard", SourceComplianceGuardAgent())
    graph.add_node("normalize", NormalizeAgent())
    graph.add_node("event_extract", EventExtractAgent())
    graph.add_node("event_unify", EventUnifyAgent())
    graph.add_node("theme_detection", ThemeDetectionAgent())
    graph.add_node("catalyst_classification", CatalystClassificationAgent())
    graph.add_node("stock_linkage", StockLinkageAgent())
    graph.add_node("relevance_ranking", RelevanceRankingAgent())
    graph.add_node("daily_review", DailyReviewAgent())
    graph.add_node("source_audit", SourceAuditAgent())

    graph.add_edge(START, "source_runtime")
    graph.add_edge("source_runtime", "compliance_guard")
    graph.add_edge("compliance_guard", "normalize")
    graph.add_edge("normalize", "event_extract")
    graph.add_edge("event_extract", "event_unify")
    graph.add_edge("event_unify", "theme_detection")
    graph.add_edge("theme_detection", "catalyst_classification")
    graph.add_edge("catalyst_classification", "stock_linkage")
    graph.add_edge("stock_linkage", "relevance_ranking")
    graph.add_edge("relevance_ranking", "daily_review")
    graph.add_edge("daily_review", "source_audit")
    graph.add_edge("source_audit", END)
    return graph.compile()
