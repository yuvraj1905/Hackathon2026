"""
LangGraph node wrapper functions for the estimation pipeline.

Each function is a thin adapter that:
  1. Reads specific inputs from the shared PipelineState.
  2. Calls the original agent/service function (logic is NOT duplicated).
  3. Writes outputs back into state.
  4. Optionally fires a progress callback for streaming.

The original agent functions (DomainDetectionAgent.execute, etc.) are
called exactly as they were in the old ProjectPipeline — no internal
logic changes.
"""

import uuid
import logging
from typing import Dict, Any

from app.graph.state import PipelineState
from app.services.confidence_engine import ConfidenceEngine
from app.services.planning_engine import PlanningEngine

logger = logging.getLogger(__name__)


def _fire_progress(state: PipelineState, event: Dict[str, Any]) -> None:
    """Fire a progress callback if one was injected into state."""
    cb = state.get("_progress_callback")
    if cb is not None:
        cb(event)


async def domain_detection_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 1: Detect the project domain (ecommerce, fintech, etc.).

    Reads: description, additional_details, extracted_text, build_options,
           timeline_constraint, additional_context, _domain_agent.
    Writes: domain_result, detected_domain.
    """
    _fire_progress(state, {"stage": "domain_detection_started"})

    agent = state["_domain_agent"]
    domain_result = await agent.execute({
        "description": state.get("description", ""),
        "additional_details": state.get("additional_details", ""),
        "extracted_text": state.get("extracted_text", ""),
        "build_options": state.get("build_options", []),
        "timeline_constraint": state.get("timeline_constraint", ""),
        "additional_context": state.get("additional_context", ""),
    })

    detected_domain = domain_result.get("detected_domain", "unknown")

    _fire_progress(state, {
        "stage": "domain_detection_done",
        "domain": detected_domain,
        "confidence": domain_result.get("confidence"),
        "reasoning": domain_result.get("reasoning", ""),
    })

    return {
        "domain_result": domain_result,
        "detected_domain": detected_domain,
    }


async def template_expansion_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 2: Select relevant domain modules via smart template expansion.

    Uses LLM to pick relevant modules from domain templates, or falls back
    to LLM-generated modules for unknown domains.

    Reads: detected_domain, description, build_options, additional_context,
           _template_expander.
    Writes: enriched_description, selected_modules.
    """
    _fire_progress(state, {"stage": "template_expansion_started"})

    expander = state["_template_expander"]
    enriched_description, selected_modules = await expander.expand(
        domain=state["detected_domain"],
        description=state.get("description", ""),
        build_options=state.get("build_options", []),
        additional_context=state.get("additional_context", ""),
    )

    _fire_progress(state, {
        "stage": "template_expansion_done",
        "modules_selected": len(selected_modules),
        "modules": selected_modules,
    })

    return {
        "enriched_description": enriched_description,
        "selected_modules": selected_modules,
    }


async def feature_structuring_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 3: Extract and structure features from requirements.

    Reads: additional_details, extracted_text, selected_modules,
           build_options, detected_domain, _feature_agent.
    Writes: features.
    """
    _fire_progress(state, {"stage": "feature_structuring_started"})

    agent = state["_feature_agent"]
    feature_result = await agent.execute({
        "additional_details": state.get("additional_details", ""),
        "extracted_text": state.get("extracted_text", ""),
        "selected_modules": state.get("selected_modules", []),
        "build_options": state.get("build_options", []),
        "domain": state["detected_domain"],
    })

    features = feature_result.get("features", [])

    _fire_progress(state, {
        "stage": "feature_structuring_done",
        "feature_count": len(features),
    })

    return {"features": features}


async def estimation_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 4: Estimate hours per feature using calibration engine.

    Reads: features, description, _estimation_agent.
    Writes: estimation_result, estimated_features, total_hours, min_hours, max_hours.
    """
    _fire_progress(state, {"stage": "estimation_started"})

    agent = state["_estimation_agent"]
    estimation_result = await agent.execute({
        "features": state.get("features", []),
        "original_description": state.get("description", ""),
    })

    estimated_features = estimation_result.get("features", [])
    total_hours = estimation_result.get("total_hours", 0)
    min_hours = estimation_result.get("min_hours", 0)
    max_hours = estimation_result.get("max_hours", 0)

    _fire_progress(state, {
        "stage": "estimation_done",
        "total_hours": total_hours,
        "feature_count": len(estimated_features),
    })

    return {
        "estimation_result": estimation_result,
        "estimated_features": estimated_features,
        "total_hours": total_hours,
        "min_hours": min_hours,
        "max_hours": max_hours,
    }


async def confidence_calculation_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 5: Calculate confidence score from calibration coverage.

    Uses ConfidenceEngine (stateless) — no LLM call.

    Reads: estimated_features, domain_result, _calibration_engine.
    Writes: confidence_score.
    """
    confidence_score = ConfidenceEngine.calculate_confidence(
        state.get("estimated_features", []),
        state.get("domain_result", {}).get("confidence", 0.5),
        state.get("_calibration_engine"),
    )

    return {"confidence_score": confidence_score}


async def tech_stack_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 6: Recommend technology stack for the project.

    Reads: detected_domain, features, platforms, _tech_stack_agent.
    Writes: tech_stack_result.
    """
    agent = state["_tech_stack_agent"]
    tech_stack_result = await agent.execute({
        "domain": state["detected_domain"],
        "features": state.get("features", []),
        "platforms": state.get("platforms", []),
    })

    return {"tech_stack_result": tech_stack_result}


