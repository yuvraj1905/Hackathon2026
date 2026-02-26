from typing import Dict, Optional
import re


class CalibrationEngine:
    
    def __init__(self):
        self._calibration_data: Dict[str, Dict[str, float]] = {}
    
    def _normalize_feature_name(self, name: str) -> str:
        """
        Normalize feature name for consistent lookup.
        
        Args:
            name: Raw feature name
            
        Returns:
            Normalized feature name (lowercase, alphanumeric only)
        """
        normalized = re.sub(r'[^a-z0-9]+', '', name.lower())
        return normalized
    
    def add_calibration_data(self, feature_name: str, actual_hours: float) -> None:
        """
        Add historical data for a feature.
        
        Args:
            feature_name: Feature name
            actual_hours: Actual hours spent
        """
        normalized_name = self._normalize_feature_name(feature_name)
        
        if normalized_name not in self._calibration_data:
            self._calibration_data[normalized_name] = {
                "total_hours": 0.0,
                "sample_size": 0
            }
        
        self._calibration_data[normalized_name]["total_hours"] += actual_hours
        self._calibration_data[normalized_name]["sample_size"] += 1
    
    def get_calibrated_hours(self, feature_name: str, base_hours: float) -> float:
        """
        Get calibrated hours for a feature.
        Only applies calibration if sample_size >= 2.
        
        Args:
            feature_name: Feature name
            base_hours: Base estimated hours
            
        Returns:
            Calibrated hours or base hours if insufficient data
        """
        normalized_name = self._normalize_feature_name(feature_name)
        
        if normalized_name not in self._calibration_data:
            return base_hours
        
        data = self._calibration_data[normalized_name]
        sample_size = data["sample_size"]
        
        if sample_size < 2:
            return base_hours
        
        avg_hours = data["total_hours"] / sample_size
        return avg_hours
    
    def get_calibration_info(self, feature_name: str) -> Optional[Dict[str, float]]:
        """
        Get calibration info for a feature.
        
        Args:
            feature_name: Feature name
            
        Returns:
            Dict with avg_hours and sample_size, or None if not found
        """
        normalized_name = self._normalize_feature_name(feature_name)
        
        if normalized_name not in self._calibration_data:
            return None
        
        data = self._calibration_data[normalized_name]
        sample_size = data["sample_size"]
        
        if sample_size == 0:
            return None
        
        return {
            "avg_hours": data["total_hours"] / sample_size,
            "sample_size": sample_size
        }
