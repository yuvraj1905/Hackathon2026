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
            input_data: Dict with domain, features, estimation, tech_stack,
                        description, additional_details

        Returns:
            Dict with proposal sections
        """
        domain = input_data.get("domain", "unknown")
        features = input_data.get("features", [])
        total_hours = input_data.get("total_hours", 0)
        tech_stack = input_data.get("tech_stack", {})
        description = input_data.get("description", "")
        additional_details = input_data.get("additional_details", "")

        feature_summary = "\n".join([
            f"- {f.get('name', '')} ({f.get('complexity', 'Medium')} complexity)"
            for f in features[:15]
        ])


        tech_parts = []
        front = tech_stack.get("frontend")
        back = tech_stack.get("backend")
        if isinstance(front, list):
            tech_parts.extend(front)
        elif isinstance(front, dict):
            for cfg in front.values():
                if isinstance(cfg, dict):
                    tech_parts.extend(str(v) for k, v in cfg.items() if v and k not in ("justification", "type"))
        if isinstance(back, list):
            tech_parts.extend(back)
        elif isinstance(back, dict):
            tech_parts.extend(str(v) for k, v in back.items() if v and k not in ("justification", "type"))
        tech_summary = ", ".join(tech_parts) if tech_parts else "See tech stack section"

        project_context = description
        if additional_details:
            project_context += f"\n\nAdditional Details:\n{additional_details}"

        prompt = f"""Domain: {domain}
Total Estimated Hours: {total_hours}
Tech Stack: {tech_summary}

Project Description:
{project_context}

Key Features:
{feature_summary}

Generate a client-ready proposal. Return JSON with:
- abstract (2-3 paragraphs providing a high-level overview of the project — what it is, why it matters, and the approach)
- executive_summary (2-3 sentences)
- scope_of_work (3-4 sentences)
- deliverables (array of 5-7 items)
- project_timeline (array of objects with "phase", "duration", "description" — e.g. [{{"phase": "Discovery & Planning", "duration": "2 weeks", "description": "Requirements gathering, architecture design, sprint planning"}}]. Include 4-6 phases covering the full project lifecycle)
- timeline_weeks (number, based on {total_hours} hours assuming 40 hours/week)
- team_composition (object with roles and counts, e.g. {{"Frontend Developer": 2, "Backend Developer": 2}})
- risks (array of 3-4 items)
- mitigation_strategies (array of 3-4 items matching risks)
- assumptions (array of 5-8 key assumptions and considerations for successful project delivery, e.g. "Client will provide timely feedback within 2 business days", "All third-party APIs have stable documentation and SLAs")
- client_dependencies (array of 4-6 items the client must provide or facilitate, e.g. "Brand guidelines and design assets", "Access credentials for third-party services", "Designated point of contact for approvals")"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        response = await self.call_llm(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000
        )

        parsed = self.parse_json_response(response)

        timeline_weeks = parsed.get("timeline_weeks", total_hours / 40)
        if isinstance(timeline_weeks, (int, float)):
            timeline_weeks = round(float(timeline_weeks), 1)
        else:
            timeline_weeks = round(total_hours / 40, 1)

        return {
            "abstract": parsed.get("abstract", ""),
            "executive_summary": parsed.get("executive_summary", ""),
            "scope_of_work": parsed.get("scope_of_work", ""),
            "deliverables": parsed.get("deliverables", []),
            "project_timeline": parsed.get("project_timeline", []),
            "timeline_weeks": timeline_weeks,
            "team_composition": parsed.get("team_composition", {}),
            "risks": parsed.get("risks", []),
            "mitigation_strategies": parsed.get("mitigation_strategies", []),
            "assumptions": parsed.get("assumptions", []),
            "client_dependencies": parsed.get("client_dependencies", []),
        }
