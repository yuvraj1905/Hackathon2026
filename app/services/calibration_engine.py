from typing import Any, Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


class CalibrationEngine:
    
    def __init__(self):
        self._calibration_data: Dict[str, Dict[str, float]] = {}
    
    def load_from_aggregated_data(self, aggregated_data: Dict[str, Dict]) -> None:
        """
        Load calibration data from CSV loader aggregated output.
        
        Args:
            aggregated_data: Dict from CSVCalibrationLoader with avg_hours and sample_size
        """
        for feature_key, data in aggregated_data.items():
            self._calibration_data[feature_key] = {
                "total_hours": data["avg_hours"] * data["sample_size"],
                "sample_size": data["sample_size"]
            }
        
        logger.info(f"Loaded {len(self._calibration_data)} features into calibration engine")
    
    STOPWORDS = [
        "user", "management", "system", "module", "service", 
        "and", "&", "the", "a", "an", "for", "with"
    ]
    
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
    
    def normalize_for_matching(self, name: str) -> str:
        """
        Normalize feature name for fuzzy matching.
        Removes stopwords and common noise.
        
        Args:
            name: Raw feature name
            
        Returns:
            Normalized name with stopwords removed
        """
        normalized = name.lower().strip()
        
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        tokens = normalized.split()
        
        filtered_tokens = [t for t in tokens if t not in self.STOPWORDS]
        
        result = ' '.join(filtered_tokens)
        
        return result.strip()
    
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
        Get calibrated hours for a feature using fuzzy matching.
        Only applies calibration if sample_size >= 2.
        
        Matching strategy (in order):
        A) Exact normalized match
        B) Contains match (substring)
        C) Token overlap >= 0.6
        
        Args:
            feature_name: Feature name
            base_hours: Base estimated hours
            
        Returns:
            Calibrated hours or base hours if insufficient data
        """
        normalized_name = self._normalize_feature_name(feature_name)
        
        if normalized_name in self._calibration_data:
            data = self._calibration_data[normalized_name]
            if data["sample_size"] >= 2:
                avg_hours = data["total_hours"] / data["sample_size"]
                return avg_hours
        
        matched_key = self._fuzzy_match(feature_name)
        
        if matched_key:
            data = self._calibration_data[matched_key]
            if data["sample_size"] >= 2:
                avg_hours = data["total_hours"] / data["sample_size"]
                logger.debug(f"Fuzzy match: '{feature_name}' → '{matched_key}' ({avg_hours}h)")
                return avg_hours
        
        return base_hours
    
    def _fuzzy_match(self, feature_name: str) -> Optional[str]:
        """
        Find best fuzzy match in calibration data.
        
        Strategy (in order):
        A) Exact normalized match (already checked by caller)
        B) Contains match (substring in normalized form)
        C) Token overlap >= 0.6
        
        Args:
            feature_name: Feature name to match
            
        Returns:
            Matched calibration key or None
        """
        feature_normalized_full = self._normalize_feature_name(feature_name)
        feature_normalized_tokens = self.normalize_for_matching(feature_name)
        feature_tokens = set(feature_normalized_tokens.split())
        
        if not feature_tokens:
            return None
        
        best_match = None
        best_sample_size = 0
        
        for calibrated_key in self._calibration_data.keys():
            data = self._calibration_data[calibrated_key]
            
            if data["sample_size"] < 2:
                continue
            
            if calibrated_key in feature_normalized_full or feature_normalized_full in calibrated_key:
                if data["sample_size"] > best_sample_size:
                    best_match = calibrated_key
                    best_sample_size = data["sample_size"]
                continue
            
            calibrated_key_expanded = re.sub(r'([a-z])([0-9])', r'\1 \2', calibrated_key)
            calibrated_tokens = set(calibrated_key_expanded.split())
            
            if not calibrated_tokens:
                continue
            
            overlap = len(feature_tokens & calibrated_tokens)
            total = len(feature_tokens | calibrated_tokens)
            
            if total > 0:
                overlap_score = overlap / total
                
                if overlap_score >= 0.6:
                    if data["sample_size"] > best_sample_size:
                        best_match = calibrated_key
                        best_sample_size = data["sample_size"]
        
        return best_match
    
    def get_historical_summary(self) -> List[Dict[str, Any]]:
        """
        Return a summary of all calibration data for LLM context.
        Only includes entries with sample_size >= 2.

        Returns:
            List of dicts with feature_name, avg_hours, sample_size
        """
        summary = []
        for key, data in self._calibration_data.items():
            if data["sample_size"] >= 2:
                summary.append({
                    "feature": key,
                    "avg_hours": round(data["total_hours"] / data["sample_size"], 1),
                    "sample_size": data["sample_size"]
                })
        summary.sort(key=lambda x: x["avg_hours"])
        return summary

    def get_calibration_info(self, feature_name: str) -> Optional[Dict[str, float]]:
        """
        Get calibration info for a feature using fuzzy matching.
        
        Args:
            feature_name: Feature name
            
        Returns:
            Dict with avg_hours and sample_size, or None if not found
        """
        normalized_name = self._normalize_feature_name(feature_name)
        
        if normalized_name in self._calibration_data:
            data = self._calibration_data[normalized_name]
            if data["sample_size"] > 0:
                return {
                    "avg_hours": data["total_hours"] / data["sample_size"],
                    "sample_size": data["sample_size"]
                }
        
        matched_key = self._fuzzy_match(feature_name)
        
        if matched_key:
            data = self._calibration_data[matched_key]
            if data["sample_size"] > 0:
                return {
                    "avg_hours": data["total_hours"] / data["sample_size"],
                    "sample_size": data["sample_size"]
                }
        
        return None
