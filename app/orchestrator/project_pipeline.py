from typing import Dict, Any, AsyncGenerator, Optional, Callable, List
import uuid
from app.agents.domain_detection_agent import DomainDetectionAgent
from app.agents.feature_structuring_agent import FeatureStructuringAgent
from app.agents.estimation_agent import EstimationAgent
from app.agents.tech_stack_agent import TechStackAgent
from app.agents.proposal_agent import ProposalAgent
from app.services.template_expander import SmartTemplateExpander
from app.services.calibration_engine import CalibrationEngine
from app.services.confidence_engine import ConfidenceEngine
from app.services.planning_engine import PlanningEngine
from app.services.csv_calibration_loader import CSVCalibrationLoader
import logging

logger = logging.getLogger(__name__)


class ProjectPipeline:
    
    def __init__(self, load_calibration: bool = True):
        self.calibration_engine = CalibrationEngine()
        
        if load_calibration:
            try:
                loader = CSVCalibrationLoader()
                calibration_data = loader.load_all_calibrations()
                self.calibration_engine.load_from_aggregated_data(calibration_data)
            except Exception as e:
                logger.warning(f"Failed to load calibration data: {str(e)}")
        
        self.domain_agent = DomainDetectionAgent()
        self.feature_agent = FeatureStructuringAgent()
        self.estimation_agent = EstimationAgent(
            calibration_engine=self.calibration_engine
        )
        self.tech_stack_agent = TechStackAgent()
        self.proposal_agent = ProposalAgent()
        self.template_expander = SmartTemplateExpander()
    
    async def run(self, project_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute full estimation pipeline (non-streaming).

        Args:
            project_input: Dict with 'description'; optional 'additional_context', 
                          'preferred_tech_stack', 'build_options', 'timeline_constraint',
                          'additional_details', 'extracted_text'.

        Returns:
            Complete pipeline response
        """
        result = None
        
        async for event in self.run_streaming(project_input):
            if event.get("stage") == "completed":
                result = event.get("result")
        
        return result
    
    async def run_streaming(
        self,
        project_input: Dict[str, Any],
        progress_callback: Optional[Callable[[str, Dict], None]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute pipeline with streaming progress updates.

        Args:
            project_input: Dict with 'description'; optional 'additional_context', 
                          'preferred_tech_stack', 'build_options', 'timeline_constraint',
                          'additional_details', 'extracted_text'.
            progress_callback: Optional callback for progress events.

        Yields:
            Progress events and final result
        """
        request_id = str(uuid.uuid4())
        
        # Extract all context from input
        description = project_input.get("description", "")
        build_options = project_input.get("build_options", [])
        timeline_constraint = project_input.get("timeline_constraint", "")
        additional_context = project_input.get("additional_context", "")
        preferred_tech_stack = project_input.get("preferred_tech_stack", [])
        additional_details = project_input.get("additional_details", "")
        extracted_text = project_input.get("extracted_text", "")
        
        # ========== STAGE 1: Domain Detection ==========
        yield {"stage": "domain_detection_started"}
        
        # Pass ALL context to domain detection for better classification
        domain_result = await self.domain_agent.execute({
            "description": description,
            "additional_details": additional_details,
            "extracted_text": extracted_text,
            "build_options": build_options,
            "timeline_constraint": timeline_constraint,
            "additional_context": additional_context,
        })
        
        detected_domain = domain_result.get("detected_domain", "unknown")
        
        yield {
            "stage": "domain_detection_done",
            "domain": detected_domain,
            "confidence": domain_result.get("confidence"),
            "reasoning": domain_result.get("reasoning", "")
        }
        
        # ========== STAGE 2: Smart Template Expansion ==========
        yield {"stage": "template_expansion_started"}
        
        # Pass context to smart template expander for intelligent module selection
        # Note: timeline_constraint is NOT passed here - it's used later for proposal/planning
        enriched_description, selected_modules = await self.template_expander.expand(
            domain=detected_domain,
            description=description,
            build_options=build_options,
            additional_context=additional_context,
        )
        
        yield {
            "stage": "template_expansion_done",
            "modules_selected": len(selected_modules),
            "modules": selected_modules
        }
        
        # ========== STAGE 3: Feature Structuring ==========
        yield {"stage": "feature_structuring_started"}
        
        feature_result = await self.feature_agent.execute({
            "additional_details": additional_details,
            "extracted_text": extracted_text,
            "selected_modules": selected_modules,
            "build_options": build_options,
            "domain": detected_domain,
        })
        
        features = feature_result.get("features", [])
        
        yield {
            "stage": "feature_structuring_done",
            "feature_count": len(features)
        }
        
        # ========== STAGE 4: Estimation ==========
        yield {"stage": "estimation_started"}
        
        estimation_result = await self.estimation_agent.execute({
            "features": features,
            "original_description": description
        })
        
        estimated_features = estimation_result.get("features", [])
        total_hours = estimation_result.get("total_hours", 0)
        min_hours = estimation_result.get("min_hours", 0)
        max_hours = estimation_result.get("max_hours", 0)
        
        yield {
            "stage": "estimation_done",
            "total_hours": total_hours,
            "feature_count": len(estimated_features)
        }
        
        # ========== STAGE 5: Confidence Calculation ==========
        confidence_score = ConfidenceEngine.calculate_confidence(
            estimated_features,
            domain_result.get("confidence", 0.5),
            self.calibration_engine
        )
        
        # ========== STAGE 6: Tech Stack ==========
        tech_stack_result = await self.tech_stack_agent.execute({
            "domain": detected_domain,
            "features": features,
            "preferred_tech_stack": preferred_tech_stack,
        })
        
        # ========== STAGE 7: Proposal ==========
        yield {"stage": "proposal_started"}
        
        proposal_result = await self.proposal_agent.execute({
            "domain": detected_domain,
            "features": estimated_features,
            "total_hours": total_hours,
            "tech_stack": tech_stack_result,
            "timeline_constraint": timeline_constraint,
        })
        
        # ========== STAGE 8: Planning ==========
        formatted_features = self._format_features_for_response(
            estimated_features,
            confidence_score / 100
        )
        
        planning_result = PlanningEngine.compute_planning(
            total_hours=total_hours,
            timeline_weeks=proposal_result.get("timeline_weeks", total_hours / 40),
            features=formatted_features
        )
        
        # ========== Build Final Result ==========
        final_result = {
            "request_id": request_id,
            "domain_detection": domain_result,
            "estimation": {
                "total_hours": total_hours,
                "min_hours": min_hours,
                "max_hours": max_hours,
                "features": formatted_features,
                "overall_complexity": self._calculate_overall_complexity(estimated_features),
                "confidence_score": round(confidence_score / 100, 2),
                "assumptions": [
                    "Estimates include 15% buffer for unforeseen complexity",
                    "Assumes standard development practices and code quality",
                    "Third-party API integrations assumed to have stable documentation"
                ]
            },
            "tech_stack": tech_stack_result,
            "proposal": proposal_result,
            "planning": {
                "phase_split": planning_result["phase_breakdown"],
                "team_recommendation": planning_result["team_recommendation"],
                "complexity_breakdown": planning_result["complexity_totals"]
            },
            "metadata": {
                "pipeline_version": "2.0.0",
                "feature_count": len(estimated_features),
                "modules_selected": len(selected_modules),
                "calibrated_features": sum(1 for f in estimated_features if f.get("was_calibrated", False)),
                "calibration_coverage": round(
                    sum(1 for f in estimated_features if f.get("was_calibrated", False)) / len(estimated_features) * 100
                    if len(estimated_features) > 0 else 0,
                    1
                ),
                "build_options": build_options,
                "timeline_constraint": timeline_constraint,
            }
        }
        
        yield {"stage": "completed", "result": final_result}
    
    def _format_features_for_response(
        self, 
        estimated_features: list, 
        overall_confidence: float
    ) -> list:
        """
        Transform estimation agent output to match Feature model schema.
        
        Args:
            estimated_features: Raw features from estimation agent
            overall_confidence: Overall confidence score
            
        Returns:
            Features formatted for Feature model with subfeatures
        """
        formatted = []
        
        for feature in estimated_features:
            subfeatures = []
            for sf in feature.get("subfeatures", []):
                subfeatures.append({
                    "name": sf.get("name", ""),
                    "effort": sf.get("effort", 0.0)
                })
            
            formatted.append({
                "name": feature.get("name", ""),
                "complexity": feature.get("complexity", "Medium").lower(),
                "total_hours": feature.get("total_hours", 0.0),
                "subfeatures": subfeatures,
                "confidence_score": round(overall_confidence, 2)
            })
        
        return formatted
    
    def _calculate_overall_complexity(self, features: list) -> str:
        """
        Calculate overall project complexity based on feature distribution.
        
        Args:
            features: List of estimated features
            
        Returns:
            Overall complexity level
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
