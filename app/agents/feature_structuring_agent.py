from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent


class FeatureStructuringAgent(BaseAgent):
    
    SYSTEM_PROMPT = """You are a senior GeekyAnts solutions architect extracting features from project requirements for estimation.

YOUR TASK: Extract features from the provided requirements/document. The document content is your primary source of truth.

FEATURE EXTRACTION:
1. Read the document/requirements carefully
2. Extract features based on what the document actually describes
3. Use the client's terminology and business domain
4. Include specific integrations or APIs mentioned
5. If suggested modules don't match the document, prioritize the document

STRUCTURE:
- Group related functionality into logical PARENT features (e.g., "User Authentication", "Payment System")
- Under each parent, list specific SUBFEATURES that are individual implementable units (e.g., "JWT Auth", "Google Login", "Password Reset")
- Each parent feature gets a complexity: Low, Medium, or High
- Subfeatures are the granular tasks that make up the parent feature

COMPLEXITY ASSESSMENT (for parent feature):

**Low:** Standard CRUD, basic forms, simple displays, static pages, basic auth

**Medium:** Business logic with conditions, third-party APIs, file processing, RBAC, search/filters, dashboards, multi-step workflows

**High:** Compliance (HIPAA, PCI-DSS, GDPR), real-time tracking/GPS, complex algorithms, AI/ML, multi-tenant, complex integrations

OUTPUT: Extract ALL features with their subfeatures. When in doubt, lean towards higher complexity.

Respond with ONLY valid JSON:
{"features": [{"name": "Feature Name", "complexity": "Low|Medium|High", "subfeatures": [{"name": "Subfeature 1"}, {"name": "Subfeature 2"}]}, ...]}"""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure project into feature list with subfeatures based on raw context.
        
        Args:
            input_data: Dict with 'additional_details', 'extracted_text', 
                       'selected_modules', 'build_options', 'domain'
            
        Returns:
            Dict with 'features' key containing list of feature dicts with subfeatures
        """
        additional_details = input_data.get("additional_details", "")
        extracted_text = input_data.get("extracted_text", "")
        selected_modules = input_data.get("selected_modules", [])
        build_options = input_data.get("build_options", [])
        domain = input_data.get("domain", "unknown")
        
        has_context = bool(
            (additional_details and additional_details.strip()) or 
            (extracted_text and extracted_text.strip()) or 
            selected_modules
        )
        
        if not has_context:
            return {"features": []}
        
        user_message = self._build_user_message(
            additional_details=additional_details,
            extracted_text=extracted_text,
            selected_modules=selected_modules,
            build_options=build_options,
            domain=domain
        )
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        response = await self.call_llm(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=4000
        )
        
        parsed = self.parse_json_response(response)
        
        features = parsed.get("features", [])
        
        normalized_features = self._normalize_features(features)
        
        return {"features": normalized_features}
    
    def _build_user_message(
        self,
        additional_details: str,
        extracted_text: str,
        selected_modules: List[str],
        build_options: List[str],
        domain: str
    ) -> str:
        """Build the user message with all context for the LLM."""
        platform_info = ""
        if build_options:
            platforms = []
            if "mobile" in build_options:
                platforms.append("Mobile App (iOS/Android)")
            if "web" in build_options:
                platforms.append("Web Application")
            if "admin" in build_options:
                platforms.append("Admin Panel")
            if "backend" in build_options:
                platforms.append("Backend API")
            if "design" in build_options:
                platforms.append("UI/UX Design")
            if platforms:
                platform_info = f"\nPLATFORMS TO BUILD: {', '.join(platforms)}"
        
        message_parts = [f"DOMAIN: {domain.upper()}{platform_info}"]
        
        if extracted_text and extracted_text.strip():
            doc_preview = extracted_text.strip()[:6000]
            if len(extracted_text.strip()) > 6000:
                doc_preview += "\n... (truncated)"
            message_parts.append(f"\nPROJECT DOCUMENT:\n{doc_preview}")
        
        if additional_details and additional_details.strip():
            message_parts.append(f"\nADDITIONAL DETAILS:\n{additional_details.strip()}")
        
        if selected_modules:
            modules_text = "\n".join(f"- {module}" for module in selected_modules)
            message_parts.append(f"\nSUGGESTED MODULES:\n{modules_text}")
        
        message_parts.append("\nExtract features with subfeatures and complexity assessment.")
        
        return "\n".join(message_parts)
    
    def _normalize_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize and validate feature structure with subfeatures."""
        normalized = []
        valid_complexities = {"low", "medium", "high"}
        
        for feature in features:
            if not isinstance(feature, dict):
                continue
            
            name = str(feature.get("name", "")).strip()
            complexity = str(feature.get("complexity", "Medium")).strip().lower()
            
            if not name:
                continue
            
            if complexity not in valid_complexities:
                complexity = "medium"
            
            raw_subfeatures = feature.get("subfeatures", [])
            subfeatures = []
            
            for sf in raw_subfeatures:
                if isinstance(sf, dict):
                    sf_name = str(sf.get("name", "")).strip()
                    if sf_name:
                        subfeatures.append({"name": sf_name})
                elif isinstance(sf, str) and sf.strip():
                    subfeatures.append({"name": sf.strip()})
            
            # If no subfeatures were provided, create a single one from the parent name
            if not subfeatures:
                subfeatures.append({"name": name})
            
            normalized.append({
                "name": name,
                "complexity": complexity.capitalize(),
                "subfeatures": subfeatures
            })
        
        return normalized
