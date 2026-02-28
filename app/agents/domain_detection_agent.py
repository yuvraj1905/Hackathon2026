from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models.project_models import DomainDetectionResult, Domain


class DomainDetectionAgent(BaseAgent):
    
    SYSTEM_PROMPT = """You are a GeekyAnts presales architect classifying software projects into domains.

Classify the project into the MOST SPECIFIC domain that matches its PRIMARY business purpose.

AVAILABLE DOMAINS:

INDUSTRY-SPECIFIC:
- ecommerce: Online stores, retail platforms, product purchasing
- fintech: Banking, payments, wallets, trading, financial services
- healthcare: Medical systems for human patients, telemedicine, clinics, hospitals
- education: Learning platforms, courses, e-learning, LMS
- marketplace: Multi-vendor platforms with multiple sellers
- logistics: Shipping, fleet, warehouse, supply chain, delivery
- insurance: Policy management, claims, underwriting

PLATFORM-TYPE:
- enterprise: Internal business systems, asset management, resource tracking, CRM, operations
- saas: B2B software, subscription services, management tools
- iot: Device management, sensors, connected devices
- social_media: Social networks, community platforms

GENERIC (last resort):
- mobile_app: Mobile-first apps not fitting above
- web_app: Web apps not fitting above
- ai_ml: AI/ML focused products
- blockchain: Crypto, DeFi, NFT, blockchain
- unknown: Cannot determine

CLASSIFICATION APPROACH:
1. Identify the PRIMARY business purpose - what is the core thing being managed or transacted?
2. Prefer specific industry domains over generic ones
3. Multi-vendor = marketplace
4. Internal management/operations systems = enterprise or saas

Respond with ONLY valid JSON: {"domain": "...", "confidence": 0.0-1.0, "reasoning": "one sentence"}"""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect the primary domain of a project from its description and context.
        
        Args:
            input_data: Dict with 'description', optional 'additional_details',
                       'extracted_text', 'build_options', 'timeline_constraint',
                       'additional_context'
            
        Returns:
            Dict containing DomainDetectionResult data
        """
        description = input_data.get("description", "")
        additional_details = input_data.get("additional_details", "")
        extracted_text = input_data.get("extracted_text", "")
        build_options = input_data.get("build_options", [])
        timeline_constraint = input_data.get("timeline_constraint", "")
        additional_context = input_data.get("additional_context", "")
        
        if not description or len(description.strip()) < 10:
            return {
                "detected_domain": Domain.UNKNOWN.value,
                "confidence": 0.0,
                "secondary_domains": [],
                "reasoning": "Insufficient project description provided"
            }
        
        # Build rich context for LLM
        build_info = self._format_build_options(build_options)
        additional_details_preview = (additional_details or "").strip()[:2000]
        extracted_text_preview = (extracted_text or "").strip()[:4000]
        
        user_message = f"""PROJECT DESCRIPTION:
{description}
{f"\nADDITIONAL DETAILS (verbatim):\n{additional_details_preview}" if additional_details_preview else ""}
{f"\nEXTRACTED DOCUMENT TEXT (verbatim):\n{extracted_text_preview}" if extracted_text_preview else ""}
{build_info}
{f"Timeline: {timeline_constraint}" if timeline_constraint else ""}
{f"Additional Context: {additional_context}" if additional_context else ""}

Classify this project into the most appropriate domain. Be specific - prefer industry domains over generic ones."""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
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
    
    def _format_build_options(self, build_options: List[str]) -> str:
        """
        Format build options into a readable string for the LLM.
        
        Args:
            build_options: List of build options (mobile, web, admin, backend, design)
            
        Returns:
            Formatted string describing platforms to build
        """
        if not build_options:
            return ""
        
        platforms = []
        if "mobile" in build_options:
            platforms.append("Mobile App")
        if "web" in build_options:
            platforms.append("Web App")
        if "admin" in build_options:
            platforms.append("Admin Panel")
        if "backend" in build_options:
            platforms.append("Backend API")
        if "design" in build_options:
            platforms.append("UI/UX Design")
        
        if platforms:
            return f"\nPlatforms to build: {', '.join(platforms)}"
        return ""
    
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
