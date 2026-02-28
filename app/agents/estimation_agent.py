from typing import Dict, Any, List
import logging
from app.agents.base_agent import BaseAgent
from app.services.calibration_engine import CalibrationEngine

logger = logging.getLogger(__name__)


class EstimationAgent(BaseAgent):
    
    COMPLEXITY_BASE_HOURS = {
        "low": 28,
        "medium": 72,
        "high": 140
    }
    
    COMPLEXITY_FLOOR_HOURS = {
        "low": 16,
        "medium": 32,
        "high": 64
    }
    
    # Per-subfeature base hours by parent complexity
    SUBFEATURE_BASE_HOURS = {
        "low": 8,
        "medium": 16,
        "high": 28
    }
    
    BUFFER_MULTIPLIER = 1.15
    
    def __init__(self, calibration_engine: CalibrationEngine, **kwargs):
        super().__init__(**kwargs)
        self.calibration_engine = calibration_engine
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate hours for each feature at the subfeature level.
        
        Args:
            input_data: Dict with 'features' key (list of feature dicts with subfeatures)
            
        Returns:
            Dict with detailed estimation breakdown
        """
        features = input_data.get("features", [])
        original_description = input_data.get("original_description", "")
        
        if not features:
            return {
                "total_hours": 0.0,
                "min_hours": 0.0,
                "max_hours": 0.0,
                "features": [],
                "breakdown": []
            }
        
        mvp_factor = self._detect_mvp_scope(original_description, features)
        
        estimated_features = []
        total_hours = 0.0
        
        for feature in features:
            feature_name = feature.get("name", "")
            complexity = feature.get("complexity", "Medium").lower()
            subfeatures = feature.get("subfeatures", [])
            
            estimated_subfeatures = []
            feature_total = 0.0
            feature_calibrated = False
            
            if not subfeatures:
                subfeatures = [{"name": feature_name}]
            
            subfeature_base = self.SUBFEATURE_BASE_HOURS.get(complexity, 16)
            
            for sf in subfeatures:
                sf_name = sf.get("name", "")
                if not sf_name:
                    continue
                
                # Try calibration on the subfeature name
                calibrated_hours = self.calibration_engine.get_calibrated_hours(
                    sf_name,
                    subfeature_base
                )
                
                calibration_info = self.calibration_engine.get_calibration_info(sf_name)
                sf_was_calibrated = calibration_info is not None and calibration_info["sample_size"] >= 2
                
                if sf_was_calibrated:
                    feature_calibrated = True
                
                final_sf_hours = calibrated_hours * self.BUFFER_MULTIPLIER * mvp_factor
                final_sf_hours = round(final_sf_hours, 1)
                
                estimated_subfeatures.append({
                    "name": sf_name,
                    "effort": final_sf_hours,
                    "was_calibrated": sf_was_calibrated
                })
                
                feature_total += final_sf_hours
            
            # Also try calibration on the parent feature name for a sanity check
            parent_base = self.COMPLEXITY_BASE_HOURS.get(complexity, 72)
            parent_calibrated = self.calibration_engine.get_calibrated_hours(
                feature_name,
                parent_base
            )
            parent_info = self.calibration_engine.get_calibration_info(feature_name)
            parent_was_calibrated = parent_info is not None and parent_info["sample_size"] >= 2
            
            if parent_was_calibrated:
                feature_calibrated = True
                # If the parent has strong calibration and subfeature sum is very different,
                # use parent calibration as a floor
                parent_calibrated_with_buffer = parent_calibrated * self.BUFFER_MULTIPLIER * mvp_factor
                complexity_floor = self.COMPLEXITY_FLOOR_HOURS.get(complexity, 32)
                parent_calibrated_with_buffer = max(parent_calibrated_with_buffer, complexity_floor)
                
                if feature_total < parent_calibrated_with_buffer * 0.5:
                    # Subfeature sum is too low vs calibration — scale up proportionally
                    if feature_total > 0:
                        scale = parent_calibrated_with_buffer / feature_total
                        for sf in estimated_subfeatures:
                            sf["effort"] = round(sf["effort"] * scale, 1)
                        feature_total = round(parent_calibrated_with_buffer, 1)
            
            feature_total = round(feature_total, 1)
            
            estimated_features.append({
                "name": feature_name,
                "complexity": complexity.capitalize(),
                "total_hours": feature_total,
                "subfeatures": estimated_subfeatures,
                "was_calibrated": feature_calibrated
            })
            
            total_hours += feature_total
        
        min_hours = total_hours * 0.85
        max_hours = total_hours * 1.15
        
        return {
            "total_hours": round(total_hours, 1),
            "min_hours": round(min_hours, 1),
            "max_hours": round(max_hours, 1),
            "features": estimated_features,
            "breakdown": self._generate_breakdown(estimated_features)
        }
    
    def _detect_mvp_scope(self, description: str, features: List[Dict[str, Any]]) -> float:
        """Detect if project is a small/MVP scope and apply reduction."""
        if len(features) >= 12:
            return 1.0
        
        description_lower = description.lower()
        
        mvp_signals = [
            "basic", "simple", "small", "mvp", "minimal",
            "flower", "flowers", "boutique", "shop", "local",
            "small business", "startup", "beginner"
        ]
        
        signal_count = sum(1 for signal in mvp_signals if signal in description_lower)
        
        if signal_count == 0:
            return 1.0
        
        if signal_count >= 3:
            return 0.75
        elif signal_count >= 2:
            return 0.80
        else:
            return 0.85
    
    def _generate_breakdown(self, features: List[Dict[str, Any]]) -> Dict[str, float]:
        """Generate hours breakdown by complexity level."""
        breakdown = {}
        
        for feature in features:
            complexity = feature.get("complexity", "Medium")
            hours = feature.get("total_hours", 0.0)
            
            if complexity not in breakdown:
                breakdown[complexity] = 0.0
            
            breakdown[complexity] += hours
        
        return {k: round(v, 1) for k, v in breakdown.items()}