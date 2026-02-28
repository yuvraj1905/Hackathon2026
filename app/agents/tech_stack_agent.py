from typing import Dict, Any
from app.agents.base_agent import BaseAgent


class TechStackAgent(BaseAgent):
    
    DOMAIN_STACK_MAPPING = {
        "ecommerce": {
            "frontend": ["React", "Next.js", "TailwindCSS"],
            "backend": ["Node.js", "Express/NestJS", "Python/FastAPI"],
            "database": ["PostgreSQL", "Redis"],
            "infrastructure": ["AWS/GCP", "Docker", "Nginx"],
            "third_party_services": ["Stripe", "SendGrid", "Cloudinary"],
            "justification": "Proven stack for high-traffic ecommerce with fast page loads, secure payments, and scalable architecture."
        },
        "saas": {
            "frontend": ["React", "TypeScript", "TailwindCSS"],
            "backend": ["Node.js/NestJS", "Python/FastAPI"],
            "database": ["PostgreSQL", "Redis"],
            "infrastructure": ["AWS/GCP", "Kubernetes", "Docker"],
            "third_party_services": ["Stripe", "Auth0", "SendGrid", "Segment"],
            "justification": "Enterprise-grade stack with multi-tenancy support, robust authentication, and horizontal scalability."
        },
        "marketplace": {
            "frontend": ["React", "Next.js", "TailwindCSS"],
            "backend": ["Node.js", "Python/FastAPI"],
            "database": ["PostgreSQL", "MongoDB", "Redis"],
            "infrastructure": ["AWS", "Docker", "Nginx"],
            "third_party_services": ["Stripe Connect", "Twilio", "AWS S3"],
            "justification": "Flexible stack supporting multi-vendor workflows, split payments, and complex transaction handling."
        },
        "healthcare": {
            "frontend": ["React", "TypeScript", "Material-UI"],
            "backend": ["Python/FastAPI", "Node.js"],
            "database": ["PostgreSQL", "Redis"],
            "infrastructure": ["AWS (HIPAA-compliant)", "Docker", "VPN"],
            "third_party_services": ["Twilio Video", "SendGrid", "AWS KMS"],
            "justification": "HIPAA-compliant stack with strong encryption, audit logging, and secure telemedicine capabilities."
        },
        "fintech": {
            "frontend": ["React", "TypeScript", "Material-UI"],
            "backend": ["Python/FastAPI", "Node.js"],
            "database": ["PostgreSQL", "Redis"],
            "infrastructure": ["AWS", "Kubernetes", "WAF"],
            "third_party_services": ["Plaid", "Stripe", "Twilio", "AWS KMS"],
            "justification": "Security-first stack with PCI compliance, fraud detection, and real-time transaction processing."
        },
        "enterprise": {
            "frontend": ["React", "TypeScript", "TailwindCSS"],
            "backend": ["Python/FastAPI", "Node.js/NestJS"],
            "database": ["PostgreSQL", "Redis"],
            "infrastructure": ["AWS/GCP", "Docker", "Nginx"],
            "third_party_services": ["SendGrid", "AWS S3", "Auth0"],
            "justification": "Scalable enterprise stack with robust data management, secure authentication, and flexible integrations."
        }
    }
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend tech stack based on domain and features.
        Uses deterministic mapping for known domains, LLM for custom cases.
        
        Args:
            input_data: Dict with 'domain' and 'features' keys
            
        Returns:
            Dict with tech stack recommendation
        """
        domain = input_data.get("domain", "unknown").lower()
        features = input_data.get("features", [])
        
        if domain in self.DOMAIN_STACK_MAPPING:
            return self.DOMAIN_STACK_MAPPING[domain]
        
        return await self._generate_custom_stack(domain, features)
    
    async def _generate_custom_stack(
        self, 
        domain: str, 
        features: list
    ) -> Dict[str, Any]:
        """
        Generate tech stack recommendation using LLM for unknown domains.
        
        Args:
            domain: Domain name
            features: List of features
            
        Returns:
            Tech stack recommendation dict
        """
        feature_list = "\n".join([f"- {f.get('name', '')}" for f in features[:20]])
        
        messages = [
            {"role": "system", "content": "You are a GeekyAnts technical architect. Recommend a modern, production-ready tech stack. Be concise."},
            {"role": "user", "content": f"Domain: {domain}\n\nFeatures:\n{feature_list}\n\nRecommend tech stack. Return JSON with: frontend (array), backend (array), database (array), infrastructure (array), third_party_services (array), justification (string)."}
        ]
        
        response = await self.call_llm(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=1024
        )
        
        try:
            parsed = self.parse_json_response(response)
        except ValueError:
            # Fallback if response was truncated or malformed
            return {
                "frontend": ["React", "TypeScript", "TailwindCSS"],
                "backend": ["Node.js", "Python/FastAPI"],
                "database": ["PostgreSQL", "Redis"],
                "infrastructure": ["AWS", "Docker"],
                "third_party_services": [],
                "justification": "Custom stack for project requirements (LLM response incomplete)"
            }
        
        return {
            "frontend": parsed.get("frontend", ["React", "TypeScript"]),
            "backend": parsed.get("backend", ["Python/FastAPI"]),
            "database": parsed.get("database", ["PostgreSQL"]),
            "infrastructure": parsed.get("infrastructure", ["AWS", "Docker"]),
            "third_party_services": parsed.get("third_party_services", []),
            "justification": parsed.get("justification", "Custom stack for project requirements")
        }
