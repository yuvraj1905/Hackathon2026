import re
from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent


class ModificationAgent(BaseAgent):
    
    SYSTEM_PROMPT = """You are a GeekyAnts presales architect modifying project scope.

Your task: Interpret the modification instruction and update the feature list. Each feature can have subfeatures.

Modification types:
- ADD FEATURE: Add a new top-level feature (e.g. "Add analytics dashboard", "Include payment gateway"). Return it as a new object in the features array with subfeatures: [{"name": "<feature name>"}] or more.
- ADD SUBFEATURE: Add a subfeature inside an existing feature. Examples: "in wallet & balance management add a subfeature of wallet history" → add subfeature "Wallet History" to the feature named "Wallet & Balance Management"; "add payment history subfeature in payment gateway integration" → add to "Payment Gateway Integration". Match the parent feature by name (ignore case, punctuation, extra words). Add ONLY the new subfeature to that feature's subfeatures array; keep all other features and their subfeatures unchanged.
- REMOVE: Remove a feature or a subfeature. If a subfeature is removed, keep the parent feature with its other subfeatures.
- MODIFY: Change existing feature/subfeature name, category, or complexity.

Rules:
1. Preserve existing features and their subfeatures unless explicitly asked to remove or modify them.
2. When the user says "add X subfeature in Y" or "add X under Y", add {"name": "X"} to feature Y's subfeatures only; do NOT add a new top-level feature.
3. When the user says "add feature X" or "add X" (without "subfeature in"), add a new top-level feature with subfeatures: [{"name": "X"}].
4. Output MUST be valid JSON: {"features": [{"name": "...", "category": "...", "complexity": "...", "subfeatures": [{"name": "..."}, ...]}, ...]}. Every feature must have a "subfeatures" array (can be empty).

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

Apply this modification to the feature list. Return JSON with: features (array of objects with name, category, complexity, subfeatures (array of {{name}})).

Keep all existing features and their subfeatures unless explicitly asked to remove them. If adding a subfeature to a feature, add it only to that feature's subfeatures array."""}
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
        
        # Ensure "add X feature" always adds X to the list (LLM sometimes omits it)
        add_feature_name = self._parse_add_feature_intent(instruction)
        if add_feature_name:
            add_feature_name = self._normalize_feature_name_typo(add_feature_name.strip())
            existing_lower = {str(f.get("name", "")).strip().lower() for f in normalized_features}
            if add_feature_name.lower() not in existing_lower:
                display = add_feature_name[0].upper() + add_feature_name[1:].lower() if len(add_feature_name) > 1 else add_feature_name.upper()
                normalized_features.append({
                    "name": display,
                    "category": "Core",
                    "complexity": "medium",
                    "subfeatures": [{"name": display}],
                })
        
        return {"features": normalized_features}
    
    def _summarize_features(self, features: List[Dict[str, Any]]) -> str:
        """
        Create a concise summary of current features and their subfeatures.
        """
        if not features:
            return "No features yet."
        
        summary_lines = []
        for idx, feature in enumerate(features, 1):
            name = feature.get("name", "")
            category = feature.get("category", "")
            complexity = feature.get("complexity", "medium")
            subfeatures = feature.get("subfeatures") or []
            if isinstance(subfeatures, list) and subfeatures:
                sub_names = [s.get("name", "") if isinstance(s, dict) else getattr(s, "name", "") for s in subfeatures]
                sub_names = [n for n in sub_names if n]
                summary_lines.append(f"{idx}. {name} ({category}, {complexity}) — subfeatures: {', '.join(sub_names) or '(none)'}")
            else:
                summary_lines.append(f"{idx}. {name} ({category}, {complexity}) — subfeatures: (none)")
        
        return "\n".join(summary_lines)
    
    def _normalize_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize and validate feature structure, preserving subfeatures.
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
            
            raw_subs = feature.get("subfeatures")
            subfeatures = []
            if isinstance(raw_subs, list):
                for sf in raw_subs:
                    if isinstance(sf, dict):
                        n = str(sf.get("name", "")).strip()
                        if n:
                            subfeatures.append({"name": n})
                    elif hasattr(sf, "name") and str(getattr(sf, "name", "")).strip():
                        subfeatures.append({"name": str(getattr(sf, "name", "")).strip()})
        
            if len(subfeatures) > 1:
                feature_name_lower = name.lower()
                subfeatures = [s for s in subfeatures if (s.get("name") or "").strip().lower() != feature_name_lower]
            if not subfeatures:
                subfeatures = [{"name": str(feature.get("name", "")).strip() or "Unnamed"}]
            
            normalized.append({
                "name": name,
                "category": category,
                "complexity": complexity.capitalize(),
                "subfeatures": subfeatures
            })
        
        return normalized

    def _normalize_feature_name_typo(self, name: str) -> str:
        """Fix common typos so the right feature appears in the table (e.g. lgout -> logout)."""
        if not name:
            return name
        fixes = {"lgout": "logout", "logut": "logout", "logotu": "logout"}
        return fixes.get(name.lower(), name)

    def _parse_add_feature_intent(self, instruction: str) -> Optional[str]:
        """Extract feature name from 'add X feature' / 'add a X feature' / 'add feature X'.
        Returns None when user asked to add a subfeature (e.g. 'add X as subfeature in Y')."""
        s = (instruction or "").strip()
        if not s or "add" not in s.lower() or "feature" not in s.lower():
            return None
        s_lower = s.lower()
        if "subfeature" in s_lower:
            return None
        if "subfeatire" in s_lower or "subfeatur" in s_lower:
            return None
        # "add a logout feature" or "add lgout feature"
        m = re.search(r"\badd\s+(?:a\s+)?(.+?)\s+feature\b", s, re.I)
        if m:
            name = re.sub(r"^(?:a|an)\s+", "", m.group(1).strip(), flags=re.I).strip()
            if name and name.lower() not in ("the", "new"):
                return name
        # "add feature logout"
        m = re.search(r"\badd\s+feature\s+(\S+)", s, re.I)
        if m:
            return m.group(1).strip()
        return None
