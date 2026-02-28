"""
Smart Template Expander Service

Intelligently selects relevant modules from domain templates based on
project description, build options, and additional context using LLM.
"""

from typing import List, Tuple, Optional, Dict, Any
import logging

from app.config.domain_templates import DOMAIN_TEMPLATES
from app.config.domain_aliases import resolve_domain_alias, should_use_fallback
from app.services.llm_client import LLMClient, parse_json_response

logger = logging.getLogger(__name__)


class SmartTemplateExpander:
    """
    Smart template expander that uses LLM to select relevant modules
    instead of dumping all modules blindly.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-4.1-nano",
        timeout: float = 60.0,
        max_retries: int = 2
    ):
        self.llm_client = LLMClient(
            api_key=api_key,
            model=model,
            timeout=timeout,
            max_retries=max_retries
        )
    
    async def expand(
        self,
        domain: str,
        description: str,
        build_options: List[str] = None,
        additional_context: str = None
    ) -> Tuple[str, List[str]]:
        """
        Smart expansion using LLM to select relevant modules.
        
        Args:
            domain: Detected domain from Domain Detection Agent
            description: Project description (fused from additional_details + extracted_text)
            build_options: List of platforms to build (mobile, web, admin, backend, design)
            additional_context: Any additional context from user
            
        Returns:
            Tuple of (enriched_description, selected_modules)
        """
        # Step 1: Resolve domain alias
        resolved_domain = resolve_domain_alias(domain)
        logger.info(f"Domain resolved: {domain} -> {resolved_domain}")
        
        # Step 2: Check if we should use fallback for this domain
        # Use fallback for: unknown domains, enterprise domains, or very detailed requirements
        use_fallback = (
            should_use_fallback(domain) or 
            resolved_domain not in DOMAIN_TEMPLATES or
            self._should_use_fallback_for_rich_document(description)
        )
        
        if use_fallback:
            logger.info(f"Using LLM fallback for domain: {domain} (resolved: {resolved_domain})")
            # Import here to avoid circular imports
            from app.services.fallback_module_generator import generate_fallback_modules
            
            modules = await generate_fallback_modules(
                domain=domain,
                description=description,
                build_options=build_options
            )
            enriched = self._build_enriched_description(description, modules, domain)
            return enriched, modules
        
        # Step 3: Get all modules for this domain
        all_modules = DOMAIN_TEMPLATES[resolved_domain]
        
        # Step 4: Use LLM to select relevant modules
        selected_modules = await self._select_relevant_modules(
            all_modules=all_modules,
            description=description,
            build_options=build_options or [],
            additional_context=additional_context,
            domain=resolved_domain
        )
        
        # Step 5: Build enriched description
        enriched = self._build_enriched_description(description, selected_modules, resolved_domain)
        
        return enriched, selected_modules
    
    async def _select_relevant_modules(
        self,
        all_modules: List[str],
        description: str,
        build_options: List[str],
        additional_context: str,
        domain: str
    ) -> List[str]:
        """
        Use LLM to select which modules from the template are relevant for this project.
        """
        # Build context about what client wants
        build_context = ""
        if build_options:
            build_context = f"""
PLATFORMS TO BUILD:
- Mobile App: {"Yes" if "mobile" in build_options else "No"}
- Web App: {"Yes" if "web" in build_options else "No"}
- Admin Panel: {"Yes" if "admin" in build_options else "No"}
- Backend/API: {"Yes" if "backend" in build_options else "No"}
- Design/UI: {"Yes" if "design" in build_options else "No"}
"""
        
        # Format modules list
        modules_list = "\n".join(f"{i+1}. {m}" for i, m in enumerate(all_modules))
        
        prompt = f"""You are a senior solutions architect scoping a {domain} project. Review the project requirements and select the modules that are ESSENTIAL for this specific project.

PROJECT REQUIREMENT:
{description}

{build_context}
Additional Context: {additional_context or "None provided"}

AVAILABLE MODULES FOR {domain.upper()} PROJECTS:
{modules_list}

YOUR TASK:
From the available modules above, select ALL modules that are:

1. **Explicitly Required** - Directly mentioned or clearly implied in the project description
2. **Core Dependencies** - Required for other selected features to work (e.g., Auth is needed for any user-facing feature)
3. **Industry Standard** - Expected in any {domain} product (e.g., Payment Gateway for ecommerce)
4. **Platform Requirements** - Needed based on the platforms being built (mobile/web/admin)

DO NOT select modules that are:
- Clearly out of scope based on the description
- Advanced features not mentioned when the project seems basic
- Platform-specific features for platforms not being built (e.g., skip mobile push notifications if mobile=No)

IMPORTANT: Select ALL essential modules. Don't artificially limit the selection - if the project needs 15 modules, select 15. If it only needs 6, select 6. Base your decision purely on what this specific project requires.

