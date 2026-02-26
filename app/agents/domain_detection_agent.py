from typing import Dict, Any
from app.agents.base_agent import BaseAgent
from app.models.project_models import DomainDetectionResult, Domain


class DomainDetectionAgent(BaseAgent):
    
    SYSTEM_PROMPT = """You are a GeekyAnts presales architect specializing in domain classification.

Analyze the project description and classify it into ONE primary domain.

Available domains:
- ecommerce: Online stores, retail platforms, shopping sites
- fintech: Banking, payments, financial services, trading platforms
- healthcare: Medical systems, patient management, telemedicine, health records
- education: Learning platforms, course management, educational tools
- saas: Business software, productivity tools, cloud services
- enterprise: Internal business systems, ERP, CRM, workforce management
- mobile_app: Mobile-first applications, native app features
- web_app: Web applications, browser-based tools
- ai_ml: AI/ML focused products, data science platforms
- marketplace: Multi-vendor platforms, peer-to-peer marketplaces
- social_media: Social networks, community platforms, content sharing
- iot: IoT platforms, device management, sensor networks
- blockchain: Crypto, DeFi, NFT, blockchain applications
- unknown: Cannot determine or multiple domains equally weighted

Respond with ONLY valid JSON. No markdown, no explanation."""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect the primary domain of a project from its description.
        
        Args:
            input_data: Dict with 'description' key
            
        Returns:
            Dict containing DomainDetectionResult data
        """
        description = input_data.get("description", "")
        
        if not description or len(description.strip()) < 10:
            return {
                "detected_domain": Domain.UNKNOWN.value,
                "confidence": 0.0,
                "secondary_domains": [],
                "reasoning": "Insufficient project description provided"
            }
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Project Description:\n{description}\n\nClassify this project into the most appropriate domain. Return JSON with: domain (string), confidence (0.0-1.0), reasoning (one sentence)."}
        ]
        
        response = await self.call_llm(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=200
        )
        
        parsed = self.parse_json_response(response)
        
        domain_str = parsed.get("domain", "unknown").lower()
        
        try:
            domain_enum = Domain(domain_str)
        except ValueError:
            domain_enum = Domain.UNKNOWN
        
        raw_confidence = float(parsed.get("confidence", 0.75))
        realistic_confidence = self._normalize_confidence(raw_confidence)
        
        return {
            "detected_domain": domain_enum.value,
            "confidence": realistic_confidence,
            "secondary_domains": [],
            "reasoning": parsed.get("reasoning", "Domain classification completed")
        }
    
    def _normalize_confidence(self, raw_confidence: float) -> float:
        """
        Normalize confidence to realistic presales range (0.65-0.95).
        
        Args:
            raw_confidence: Raw confidence from LLM (0.0-1.0)
            
        Returns:
            Normalized confidence (0.65-0.95)
        """
        clamped = max(0.0, min(1.0, raw_confidence))
        
        normalized = 0.65 + (clamped * 0.30)
        
        return round(normalized, 2)
