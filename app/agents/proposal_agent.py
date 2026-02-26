from typing import Dict, Any
from app.agents.base_agent import BaseAgent


class ProposalAgent(BaseAgent):
    
    SYSTEM_PROMPT = """You are a GeekyAnts presales architect writing client-ready proposals.

Write professional, concise proposals that inspire confidence.

Tone: Professional, clear, solution-oriented
Style: Executive-level, no technical jargon unless necessary
Focus: Business value, risk mitigation, delivery confidence

Keep all sections concise."""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate client-ready proposal document.
        
        Args:
            input_data: Dict with domain, features, estimation, tech_stack
            
        Returns:
            Dict with proposal sections
        """
        domain = input_data.get("domain", "unknown")
        features = input_data.get("features", [])
        total_hours = input_data.get("total_hours", 0)
        tech_stack = input_data.get("tech_stack", {})
        
        feature_summary = "\n".join([
            f"- {f.get('name', '')} ({f.get('complexity', 'Medium')} complexity)"
            for f in features[:15]
        ])
        
        tech_summary = ", ".join(tech_stack.get("frontend", []) + tech_stack.get("backend", []))
        
        prompt = f"""Domain: {domain}
Total Estimated Hours: {total_hours}
Tech Stack: {tech_summary}

Key Features:
{feature_summary}

Generate a client-ready proposal. Return JSON with:
- executive_summary (2-3 sentences)
- scope_of_work (3-4 sentences)
- deliverables (array of 5-7 items)
- timeline_weeks (number, based on {total_hours} hours assuming 40 hours/week)
- team_composition (object with roles and counts, e.g. {{"Frontend Developer": 2, "Backend Developer": 2}})
- risks (array of 3-4 items)
- mitigation_strategies (array of 3-4 items matching risks)"""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.call_llm(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1000
        )
        
        parsed = self.parse_json_response(response)
        
        timeline_weeks = parsed.get("timeline_weeks", total_hours / 40)
        if isinstance(timeline_weeks, (int, float)):
            timeline_weeks = round(float(timeline_weeks), 1)
        else:
            timeline_weeks = round(total_hours / 40, 1)
        
        return {
            "executive_summary": parsed.get("executive_summary", ""),
            "scope_of_work": parsed.get("scope_of_work", ""),
            "deliverables": parsed.get("deliverables", []),
            "timeline_weeks": timeline_weeks,
            "team_composition": parsed.get("team_composition", {}),
            "risks": parsed.get("risks", []),
            "mitigation_strategies": parsed.get("mitigation_strategies", [])
        }