FORMAT: Return a JSON object:
{{
    "selected_modules": ["Module 1 name exactly as listed", "Module 2 name exactly as listed", ...],
    "excluded_modules": ["Module X", "Module Y"],
    "reasoning": "Brief explanation of selection criteria for this project"
}}"""

        messages = [
            {"role": "system", "content": "You are a senior solutions architect. Select relevant modules based on project requirements. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.llm_client.complete(
                messages=messages,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            parsed = parse_json_response(response)
            
            selected = parsed.get("selected_modules", [])
            reasoning = parsed.get("reasoning", "")
            
            logger.info(f"Module selection: {len(selected)}/{len(all_modules)} modules selected. Reasoning: {reasoning}")
            
            # Validate that selected modules exist in all_modules
            # Use fuzzy matching for module names
            validated_modules = []
            all_modules_lower = {m.lower(): m for m in all_modules}
            
            for selected_module in selected:
                selected_lower = selected_module.lower()
                # Exact match
                if selected_lower in all_modules_lower:
                    validated_modules.append(all_modules_lower[selected_lower])
                else:
                    # Partial match - find modules that contain the selection or vice versa
                    for mod_lower, mod_original in all_modules_lower.items():
                        if selected_lower in mod_lower or mod_lower in selected_lower:
                            if mod_original not in validated_modules:
                                validated_modules.append(mod_original)
                            break
                    else:
                        # If still no match, add the original (might be slightly different wording)
                        # Find closest match
                        for mod_original in all_modules:
                            if selected_module.split("(")[0].strip().lower() in mod_original.lower():
                                if mod_original not in validated_modules:
                                    validated_modules.append(mod_original)
                                break
            
            # If validation resulted in empty list, fall back to all modules
            if not validated_modules:
                logger.warning("Module validation resulted in empty list, using all modules")
                return all_modules
            
            return validated_modules
            
        except Exception as e:
            logger.error(f"Error in module selection LLM call: {e}. Falling back to all modules.")
            return all_modules
    
    def _should_use_fallback_for_rich_document(self, description: str) -> bool:
        """
        Check if the description is rich enough to warrant using LLM fallback
        instead of template-based selection.
        
        Rich documents with specific requirements are better handled by LLM
        that can extract exact features from the document.
        
        Args:
            description: The project description (may include extracted document text)
            
        Returns:
            True if LLM fallback should be used
        """
        if not description:
            return False
        
        # If description is very long (likely a full requirements doc), use fallback
        if len(description) > 3000:
            logger.info("Using fallback: Long document detected (>3000 chars)")
            return True
        
        # If description contains typical requirements doc keywords, use fallback
        requirements_keywords = [
            "in-scope features",
            "out-of-scope",
            "user requirements",
            "functional requirements",
            "non-functional requirements",
            "scope of work",
            "project overview",
            "stakeholders",
            "user types",
            "user roles",
            "technical requirements",
        ]
        
        description_lower = description.lower()
        keyword_matches = sum(1 for kw in requirements_keywords if kw in description_lower)
        
        if keyword_matches >= 3:
            logger.info(f"Using fallback: Requirements document detected ({keyword_matches} keywords matched)")
            return True
        
        return False
    
    def _build_enriched_description(
        self,
        description: str,
        modules: List[str],
        domain: str
    ) -> str:
        """
        Build the enriched description with selected modules.
        """
        if not modules:
            return description
        
        enriched = f"{description}\n\n"
        enriched += f"Selected Core Modules for {domain.upper()} Project:\n"
        
        for idx, module in enumerate(modules, 1):
            enriched += f"{idx}. {module}\n"
        
        return enriched.strip()


# Backward compatibility: Keep the old TemplateExpander class for non-async usage
class TemplateExpander:
    """
    Legacy template expander for backward compatibility.
    Use SmartTemplateExpander for new code.
    """
    
    @staticmethod
    def expand(domain: str, description: str) -> str:
        """
        Expand project description with domain-specific required modules.
        Deterministic, rule-based expansion with no LLM calls.
        
        Args:
            domain: Domain identifier (e.g., 'ecommerce', 'saas')
            description: Original project description
            
        Returns:
            Expanded description with required modules appended
        """
        # Use domain alias resolution
        resolved_domain = resolve_domain_alias(domain)
        
        if resolved_domain not in DOMAIN_TEMPLATES:
            return description
        
        modules = DOMAIN_TEMPLATES[resolved_domain]
        
        if not modules:
            return description
        
        expanded = f"{description}\n\n"
        expanded += f"Required Core Modules for {resolved_domain.upper()}:\n"
        
        for idx, module in enumerate(modules, 1):
            expanded += f"{idx}. {module}\n"
        
        return expanded.strip()
