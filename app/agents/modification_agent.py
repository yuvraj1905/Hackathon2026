from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent


class ModificationAgent(BaseAgent):
    
    SYSTEM_PROMPT = """You are a GeekyAnts presales architect modifying project scope.

Your task: Interpret the modification instruction and update the feature list accordingly.

Modification types:
- ADD: Add new features (e.g., "Add analytics dashboard", "Include payment gateway")
- REMOVE: Remove features (e.g., "Remove social login", "Skip email notifications")
- MODIFY: Change existing features (e.g., "Make admin dashboard more complex", "Simplify checkout")

Rules:
1. Preserve existing features unless explicitly asked to remove/modify them
2. For ADD: Create new features with appropriate category and complexity
3. For REMOVE: Filter out matching features
4. For MODIFY: Update complexity or description of matching features
5. Use the same category and complexity standards as the original features
6. Be precise and conservative

Respond with ONLY valid JSON. No markdown, no explanation."""
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modify feature list based on instruction.
        
        Args:
            input_data: Dict with 'current_features' and 'instruction' keys
            
        Returns:
            Dict with 'features' key containing updated feature list
        """
        current_features = input_data.get("current_features", [])
        instruction = input_data.get("instruction", "")
        
        if not instruction or len(instruction.strip()) < 3:
            return {"features": current_features}
        
        features_summary = self._summarize_features(current_features)
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""Current Features:
{features_summary}

Modification Instruction: {instruction}

Apply this modification to the feature list. Return JSON with: features (array of objects with name, category, complexity).

Keep all existing features unless explicitly asked to remove them. Add/modify as instructed."""}
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
    
    def _summarize_features(self, features: List[Dict[str, Any]]) -> str:
        """
        Create a concise summary of current features.
        
        Args:
            features: Current feature list
            
        Returns:
            Formatted feature summary string
        """
        if not features:
            return "No features yet."
        
        summary_lines = []
        for idx, feature in enumerate(features, 1):
            name = feature.get("name", "")
            category = feature.get("category", "")
            complexity = feature.get("complexity", "medium")
            summary_lines.append(f"{idx}. {name} ({category}, {complexity})")
        
        return "\n".join(summary_lines)
    
    def _normalize_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Normalize and validate feature structure.
        
        Args:
            features: Raw feature list from LLM
            
        Returns:
            Normalized feature list
        """
        normalized = []
        valid_complexities = {"low", "medium", "high", "very_high"}
        
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
