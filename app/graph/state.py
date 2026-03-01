"""
LangGraph state schema for the estimation pipeline.

This TypedDict captures ALL data flowing between pipeline stages.
Each node reads what it needs from state and writes its outputs back.
"""

from typing import Any, Dict, List, Optional, TypedDict, Callable


class PipelineState(TypedDict, total=False):
    """
    Shared state passed through every LangGraph node in the estimation pipeline.

    ── Inputs (set once from the /estimate request) ──────────────────────
    description:          Fused manual + extracted text (primary input).
    additional_details:   Original manual input from the user.
    extracted_text:       Text extracted from uploaded document.
    build_options:        Platforms to build (e.g. ["mobile", "web"]).
    platforms:            Lowercased/normalized build_options for tech stack.
    timeline_constraint:  Timeline string (e.g. "3 months").
    additional_context:   Extra context provided by user.
    preferred_tech_stack: User's preferred technologies.

    ── Stage 1: Domain Detection ─────────────────────────────────────────
    domain_result:        Full result dict from DomainDetectionAgent.
    detected_domain:      Extracted domain string (e.g. "ecommerce").

    ── Stage 2: Template Expansion ───────────────────────────────────────
    enriched_description: Description enriched with module context.
    selected_modules:     List of module names selected by template expander.

    ── Stage 3: Feature Structuring ──────────────────────────────────────
    features:             Raw features list from FeatureStructuringAgent.

    ── Stage 4: Estimation ───────────────────────────────────────────────
    estimation_result:    Full result dict from EstimationAgent.
    estimated_features:   Features with hours, calibration data.
    total_hours:          Nominal total hours.
    min_hours:            Minimum hours estimate (85%).
    max_hours:            Maximum hours estimate (115%).

    ── Stage 5: Confidence Calculation ───────────────────────────────────
    confidence_score:     Confidence score (0-95).

    ── Stage 6: Tech Stack ───────────────────────────────────────────────
    tech_stack_result:    Full result dict from TechStackAgent.

    ── Stage 7: Proposal ─────────────────────────────────────────────────
    proposal_result:      Full result dict from ProposalAgent.

    ── Stage 8: Planning ─────────────────────────────────────────────────
    formatted_features:   Features formatted for the response model.
    planning_result:      Full result dict from PlanningEngine.

    ── Final Output ──────────────────────────────────────────────────────
    request_id:           UUID for this pipeline run.
    final_result:         Complete pipeline response dict.

    ── Pipeline services (injected, not serialized) ──────────────────────
    _domain_agent:           DomainDetectionAgent instance.
    _feature_agent:          FeatureStructuringAgent instance.
    _estimation_agent:       EstimationAgent instance.
    _tech_stack_agent:       TechStackAgent instance.
    _proposal_agent:         ProposalAgent instance.
    _template_expander:      SmartTemplateExpander instance.
    _calibration_engine:     CalibrationEngine instance.
    _progress_callback:      Optional callback for streaming progress events.
    """

    # ── Inputs ──────────────────────────────────────────────────────────
    description: str
    additional_details: str
    extracted_text: str
    build_options: List[str]
    platforms: List[str]
    timeline_constraint: str
    additional_context: str
    preferred_tech_stack: List[str]

    # ── Stage 1 ─────────────────────────────────────────────────────────
    domain_result: Dict[str, Any]
    detected_domain: str

    # ── Stage 2 ─────────────────────────────────────────────────────────
    enriched_description: str
    selected_modules: List[str]

    # ── Stage 3 ─────────────────────────────────────────────────────────
    features: List[Dict[str, Any]]

    # ── Stage 4 ─────────────────────────────────────────────────────────
    estimation_result: Dict[str, Any]
    estimated_features: List[Dict[str, Any]]
    total_hours: float
    min_hours: float
    max_hours: float

    # ── Stage 5 ─────────────────────────────────────────────────────────
    confidence_score: float

    # ── Stage 6 ─────────────────────────────────────────────────────────
    tech_stack_result: Dict[str, Any]

    # ── Stage 7 ─────────────────────────────────────────────────────────
    proposal_result: Dict[str, Any]

    # ── Stage 8 ─────────────────────────────────────────────────────────
    formatted_features: List[Dict[str, Any]]
    planning_result: Dict[str, Any]

    # ── Final ───────────────────────────────────────────────────────────
    request_id: str
    final_result: Dict[str, Any]

    # ── Injected services (not serialized) ──────────────────────────────
    _domain_agent: Any
    _feature_agent: Any
    _estimation_agent: Any
    _tech_stack_agent: Any
    _proposal_agent: Any
    _template_expander: Any
    _calibration_engine: Any
    _progress_callback: Optional[Callable]
