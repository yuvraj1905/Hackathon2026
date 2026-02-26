from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.services.calibration_engine import CalibrationEngine


class EstimationAgent(BaseAgent):
    
    COMPLEXITY_BASE_HOURS = {
        "low": 28,
        "medium": 72,
        "high": 140
    }
    
    BUFFER_MULTIPLIER = 1.15
    
    def __init__(self, calibration_engine: CalibrationEngine, **kwargs):
        super().__init__(**kwargs)
        self.calibration_engine = calibration_engine
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate hours for each feature with calibration and buffer.
        
        Args:
            input_data: Dict with 'features' key (list of feature dicts)
            
        Returns:
            Dict with detailed estimation breakdown
        """
        features = input_data.get("features", [])
        
        if not features:
            return {
                "total_hours": 0.0,
                "min_hours": 0.0,
                "max_hours": 0.0,
                "features": [],
                "breakdown": []
            }
        
        estimated_features = []
        total_base_hours = 0.0
        
        for feature in features:
            feature_name = feature.get("name", "")
            complexity = feature.get("complexity", "Medium").lower()
            
            base_hours = self.COMPLEXITY_BASE_HOURS.get(complexity, 72)
            
            calibrated_hours = self.calibration_engine.get_calibrated_hours(
                feature_name, 
                base_hours
            )
            
            final_hours = calibrated_hours * self.BUFFER_MULTIPLIER
            
            calibration_info = self.calibration_engine.get_calibration_info(feature_name)
            was_calibrated = calibration_info is not None and calibration_info["sample_size"] >= 2
            
            estimated_features.append({
                "name": feature_name,
                "category": feature.get("category", "Core"),
                "complexity": complexity.capitalize(),
                "base_hours": round(base_hours, 1),
                "calibrated_hours": round(calibrated_hours, 1),
                "final_hours": round(final_hours, 1),
                "was_calibrated": was_calibrated
            })
            
            total_base_hours += final_hours
        
        min_hours = total_base_hours * 0.85
        max_hours = total_base_hours * 1.35
        
        return {
            "total_hours": round(total_base_hours, 1),
            "min_hours": round(min_hours, 1),
            "max_hours": round(max_hours, 1),
            "features": estimated_features,
            "breakdown": self._generate_breakdown(estimated_features)
        }
    
    def _generate_breakdown(self, features: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Generate hours breakdown by category.
        
        Args:
            features: List of estimated features
            
        Returns:
            Dict mapping category to total hours
        """
        breakdown = {}
        
        for feature in features:
            category = feature.get("category", "Core")
            hours = feature.get("final_hours", 0.0)
            
            if category not in breakdown:
                breakdown[category] = 0.0
            
            breakdown[category] += hours
        
        return {k: round(v, 1) for k, v in breakdown.items()}
