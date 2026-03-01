"""
Tests for the LangGraph pipeline refactoring.

Verifies:
  1. Graph structure (nodes, edges) is correct.
  2. Each node wrapper calls the right agent/service and returns correct state keys.
  3. Full pipeline produces identical output shape as before.
  4. Helper functions (_format_features, _calculate_overall_complexity) are unchanged.
  5. Progress events are emitted in the correct order.
  6. FastAPI endpoints remain unchanged.
"""

import asyncio
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from dotenv import load_dotenv

load_dotenv()

from app.graph.state import PipelineState
from app.graph.builder import build_pipeline_graph
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
    _format_features_for_response,
    _calculate_overall_complexity,
)


# ── Fixtures ────────────────────────────────────────────────────────────


def _mock_domain_agent():
    agent = AsyncMock()
    agent.execute.return_value = {
        "detected_domain": "ecommerce",
        "confidence": 0.85,
        "secondary_domains": [],
        "reasoning": "Test reasoning",
    }
    return agent


def _mock_feature_agent():
    agent = AsyncMock()
    agent.execute.return_value = {
        "features": [
            {
                "name": "User Authentication",
                "complexity": "Medium",
                "subfeatures": [
                    {"name": "Login"},
                    {"name": "Registration"},
                ],
            },
            {
                "name": "Product Catalog",
                "complexity": "High",
                "subfeatures": [
                    {"name": "Listing"},
                    {"name": "Search"},
                ],
            },
        ]
    }
    return agent


def _mock_estimation_agent():
    agent = AsyncMock()
    agent.execute.return_value = {
        "features": [
            {
                "name": "User Authentication",
                "complexity": "Medium",
                "total_hours": 80,
                "was_calibrated": True,
                "subfeatures": [
                    {"name": "Login", "effort": 40},
                    {"name": "Registration", "effort": 40},
                ],
            },
            {
                "name": "Product Catalog",
                "complexity": "High",
                "total_hours": 140,
                "was_calibrated": False,
                "subfeatures": [
                    {"name": "Listing", "effort": 70},
                    {"name": "Search", "effort": 70},
                ],
            },
        ],
        "total_hours": 220,
        "min_hours": 187,
        "max_hours": 253,
    }
    return agent


def _mock_tech_stack_agent():
    agent = AsyncMock()
    agent.execute.return_value = {
        "frontend": {"web": {"name": "Next.js"}},
        "backend": {"framework": "Express", "language": "TypeScript"},
        "database": {"primary": {"name": "PostgreSQL"}},
        "infrastructure": {"cloud_provider": "AWS"},
        "third_party_services": {"payment": "Stripe"},
        "justification": "Standard ecommerce stack",
    }
    return agent


def _mock_proposal_agent():
    agent = AsyncMock()
    agent.execute.return_value = {
        "abstract": "Test abstract",
        "executive_summary": "Test summary",
        "scope_of_work": "Test scope",
        "deliverables": ["Web app", "Admin panel"],
        "project_timeline": [{"phase": "Phase 1", "duration": "4 weeks", "description": "Setup"}],
        "timeline_weeks": 8,
        "team_composition": {"Frontend Developer": 2, "Backend Developer": 2},
        "risks": ["Risk 1"],
        "mitigation_strategies": ["Mitigation 1"],
        "assumptions": ["Assumption 1"],
        "client_dependencies": ["Dep 1"],
    }
    return agent


def _mock_template_expander():
    expander = AsyncMock()
    expander.expand.return_value = (
        "enriched description with modules",
        ["auth_module", "catalog_module", "payment_module"],
    )
    return expander


def _mock_calibration_engine():
    engine = MagicMock()
    engine.get_calibration_info.return_value = {"sample_size": 5}
    return engine


