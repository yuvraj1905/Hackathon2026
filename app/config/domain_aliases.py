"""
Domain Aliases Configuration

Maps domain detection output names to domain template names.
Handles mismatches between what the Domain Detection Agent outputs
and what exists in DOMAIN_TEMPLATES.
"""

from typing import Optional


DOMAIN_ALIASES = {
    # Direct mismatches - detection name -> template name
    "education": "edtech",
    "social_media": "social_media_platform",
    "iot": "iot_platform",
    
    # Enterprise mappings (default to saas-like structure)
    "enterprise": "saas",
    
    # Generic app types -> closest domain template
    # These will use the template as a base, LLM will select relevant modules
    "mobile_app": "mobile_app",  # Now has its own template
    "web_app": "web_app",        # Now has its own template
    
    # Specialized domains - these have their own templates now
    "ai_ml": "ai_ml",
    "blockchain": "blockchain",
}

# Domains that should use LLM fallback to generate modules from scratch
# These domains are too varied for static templates - LLM generates custom modules
DOMAINS_NEEDING_FALLBACK = {
    "unknown",
    "enterprise",  # Enterprise systems are too varied (equine mgmt, property mgmt, etc.)
}

# Domains that exist in detection but map directly to templates (no alias needed)
DIRECT_MAPPING_DOMAINS = {
    "ecommerce",
    "fintech", 
    "healthcare",
    "saas",
    "marketplace",
    "edtech",
    "logistics",
    "crm",
    "hrms",
    "real_estate",
    "project_management",
    "social_media_platform",
    "food_delivery",
    "travel_booking",
    "iot_platform",
    "insurance",
}


def resolve_domain_alias(detected_domain: str) -> str:
    """
    Resolve a detected domain to its template domain name.
    
    Args:
        detected_domain: Domain string from Domain Detection Agent
        
    Returns:
        Template domain name to use for module lookup
    """
    domain_lower = detected_domain.lower().strip()
    
    # Check if it's a direct mapping (no alias needed)
    if domain_lower in DIRECT_MAPPING_DOMAINS:
        return domain_lower
    
    # Check if there's an alias
    if domain_lower in DOMAIN_ALIASES:
        return DOMAIN_ALIASES[domain_lower]
    
    # Default: return as-is (will trigger fallback if not in templates)
    return domain_lower


def should_use_fallback(detected_domain: str) -> bool:
    """
    Check if this domain should use LLM fallback for module generation.
    
    Args:
        detected_domain: Domain string from Domain Detection Agent
        
    Returns:
        True if LLM fallback should be used
    """
    return detected_domain.lower().strip() in DOMAINS_NEEDING_FALLBACK
