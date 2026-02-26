from typing import List, Dict, Any


class ConfidenceEngine:
    
    @staticmethod
    def calculate_confidence(
        features: List[Dict[str, Any]],
        domain_confidence: float,
        calibration_engine: Any = None
    ) -> float:
        """
        Calculate overall confidence score using calibration-weighted formula.
        
        Formula: (coverage_score * 0.6 + strength_score * 0.4) * 100
        Capped at 95.
        
        Args:
            features: List of estimated features with calibration info
            domain_confidence: Confidence from domain detection (0.0-1.0)
            calibration_engine: Optional calibration engine for sample size lookup
            
        Returns:
            Confidence score (0-95)
        """
        if not features:
            return 0.0
        
        coverage_score = ConfidenceEngine._calculate_coverage_score(features)
        strength_score = ConfidenceEngine._calculate_strength_score(
            features,
            calibration_engine
        )
        
        confidence = (coverage_score * 0.6 + strength_score * 0.4) * 100
        
        return min(confidence, 95.0)
    
    @staticmethod
    def _calculate_coverage_score(features: List[Dict[str, Any]]) -> float:
        """
        Calculate coverage score based on calibration availability.
        
        coverage_score = calibrated_features / total_features
        
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
        
        return coverage
    
    @staticmethod
    def _calculate_strength_score(
        features: List[Dict[str, Any]],
        calibration_engine: Any = None
    ) -> float:
        """
        Calculate strength score based on calibration sample sizes.
        
        strength_score = features_with_sample_size>=3 / total_features
        
        Args:
            features: List of features
            calibration_engine: Calibration engine for sample size lookup
            
        Returns:
            Strength score (0.0-1.0)
        """
        if not features:
            return 0.0
        
        if not calibration_engine:
            return 0.5
        
        strong_calibration_count = 0
        
        for feature in features:
            if not feature.get("was_calibrated", False):
                continue
            
            feature_name = feature.get("name", "")
            calibration_info = calibration_engine.get_calibration_info(feature_name)
            
            if calibration_info and calibration_info.get("sample_size", 0) >= 3:
                strong_calibration_count += 1
        
        strength = strong_calibration_count / len(features)
        
        return strength
