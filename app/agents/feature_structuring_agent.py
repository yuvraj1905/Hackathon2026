from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent


class FeatureStructuringAgent(BaseAgent):
    
    SYSTEM_PROMPT = """You are a senior GeekyAnts presales architect breaking down project scope into normalized features.

Your task: Convert project description into a structured feature list.

Rules:
1. Extract ALL features mentioned in the description
2. Normalize feature names (use standard industry terms)
3. Assign each feature to a category: Core, Integration, Admin, Security, Infrastructure, UI/UX, Analytics, Communication
4. Assign complexity: Low, Medium, or High based on:
   - Low: Standard CRUD, basic UI, simple integrations
   - Medium: Complex business logic, third-party APIs, real-time features
   - High: Advanced algorithms, complex integrations, compliance requirements, scalability challenges

5. Ensure ALL "Required Core Modules" from the input are included as features
6. Be comprehensive but avoid duplication
7. Use clear, professional feature names

Respond with ONLY valid JSON. No markdown, no explanation."""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure project description into normalized feature list.
        
        Args:
            input_data: Dict with 'enriched_description' key
            
        Returns:
            Dict with 'features' key containing list of feature dicts
        """
        enriched_description = input_data.get("enriched_description", "")
        
        if not enriched_description or len(enriched_description.strip()) < 10:
            return {"features": []}
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"{enriched_description}\n\nBreak down this project into normalized features. Return JSON with: features (array of objects with name, category, complexity)."}
        ]
        
        response = await self.call_llm(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=2000
        )
        
        parsed = self.parse_json_response(response)
        
        features = parsed.get("features", [])
        
        normalized_features = self._normalize_features(features)
        
        return {"features": normalized_features}
    
    def _normalize_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Normalize and validate feature structure.
        
        Args:
            features: Raw feature list from LLM
            
        Returns:
            Normalized feature list with consistent structure
        """
        normalized = []
        valid_complexities = {"low", "medium", "high"}
        
        for feature in features:
            if not isinstance(feature, dict):
                continue
            
            name = str(feature.get("name", "")).strip()
            category = str(feature.get("category", "Core")).strip()
            complexity = str(feature.get("complexity", "Medium")).strip().lower()
            
            if not name:
                continue
            
            if complexity not in valid_complexities:
                complexity = "medium"
            
            normalized.append({
                "name": name,
                "category": category,
                "complexity": complexity.capitalize()
            })
        
        return normalized
