"""
LangGraph graph construction and compilation for the estimation pipeline.

Defines the StateGraph with all nodes and edges, then compiles it.
The compiled graph is the single source of truth for orchestration.

Flow:
  START -> domain_detection -> template_expansion -> feature_structuring
        -> estimation -> confidence_calculation -> tech_stack
        -> proposal -> planning -> build_result -> END
"""

from langgraph.graph import StateGraph, START, END

from app.graph.state import PipelineState
from app.graph.nodes import (
    domain_detection_node,
    template_expansion_node,
    feature_structuring_node,
    estimation_node,
    confidence_calculation_node,
    tech_stack_node,
    proposal_node,
    planning_node,
    build_result_node,
)


def build_pipeline_graph() -> StateGraph:
    """
    Construct the estimation pipeline as a LangGraph StateGraph.

    All edges are sequential (no conditional branching in the main pipeline).
    Conditional logic (e.g. template fallback, MVP detection) is encapsulated
    inside the individual agent/service functions — not in the graph routing.

    Returns:
        Compiled StateGraph ready to be invoked with ainvoke().
    """
    graph = StateGraph(PipelineState)

    # ── Add nodes ───────────────────────────────────────────────────────
    # Each node wraps an existing agent/service function.
    graph.add_node("domain_detection", domain_detection_node)
    graph.add_node("template_expansion", template_expansion_node)
    graph.add_node("feature_structuring", feature_structuring_node)
    graph.add_node("estimation", estimation_node)
    graph.add_node("confidence_calculation", confidence_calculation_node)
    graph.add_node("tech_stack", tech_stack_node)
    graph.add_node("proposal", proposal_node)
    graph.add_node("planning", planning_node)
    graph.add_node("build_result", build_result_node)

    # ── Add edges (sequential pipeline) ─────────────────────────────────
    # START -> domain_detection -> template_expansion -> feature_structuring
    #       -> estimation -> confidence_calculation -> tech_stack
    #       -> proposal -> planning -> build_result -> END
    graph.add_edge(START, "domain_detection")
    graph.add_edge("domain_detection", "template_expansion")
    graph.add_edge("template_expansion", "feature_structuring")
    graph.add_edge("feature_structuring", "estimation")
    graph.add_edge("estimation", "confidence_calculation")
    graph.add_edge("confidence_calculation", "tech_stack")
    graph.add_edge("tech_stack", "proposal")
    graph.add_edge("proposal", "planning")
    graph.add_edge("planning", "build_result")
    graph.add_edge("build_result", END)

    # ── Compile ─────────────────────────────────────────────────────────
    compiled = graph.compile()

    return compiled
