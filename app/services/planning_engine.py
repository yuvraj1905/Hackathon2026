from typing import Dict, List, Any
from math import ceil


class PlanningEngine:
    
    PHASE_RATIOS = {
        "frontend": 0.40,
        "backend": 0.35,
        "qa": 0.15,
        "pm_ba": 0.10
    }
    
    HOURS_PER_WEEK = 40
    
    @staticmethod
    def compute_planning(
        total_hours: float,
        timeline_weeks: float,
        features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute deterministic project planning breakdown.
        
        Args:
            total_hours: Total estimated hours
            timeline_weeks: Project timeline in weeks
            features: List of features with complexity levels
            
        Returns:
            Planning breakdown with phases, team, and complexity totals
        """
        phase_breakdown = PlanningEngine._compute_phase_breakdown(total_hours)
        
        team_recommendation = PlanningEngine._compute_team_recommendation(
            total_hours,
            timeline_weeks
        )
        
        complexity_totals = PlanningEngine._compute_complexity_totals(features)
        
        return {
            "phase_breakdown": phase_breakdown,
            "team_recommendation": team_recommendation,
            "complexity_totals": complexity_totals,
            "timeline_weeks": round(timeline_weeks, 1),
            "total_hours": round(total_hours, 1)
        }
    
    @staticmethod
    def _compute_phase_breakdown(total_hours: float) -> Dict[str, float]:
        """
        Split total hours into phases using default ratios.
        
        Args:
            total_hours: Total estimated hours
            
        Returns:
            Dict mapping phase to hours
        """
        return {
            "frontend": round(total_hours * PlanningEngine.PHASE_RATIOS["frontend"], 1),
            "backend": round(total_hours * PlanningEngine.PHASE_RATIOS["backend"], 1),
            "qa": round(total_hours * PlanningEngine.PHASE_RATIOS["qa"], 1),
            "pm_ba": round(total_hours * PlanningEngine.PHASE_RATIOS["pm_ba"], 1)
        }
    
    @staticmethod
    def _compute_team_recommendation(
        total_hours: float,
        timeline_weeks: float
    ) -> Dict[str, int]:
        """
        Calculate recommended team composition.
        
        Args:
            total_hours: Total estimated hours
            timeline_weeks: Project timeline in weeks
            
        Returns:
            Dict mapping role to engineer count
        """
        if timeline_weeks <= 0:
            timeline_weeks = 1
        
        available_hours_per_engineer = timeline_weeks * PlanningEngine.HOURS_PER_WEEK
        
        total_engineers_needed = ceil(total_hours / available_hours_per_engineer)
        
        total_engineers_needed = max(2, total_engineers_needed)
        
        frontend_engineers = max(1, ceil(total_engineers_needed * 0.5))
        backend_engineers = max(1, ceil(total_engineers_needed * 0.5))
        
        qa_engineers = max(1, total_engineers_needed // 3)
        
        pm_count = 1
        
        return {
            "Frontend Developer": frontend_engineers,
            "Backend Developer": backend_engineers,
            "QA Engineer": qa_engineers,
            "Project Manager": pm_count
        }
    
    @staticmethod
    def _compute_complexity_totals(features: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Aggregate hours by feature complexity level.
        
        Args:
            features: List of features with complexity and hours
            
        Returns:
            Dict mapping complexity level (Low, Medium, High) to total hours
        """
        complexity_totals: Dict[str, float] = {}
        
        for feature in features:
            complexity = feature.get("complexity", "medium").capitalize()
            hours = feature.get("total_hours", feature.get("estimated_hours", 0.0))
            
            if complexity not in complexity_totals:
                complexity_totals[complexity] = 0.0
            
            complexity_totals[complexity] += hours
        
        complexity_order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_items = sorted(
            complexity_totals.items(),
            key=lambda x: complexity_order.get(x[0], 3)
        )
        return {k: round(v, 1) for k, v in sorted_items}
