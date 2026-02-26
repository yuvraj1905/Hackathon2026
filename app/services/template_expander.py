from app.config.domain_templates import DOMAIN_TEMPLATES


class TemplateExpander:
    
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
        domain_lower = domain.lower()
        
        if domain_lower not in DOMAIN_TEMPLATES:
            return description
        
        modules = DOMAIN_TEMPLATES[domain_lower]
        
        if not modules:
            return description
        
        expanded = f"{description}\n\n"
        expanded += f"Required Core Modules for {domain_lower.upper()}:\n"
        
        for idx, module in enumerate(modules, 1):
            expanded += f"{idx}. {module}\n"
        
        return expanded.strip()