async def proposal_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 7: Generate client-ready proposal sections via LLM.

    Reads: detected_domain, estimated_features, total_hours, tech_stack_result,
           timeline_constraint, description, additional_details, _proposal_agent.
    Writes: proposal_result.
    """
    _fire_progress(state, {"stage": "proposal_started"})

    agent = state["_proposal_agent"]
    proposal_result = await agent.execute({
        "domain": state["detected_domain"],
        "features": state.get("estimated_features", []),
        "total_hours": state.get("total_hours", 0),
        "tech_stack": state.get("tech_stack_result", {}),
        "timeline_constraint": state.get("timeline_constraint", ""),
        "description": state.get("description", ""),
        "additional_details": state.get("additional_details", ""),
    })

    return {"proposal_result": proposal_result}


async def planning_node(state: PipelineState) -> Dict[str, Any]:
    """
    Stage 8: Compute deterministic planning breakdown (phases, team, complexity).

    Also formats features for the final response model.

    Reads: estimated_features, confidence_score, total_hours, proposal_result.
    Writes: formatted_features, planning_result.
    """
    confidence_score = state.get("confidence_score", 0)
    estimated_features = state.get("estimated_features", [])

    # Format features for the response model (same logic as _format_features_for_response)
    formatted_features = _format_features_for_response(
        estimated_features, confidence_score / 100
    )

    proposal_result = state.get("proposal_result", {})
    total_hours = state.get("total_hours", 0)

    planning_result = PlanningEngine.compute_planning(
        total_hours=total_hours,
        timeline_weeks=proposal_result.get("timeline_weeks", total_hours / 40),
        features=formatted_features,
    )

    return {
        "formatted_features": formatted_features,
        "planning_result": planning_result,
    }


async def build_result_node(state: PipelineState) -> Dict[str, Any]:
    """
    Final node: Assemble the complete pipeline response from all stage outputs.

    Reads: All stage outputs.
    Writes: final_result.
    """
    request_id = state.get("request_id", str(uuid.uuid4()))
    estimated_features = state.get("estimated_features", [])
    confidence_score = state.get("confidence_score", 0)
    proposal_result = state.get("proposal_result", {})
    selected_modules = state.get("selected_modules", [])
    build_options = state.get("build_options", [])
    timeline_constraint = state.get("timeline_constraint", "")

    final_result = {
        "request_id": request_id,
        "domain_detection": state.get("domain_result", {}),
        "estimation": {
            "total_hours": state.get("total_hours", 0),
            "min_hours": state.get("min_hours", 0),
            "max_hours": state.get("max_hours", 0),
            "features": state.get("formatted_features", []),
            "overall_complexity": _calculate_overall_complexity(estimated_features),
            "confidence_score": round(confidence_score / 100, 2),
            "assumptions": proposal_result.get("assumptions", [
                "Estimates include 15% buffer for unforeseen complexity",
                "Assumes standard development practices and code quality",
                "Third-party API integrations assumed to have stable documentation",
            ]),
        },
        "tech_stack": state.get("tech_stack_result", {}),
        "proposal": proposal_result,
        "planning": {
            "phase_split": state.get("planning_result", {}).get("phase_breakdown", {}),
            "team_recommendation": state.get("planning_result", {}).get("team_recommendation", {}),
            "complexity_breakdown": state.get("planning_result", {}).get("complexity_totals", {}),
        },
        "metadata": {
            "pipeline_version": "2.0.0",
            "feature_count": len(estimated_features),
            "modules_selected": len(selected_modules),
            "calibrated_features": sum(
                1 for f in estimated_features if f.get("was_calibrated", False)
            ),
            "calibration_coverage": round(
                sum(1 for f in estimated_features if f.get("was_calibrated", False))
                / len(estimated_features) * 100
                if len(estimated_features) > 0
                else 0,
                1,
            ),
            "build_options": build_options,
            "timeline_constraint": timeline_constraint,
        },
    }

    _fire_progress(state, {"stage": "completed", "result": final_result})

    return {"final_result": final_result}


# ── Helper functions (moved from ProjectPipeline, logic unchanged) ──────


def _format_features_for_response(
    estimated_features: list,
    overall_confidence: float,
) -> list:
    """
    Transform estimation agent output to match Feature model schema.

    This is the exact same logic as ProjectPipeline._format_features_for_response.
    """
    formatted = []
    for feature in estimated_features:
        subfeatures = []
        for sf in feature.get("subfeatures", []):
            subfeatures.append({
                "name": sf.get("name", ""),
                "effort": sf.get("effort", 0.0),
            })
        formatted.append({
            "name": feature.get("name", ""),
            "complexity": feature.get("complexity", "Medium").lower(),
            "total_hours": feature.get("total_hours", 0.0),
            "subfeatures": subfeatures,
            "confidence_score": round(overall_confidence, 2),
        })
    return formatted


def _calculate_overall_complexity(features: list) -> str:
    """
    Calculate overall project complexity based on feature distribution.

    This is the exact same logic as ProjectPipeline._calculate_overall_complexity.
    """
    if not features:
        return "medium"

    complexity_counts = {"low": 0, "medium": 0, "high": 0}
    for feature in features:
        complexity = feature.get("complexity", "Medium").lower()
        if complexity in complexity_counts:
            complexity_counts[complexity] += 1

    total = len(features)
    high_ratio = complexity_counts["high"] / total if total > 0 else 0

    if high_ratio > 0.4 or complexity_counts["high"] > 5:
        return "very_high"
    elif high_ratio > 0.2 or complexity_counts["high"] > 2:
        return "high"
    elif complexity_counts["medium"] > complexity_counts["low"]:
        return "medium"
    else:
        return "low"