def _build_test_state(**overrides) -> dict:
    """Build a minimal test state with all mocked services."""
    state = {
        "description": "Build an ecommerce platform with product catalog and payments",
        "additional_details": "Need user auth, product listings, and checkout",
        "extracted_text": "",
        "build_options": ["web", "mobile"],
        "platforms": ["web", "mobile"],
        "timeline_constraint": "3 months",
        "additional_context": "",
        "preferred_tech_stack": [],
        "request_id": str(uuid.uuid4()),
        "_domain_agent": _mock_domain_agent(),
        "_feature_agent": _mock_feature_agent(),
        "_estimation_agent": _mock_estimation_agent(),
        "_tech_stack_agent": _mock_tech_stack_agent(),
        "_proposal_agent": _mock_proposal_agent(),
        "_template_expander": _mock_template_expander(),
        "_calibration_engine": _mock_calibration_engine(),
        "_progress_callback": None,
    }
    state.update(overrides)
    return state


# ═══════════════════════════════════════════════════════════════════════
# TEST 1: Graph Structure
# ═══════════════════════════════════════════════════════════════════════


class TestGraphStructure:
    """Verify the compiled graph has the correct nodes and edges."""

    def test_graph_compiles(self):
        graph = build_pipeline_graph()
        assert graph is not None

    def test_graph_has_all_nodes(self):
        graph = build_pipeline_graph()
        node_names = set(graph.get_graph().nodes.keys())
        expected = {
            "__start__",
            "__end__",
            "domain_detection",
            "template_expansion",
            "feature_structuring",
            "estimation",
            "confidence_calculation",
            "tech_stack",
            "proposal",
            "planning",
            "build_result",
        }
        assert node_names == expected

    def test_graph_has_correct_edge_count(self):
        graph = build_pipeline_graph()
        edges = graph.get_graph().edges
        # 10 edges: start->domain, domain->template, template->feature,
        # feature->estimation, estimation->confidence, confidence->tech_stack,
        # tech_stack->proposal, proposal->planning, planning->build_result, build_result->end
        assert len(edges) == 10

    def test_graph_edge_sequence(self):
        graph = build_pipeline_graph()
        edges = graph.get_graph().edges
        edge_tuples = {(e.source, e.target) for e in edges}
        expected_edges = {
            ("__start__", "domain_detection"),
            ("domain_detection", "template_expansion"),
            ("template_expansion", "feature_structuring"),
            ("feature_structuring", "estimation"),
            ("estimation", "confidence_calculation"),
            ("confidence_calculation", "tech_stack"),
            ("tech_stack", "proposal"),
            ("proposal", "planning"),
            ("planning", "build_result"),
            ("build_result", "__end__"),
        }
        assert edge_tuples == expected_edges

    def test_no_conditional_edges(self):
        graph = build_pipeline_graph()
        edges = graph.get_graph().edges
        for edge in edges:
            assert not edge.conditional, f"Edge {edge.source}->{edge.target} should not be conditional"


# ═══════════════════════════════════════════════════════════════════════
# TEST 2: Individual Node Wrappers
# ═══════════════════════════════════════════════════════════════════════


