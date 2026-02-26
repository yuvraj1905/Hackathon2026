from typing import List, Dict, Any


class ConfidenceEngine:
    
    @staticmethod
    def calculate_confidence(
        features: List[Dict[str, Any]],
        domain_confidence: float
    ) -> float:
        """
        Calculate overall confidence score using weighted formula.
        
        Formula: (coverage_score * 0.6 + strength_score * 0.4) * 100
        Capped at 95.
        
        Args:
            features: List of estimated features with calibration info
            domain_confidence: Confidence from domain detection (0.0-1.0)
            
        Returns:
            Confidence score (0-95)
        """
        if not features:
            return 0.0
        
        coverage_score = ConfidenceEngine._calculate_coverage_score(features)
        strength_score = ConfidenceEngine._calculate_strength_score(
            features, 
            domain_confidence
        )
        
        confidence = (coverage_score * 0.6 + strength_score * 0.4) * 100
        
        return min(confidence, 95.0)
    
    @staticmethod
    def _calculate_coverage_score(features: List[Dict[str, Any]]) -> float:
        """
        Calculate coverage score based on calibration data availability.
        
        Args:
            features: List of features
            
        Returns:
            Coverage score (0.0-1.0)
        """
        if not features:
            return 0.0
        
        calibrated_count = sum(
            1 for f in features if f.get("was_calibrated", False)
        )
        
        coverage = calibrated_count / len(features)
        
        base_coverage = 0.5
        
        return base_coverage + (coverage * 0.5)
    
    @staticmethod
    def _calculate_strength_score(
        features: List[Dict[str, Any]], 
        domain_confidence: float
    ) -> float:
        """
        Calculate strength score based on domain confidence and feature count.
        
        Args:
            features: List of features
            domain_confidence: Domain detection confidence
            
        Returns:
            Strength score (0.0-1.0)
        """
        feature_count = len(features)
        
        if feature_count == 0:
            return 0.0
        
        count_factor = min(feature_count / 15.0, 1.0)
        
        strength = (domain_confidence * 0.7) + (count_factor * 0.3)
        
        return strength
