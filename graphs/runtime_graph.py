from __future__ import annotations

from agents.runtime import (
    CatalystClassificationAgent,
    DailyReviewAgent,
    EventExtractAgent,
    EventUnifyAgent,
    FermentingThemeFeedAgent,
    LowPositionDiscoveryAgent,
    NormalizeAgent,
    RelevanceRankingAgent,
    ResultWarehouseAgent,
    SourceAuditAgent,
    SourceComplianceGuardAgent,
    SourceScoutAgent,
    SourceRuntimeAgent,
    StockLinkageAgent,
    StructuredResultCardsAgent,
    ThemeClusterAgent,
    ThemeCandidateAggregationAgent,
    ThemeDetectionAgent,
    ThemeHeatSnapshotAgent,
)
from graphs._compat import END, START, StateGraph, ensure_langgraph
from packages.schema.state import GraphState


def build_runtime_graph():
    ensure_langgraph()
    graph = StateGraph(GraphState)
    graph.add_node("source_runtime", SourceRuntimeAgent())
    graph.add_node("compliance_guard", SourceComplianceGuardAgent())
    graph.add_node("source_scout", SourceScoutAgent())
    graph.add_node("normalize", NormalizeAgent())
    graph.add_node("event_extract", EventExtractAgent())
    graph.add_node("event_unify", EventUnifyAgent())
    graph.add_node("theme_detection", ThemeDetectionAgent())
    graph.add_node("catalyst_classification", CatalystClassificationAgent())
    graph.add_node("stock_linkage", StockLinkageAgent())
    graph.add_node("theme_cluster", ThemeClusterAgent())
    graph.add_node("theme_candidate_aggregation", ThemeCandidateAggregationAgent())
    graph.add_node("structured_result_cards", StructuredResultCardsAgent())
    graph.add_node("theme_heat_snapshot", ThemeHeatSnapshotAgent())
    graph.add_node("low_position_discovery", LowPositionDiscoveryAgent())
    graph.add_node("fermenting_theme_feed", FermentingThemeFeedAgent())
    graph.add_node("relevance_ranking", RelevanceRankingAgent())
    graph.add_node("daily_review", DailyReviewAgent())
    graph.add_node("result_warehouse", ResultWarehouseAgent())
    graph.add_node("source_audit", SourceAuditAgent())

    graph.add_edge(START, "source_runtime")
    graph.add_edge("source_runtime", "compliance_guard")
    graph.add_edge("compliance_guard", "source_scout")
    graph.add_edge("source_scout", "normalize")
    graph.add_edge("normalize", "event_extract")
    graph.add_edge("event_extract", "event_unify")
    graph.add_edge("event_unify", "theme_detection")
    graph.add_edge("theme_detection", "catalyst_classification")
    graph.add_edge("catalyst_classification", "stock_linkage")
    graph.add_edge("stock_linkage", "theme_cluster")
    graph.add_edge("theme_cluster", "theme_candidate_aggregation")
    graph.add_edge("theme_candidate_aggregation", "structured_result_cards")
    graph.add_edge("structured_result_cards", "theme_heat_snapshot")
    graph.add_edge("theme_heat_snapshot", "low_position_discovery")
    graph.add_edge("low_position_discovery", "fermenting_theme_feed")
    graph.add_edge("fermenting_theme_feed", "relevance_ranking")
    graph.add_edge("relevance_ranking", "daily_review")
    graph.add_edge("daily_review", "result_warehouse")
    graph.add_edge("result_warehouse", "source_audit")
    graph.add_edge("source_audit", END)
    return graph.compile()