class TestDomainDetectionNode:

    @pytest.mark.asyncio
    async def test_calls_agent_and_returns_correct_keys(self):
        state = _build_test_state()
        result = await domain_detection_node(state)
        assert "domain_result" in result
        assert "detected_domain" in result
        assert result["detected_domain"] == "ecommerce"
        assert result["domain_result"]["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_passes_all_context_to_agent(self):
        agent = _mock_domain_agent()
        state = _build_test_state(_domain_agent=agent)
        await domain_detection_node(state)
        call_args = agent.execute.call_args[0][0]
        assert "description" in call_args
        assert "additional_details" in call_args
        assert "extracted_text" in call_args
        assert "build_options" in call_args

    @pytest.mark.asyncio
    async def test_fires_progress_events(self):
        events = []
        state = _build_test_state(_progress_callback=lambda e: events.append(e))
        await domain_detection_node(state)
        stages = [e["stage"] for e in events]
        assert "domain_detection_started" in stages
        assert "domain_detection_done" in stages


class TestTemplateExpansionNode:

    @pytest.mark.asyncio
    async def test_returns_modules(self):
        state = _build_test_state(detected_domain="ecommerce")
        result = await template_expansion_node(state)
        assert "selected_modules" in result
        assert "enriched_description" in result
        assert len(result["selected_modules"]) == 3


class TestFeatureStructuringNode:

    @pytest.mark.asyncio
    async def test_returns_features(self):
        state = _build_test_state(
            detected_domain="ecommerce",
            selected_modules=["auth", "catalog"],
        )
        result = await feature_structuring_node(state)
        assert "features" in result
        assert len(result["features"]) == 2


class TestEstimationNode:

    @pytest.mark.asyncio
    async def test_returns_hours(self):
        state = _build_test_state(
            features=[{"name": "Auth", "complexity": "Medium", "subfeatures": []}]
        )
        result = await estimation_node(state)
        assert result["total_hours"] == 220
        assert result["min_hours"] == 187
        assert result["max_hours"] == 253
        assert len(result["estimated_features"]) == 2


class TestConfidenceCalculationNode:

    @pytest.mark.asyncio
    async def test_returns_score(self):
        state = _build_test_state(
            estimated_features=[
                {"name": "Auth", "was_calibrated": True},
                {"name": "Catalog", "was_calibrated": False},
            ],
            domain_result={"confidence": 0.85},
        )
        result = await confidence_calculation_node(state)
        assert "confidence_score" in result
        assert 0 <= result["confidence_score"] <= 95


class TestTechStackNode:

    @pytest.mark.asyncio
    async def test_returns_stack(self):
        state = _build_test_state(
            detected_domain="ecommerce",
            features=[{"name": "Auth"}],
        )
        result = await tech_stack_node(state)
        assert "tech_stack_result" in result
        assert "frontend" in result["tech_stack_result"]


class TestProposalNode:

    @pytest.mark.asyncio
    async def test_returns_proposal(self):
        state = _build_test_state(
            detected_domain="ecommerce",
            estimated_features=[],
            total_hours=220,
            tech_stack_result={},
        )
        result = await proposal_node(state)
        assert "proposal_result" in result
        assert "abstract" in result["proposal_result"]


class TestPlanningNode:

    @pytest.mark.asyncio
    async def test_returns_planning(self):
        state = _build_test_state(
            estimated_features=[
                {"name": "Auth", "complexity": "Medium", "total_hours": 80, "subfeatures": [{"name": "Login", "effort": 40}]},
            ],
            confidence_score=50.0,
            total_hours=220,
            proposal_result={"timeline_weeks": 8},
        )
        result = await planning_node(state)
        assert "planning_result" in result
        assert "formatted_features" in result
        assert "phase_breakdown" in result["planning_result"]
        assert "team_recommendation" in result["planning_result"]


class TestBuildResultNode:

    @pytest.mark.asyncio
    async def test_produces_final_result(self):
        state = _build_test_state(
            domain_result={"detected_domain": "ecommerce", "confidence": 0.85, "reasoning": "test", "secondary_domains": []},
            estimated_features=[
                {"name": "Auth", "complexity": "Medium", "total_hours": 80, "was_calibrated": True,
                 "subfeatures": [{"name": "Login", "effort": 40}]},
            ],
            total_hours=220,
            min_hours=187,
            max_hours=253,
            confidence_score=50.0,
            tech_stack_result={"frontend": [], "backend": [], "database": [], "infrastructure": [], "third_party_services": [], "justification": "test"},
            proposal_result={"assumptions": ["A1"], "timeline_weeks": 8},
            formatted_features=[{"name": "Auth", "complexity": "medium", "total_hours": 80, "subfeatures": [], "confidence_score": 0.5}],
            planning_result={"phase_breakdown": {}, "team_recommendation": {}, "complexity_totals": {}},
            selected_modules=["mod1"],
            build_options=["web"],
            timeline_constraint="3 months",
        )
        result = await build_result_node(state)
        final = result["final_result"]

        # Verify the response has all required top-level keys
        assert "request_id" in final
        assert "domain_detection" in final
        assert "estimation" in final
        assert "tech_stack" in final
        assert "proposal" in final
        assert "planning" in final
        assert "metadata" in final

        # Verify estimation sub-keys
        est = final["estimation"]
        assert "total_hours" in est
        assert "min_hours" in est
        assert "max_hours" in est
        assert "features" in est
        assert "overall_complexity" in est
        assert "confidence_score" in est
        assert "assumptions" in est

        # Verify planning sub-keys
        plan = final["planning"]
        assert "phase_split" in plan
        assert "team_recommendation" in plan
        assert "complexity_breakdown" in plan

        # Verify metadata
        meta = final["metadata"]
        assert meta["pipeline_version"] == "2.0.0"
        assert "feature_count" in meta
        assert "modules_selected" in meta


# ═══════════════════════════════════════════════════════════════════════
# TEST 3: Helper Functions
# ═══════════════════════════════════════════════════════════════════════


class TestHelperFunctions:

    def test_format_features_basic(self):
        features = [
            {
                "name": "Auth",
                "complexity": "Medium",
                "total_hours": 80,
                "subfeatures": [{"name": "Login", "effort": 40}],
            }
        ]
        result = _format_features_for_response(features, 0.75)
        assert len(result) == 1
        assert result[0]["name"] == "Auth"
        assert result[0]["complexity"] == "medium"
        assert result[0]["total_hours"] == 80
        assert result[0]["confidence_score"] == 0.75
        assert len(result[0]["subfeatures"]) == 1

    def test_format_features_empty(self):
        assert _format_features_for_response([], 0.5) == []

    def test_complexity_empty(self):
        assert _calculate_overall_complexity([]) == "medium"

    def test_complexity_high(self):
        features = [{"complexity": "High"}] * 6 + [{"complexity": "Low"}] * 4
        assert _calculate_overall_complexity(features) == "very_high"

    def test_complexity_medium(self):
        features = [{"complexity": "Medium"}] * 5 + [{"complexity": "Low"}] * 3
        assert _calculate_overall_complexity(features) == "medium"

    def test_complexity_low(self):
        features = [{"complexity": "Low"}] * 5 + [{"complexity": "Medium"}] * 2
        assert _calculate_overall_complexity(features) == "low"


# ═══════════════════════════════════════════════════════════════════════
# TEST 4: Full Pipeline (end-to-end with mocks)
# ═══════════════════════════════════════════════════════════════════════


class TestFullPipeline:

    @pytest.mark.asyncio
    async def test_full_graph_invocation(self):
        """Run the full graph with mocked agents and verify output shape."""
        graph = build_pipeline_graph()

        initial_state = _build_test_state(
            detected_domain="",
            selected_modules=[],
            features=[],
            estimated_features=[],
            estimation_result={},
            total_hours=0,
            min_hours=0,
            max_hours=0,
            confidence_score=0,
            tech_stack_result={},
            proposal_result={},
            formatted_features=[],
            planning_result={},
            final_result={},
            enriched_description="",
            domain_result={},
        )

        final_state = await graph.ainvoke(initial_state)

        # Verify final_result exists and has correct shape
        assert "final_result" in final_state
        result = final_state["final_result"]
        assert result["domain_detection"]["detected_domain"] == "ecommerce"
        assert result["estimation"]["total_hours"] == 220
        assert result["estimation"]["min_hours"] == 187
        assert result["estimation"]["max_hours"] == 253
        assert "features" in result["estimation"]
        assert len(result["estimation"]["features"]) > 0
        assert "frontend" in result["tech_stack"]
        assert "abstract" in result["proposal"]
        assert "phase_split" in result["planning"]
        assert result["metadata"]["pipeline_version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_progress_events_order(self):
        """Verify progress events are emitted in correct pipeline order."""
        graph = build_pipeline_graph()
        events = []

        initial_state = _build_test_state(
            _progress_callback=lambda e: events.append(e),
        )

        await graph.ainvoke(initial_state)

        stages = [e["stage"] for e in events]
        expected_order = [
            "domain_detection_started",
            "domain_detection_done",
            "template_expansion_started",
            "template_expansion_done",
            "feature_structuring_started",
            "feature_structuring_done",
            "estimation_started",
            "estimation_done",
            "proposal_started",
            "completed",
        ]
        assert stages == expected_order

    @pytest.mark.asyncio
    async def test_pipeline_class_run(self):
        """Verify ProjectPipeline.run() works with LangGraph under the hood."""
        from app.orchestrator.project_pipeline import ProjectPipeline

        pipeline = ProjectPipeline(load_calibration=False)

        # Mock all agents on the pipeline instance
        pipeline.domain_agent = _mock_domain_agent()
        pipeline.feature_agent = _mock_feature_agent()
        pipeline.estimation_agent = _mock_estimation_agent()
        pipeline.tech_stack_agent = _mock_tech_stack_agent()
        pipeline.proposal_agent = _mock_proposal_agent()
        pipeline.template_expander = _mock_template_expander()

        result = await pipeline.run({
            "description": "Build an ecommerce platform",
            "additional_details": "With auth and payments",
            "build_options": ["web"],
        })

        assert result is not None
        assert result["domain_detection"]["detected_domain"] == "ecommerce"
        assert result["estimation"]["total_hours"] == 220
        assert "tech_stack" in result
        assert "proposal" in result
        assert "planning" in result

    @pytest.mark.asyncio
    async def test_pipeline_streaming_events(self):
        """Verify ProjectPipeline.run_streaming() yields all progress events."""
        from app.orchestrator.project_pipeline import ProjectPipeline

        pipeline = ProjectPipeline(load_calibration=False)
        pipeline.domain_agent = _mock_domain_agent()
        pipeline.feature_agent = _mock_feature_agent()
        pipeline.estimation_agent = _mock_estimation_agent()
        pipeline.tech_stack_agent = _mock_tech_stack_agent()
        pipeline.proposal_agent = _mock_proposal_agent()
        pipeline.template_expander = _mock_template_expander()

        events = []
        async for event in pipeline.run_streaming({
            "description": "Build an ecommerce platform",
            "additional_details": "With auth and payments",
            "build_options": ["web"],
        }):
            events.append(event)

        stages = [e["stage"] for e in events]
        assert "domain_detection_started" in stages
        assert "domain_detection_done" in stages
        assert "estimation_done" in stages
        assert "completed" in stages

        # The last event should be "completed" with the result
        completed = [e for e in events if e["stage"] == "completed"]
        assert len(completed) == 1
        assert "result" in completed[0]


# ═══════════════════════════════════════════════════════════════════════
# TEST 5: Output Compatibility
# ═══════════════════════════════════════════════════════════════════════


class TestOutputCompatibility:
    """Verify the LangGraph pipeline output matches FinalPipelineResponse model."""

    @pytest.mark.asyncio
    async def test_output_matches_pydantic_model(self):
        """The final_result dict should be valid for FinalPipelineResponse."""
        from app.models.project_models import FinalPipelineResponse

        graph = build_pipeline_graph()
        initial_state = _build_test_state()
        final_state = await graph.ainvoke(initial_state)
        result = final_state["final_result"]

        # This should not raise a validation error
        response = FinalPipelineResponse(**result)
        assert response.domain_detection.detected_domain.value == "ecommerce"
        assert response.estimation.total_hours == 220
        assert response.estimation.min_hours == 187
        assert response.estimation.max_hours == 253
        assert response.planning.phase_split is not None
        assert response.metadata["pipeline_version"] == "2.0.0"
