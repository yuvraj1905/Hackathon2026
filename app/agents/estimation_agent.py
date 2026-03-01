import json
from typing import Dict, Any, List
import logging
from app.agents.base_agent import BaseAgent
from app.services.calibration_engine import CalibrationEngine

logger = logging.getLogger(__name__)


class EstimationAgent(BaseAgent):

    BUFFER_MULTIPLIER = 1.20

    def __init__(self, calibration_engine: CalibrationEngine, **kwargs):
        super().__init__(**kwargs)
        self.calibration_engine = calibration_engine

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate hours for each feature at the subfeature level.

        Logic:
          - If calibration data matches a subfeature/feature → use calibrated effort × 1.20
          - If no match → ask LLM to estimate based on historical data trends × 1.20
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

        # Collect all unmatched subfeatures for a single batched LLM call
        unmatched_items: List[Dict[str, str]] = []
        estimated_features = []
        total_hours = 0.0

        for feature in features:
            feature_name = feature.get("name", "")
            complexity = feature.get("complexity", "Medium").lower()
            subfeatures = feature.get("subfeatures", [])

            if not subfeatures:
                subfeatures = [{"name": feature_name}]

            estimated_subfeatures = []
            feature_total = 0.0
            feature_calibrated = False

            for sf in subfeatures:
                sf_name = sf.get("name", "")
                if not sf_name:
                    continue

                calibration_info = self.calibration_engine.get_calibration_info(sf_name)
                was_calibrated = calibration_info is not None and calibration_info["sample_size"] >= 2

                if was_calibrated:
                    feature_calibrated = True
                    raw_hours = calibration_info["avg_hours"]
                    final_hours = round(raw_hours * self.BUFFER_MULTIPLIER, 1)

                    estimated_subfeatures.append({
                        "name": sf_name,
                        "effort": final_hours,
                        "was_calibrated": True
                    })
                    feature_total += final_hours
                else:
                    # Mark for LLM estimation — placeholder to be filled later
                    estimated_subfeatures.append({
                        "name": sf_name,
                        "effort": 0.0,
                        "was_calibrated": False,
                        "_pending_llm": True
                    })
                    unmatched_items.append({
                        "feature": feature_name,
                        "subfeature": sf_name,
                        "complexity": complexity
                    })

            estimated_features.append({
                "name": feature_name,
                "complexity": complexity.capitalize(),
                "total_hours": feature_total,
                "subfeatures": estimated_subfeatures,
                "was_calibrated": feature_calibrated
            })

        # Batch LLM call for all unmatched subfeatures
        if unmatched_items:
            llm_estimates = await self._llm_estimate_batch(unmatched_items, original_description)

            # Fill in LLM estimates
            llm_idx = 0
            for feat in estimated_features:
                for sf in feat["subfeatures"]:
                    if sf.get("_pending_llm"):
                        del sf["_pending_llm"]
                        if llm_idx < len(llm_estimates):
                            raw_hours = llm_estimates[llm_idx]
                            sf["effort"] = round(raw_hours * self.BUFFER_MULTIPLIER, 1)
                        else:
                            # Fallback if LLM returned fewer items
                            sf["effort"] = round(16 * self.BUFFER_MULTIPLIER, 1)
                        feat["total_hours"] += sf["effort"]
                        feat["total_hours"] = round(feat["total_hours"], 1)
                        llm_idx += 1

        # Recalculate totals
        total_hours = sum(f["total_hours"] for f in estimated_features)

        min_hours = total_hours * 0.85
        max_hours = total_hours * 1.15

        return {
            "total_hours": round(total_hours, 1),
            "min_hours": round(min_hours, 1),
            "max_hours": round(max_hours, 1),
            "features": estimated_features,
            "breakdown": self._generate_breakdown(estimated_features)
        }

    async def _llm_estimate_batch(
        self,
        items: List[Dict[str, str]],
        project_description: str
    ) -> List[float]:
        """
        Ask the LLM to estimate hours for unmatched subfeatures,
        using historical calibration data as context for trends.
        """
        historical_summary = self.calibration_engine.get_historical_summary()

        # Build a concise historical context string
        if historical_summary:
            hist_lines = [
                f"  - {entry['feature']}: {entry['avg_hours']}h (from {entry['sample_size']} projects)"
                for entry in historical_summary[:50]  # cap to avoid token bloat
            ]
            historical_context = "Historical effort data from past projects:\n" + "\n".join(hist_lines)
        else:
            historical_context = "No historical data available. Use industry-standard estimates."

        items_description = json.dumps(items, indent=2)

        prompt = f"""You are a software effort estimation expert. Estimate development hours for each subfeature below.

Project context: {project_description}

{historical_context}

Subfeatures to estimate (no calibration data matched these):
{items_description}

Rules:
- Use the historical data trends above to guide your estimates.
- Consider the complexity level of each item (low/medium/high).
- Return ONLY a JSON object with a single key "hours" containing an array of numbers.
- Each number is your best estimate of raw development hours for the corresponding subfeature.
- The order must match the input order exactly.
- Do NOT include any buffer — just raw effort hours.

Example response: {{"hours": [12, 24, 8, 40]}}"""

        try:
            messages = [
                {"role": "system", "content": "You are a precise software estimation assistant. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = await self.call_llm(
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=500
            )

            parsed = self.parse_json_response(response)
            hours_list = parsed.get("hours", [])

            # Validate: must be list of numbers with correct length
            if isinstance(hours_list, list) and len(hours_list) == len(items):
                return [float(h) if isinstance(h, (int, float)) and h > 0 else 16.0 for h in hours_list]

            logger.warning("LLM returned %d estimates for %d items, using fallback", len(hours_list), len(items))
            return [16.0] * len(items)

        except Exception as e:
            logger.error("LLM estimation failed: %s — using fallback", str(e))
            return [16.0] * len(items)

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
