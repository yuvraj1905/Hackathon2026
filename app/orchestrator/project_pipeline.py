from typing import Dict, Any
import uuid
from app.agents.domain_detection_agent import DomainDetectionAgent
from app.agents.feature_structuring_agent import FeatureStructuringAgent
from app.agents.estimation_agent import EstimationAgent
from app.agents.tech_stack_agent import TechStackAgent
from app.agents.proposal_agent import ProposalAgent
from app.services.template_expander import TemplateExpander
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
    
    async def run(self, project_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute full estimation pipeline.
        
        Flow:
        1. Detect domain
        2. Expand with templates
        3. Structure features
        4. Estimate hours
        5. Calculate confidence
        6. Recommend tech stack
        7. Generate proposal
        
        Args:
            project_input: Dict with 'description' key
            
        Returns:
            Complete pipeline response
        """
        request_id = str(uuid.uuid4())
        description = project_input.get("description", "")
        
        domain_result = await self.domain_agent.execute({
            "description": description
        })
        
        detected_domain = domain_result.get("detected_domain", "unknown")
        
        enriched_description = TemplateExpander.expand(
            detected_domain, 
            description
        )
        
        feature_result = await self.feature_agent.execute({
            "enriched_description": enriched_description
        })
        
        features = feature_result.get("features", [])
        
        estimation_result = await self.estimation_agent.execute({
            "features": features,
            "original_description": description
        })
        
        estimated_features = estimation_result.get("features", [])
        total_hours = estimation_result.get("total_hours", 0)
        min_hours = estimation_result.get("min_hours", 0)
        max_hours = estimation_result.get("max_hours", 0)
        
        confidence_score = ConfidenceEngine.calculate_confidence(
            estimated_features,
            domain_result.get("confidence", 0.5),
            self.calibration_engine
        )
        
        tech_stack_result = await self.tech_stack_agent.execute({
            "domain": detected_domain,
            "features": features
        })
        
        proposal_result = await self.proposal_agent.execute({
            "domain": detected_domain,
            "features": estimated_features,
            "total_hours": total_hours,
            "tech_stack": tech_stack_result
        })
        
        formatted_features = self._format_features_for_response(
            estimated_features, 
            confidence_score / 100
        )
        
        planning_result = PlanningEngine.compute_planning(
            total_hours=total_hours,
            timeline_weeks=proposal_result.get("timeline_weeks", total_hours / 40),
            features=formatted_features
        )
        
        return {
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
                "category_breakdown": planning_result["category_totals"]
            },
            "metadata": {
                "pipeline_version": "1.0.0",
                "feature_count": len(estimated_features),
                "calibrated_features": sum(1 for f in estimated_features if f.get("was_calibrated", False)),
                "calibration_coverage": round(
                    sum(1 for f in estimated_features if f.get("was_calibrated", False)) / len(estimated_features) * 100
                    if len(estimated_features) > 0 else 0,
                    1
                )
            }
        }
    
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
            Features formatted for Feature model
        """
        formatted = []
        
        for feature in estimated_features:
            formatted.append({
                "name": feature.get("name", ""),
                "description": feature.get("category", "Core"),
                "complexity": feature.get("complexity", "Medium").lower(),
                "estimated_hours": feature.get("final_hours", 0.0),
                "dependencies": [],
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
