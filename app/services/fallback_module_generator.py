"""
Fallback Module Generator

Generates domain-specific modules using LLM when no template exists.
Used for unknown domains or domains that don't have predefined templates.
"""

from typing import List, Dict, Any
import logging

from app.services.llm_client import llm_complete_json

logger = logging.getLogger(__name__)


async def generate_fallback_modules(
    domain: str,
    description: str,
    build_options: List[str] = None
) -> List[str]:
    """
    Generate domain-specific modules using LLM when no template exists.
    Used for: unknown, or any domain without a predefined template.
    
    Args:
        domain: The detected domain name
        description: Project description (fused from additional_details + extracted_text)
        build_options: List of platforms to build (mobile, web, admin, backend, design)
        
    Returns:
        List of generated module strings with sub-features in parentheses
    """
    # Build context about what client wants to build
    build_context = ""
    if build_options:
        build_context = f"""
PLATFORMS TO BUILD:
- Mobile App: {"Yes - include mobile-specific features" if "mobile" in build_options else "No"}
- Web App: {"Yes - include web-specific features" if "web" in build_options else "No"}
- Admin Panel: {"Yes - include admin/back-office features" if "admin" in build_options else "No"}
- Backend/API: {"Yes - include API and server-side features" if "backend" in build_options else "No"}
- Design/UI: {"Yes - include UI/UX considerations" if "design" in build_options else "No"}
"""
    
    prompt = f"""You are a senior solutions architect analyzing a project requirement to identify essential feature modules.

PROJECT REQUIREMENT:
{description}

{build_context}

YOUR TASK:
Analyze this project and identify every essential feature module. Read the requirements carefully and extract modules based on what the client actually needs.

THINK ABOUT:
1. **Core Business Entities** - What are the main things being managed?
2. **User Roles** - What types of users are described?
3. **Specific Features** - What functionality did the client request?
4. **Integrations** - Are there external APIs or systems mentioned?
5. **Data & Reporting** - What data needs to be stored, viewed, or exported?
6. **Platform Requirements** - What features are needed for the selected platforms?

GUIDELINES:
- Extract modules based on the actual requirements, not generic templates
- Use the client's terminology and business domain
- Include specific integrations mentioned in the requirements
- Each module should represent a distinct functional area
- Include details in parentheses explaining key sub-features

FORMAT: Return a JSON object:
{{
    "modules": [
        "Module Name (key sub-feature 1, sub-feature 2, sub-feature 3, ...)",
        ...
    ],
    "reasoning": "Brief explanation of your module selection approach"
}}

EXAMPLE for a "Food Delivery Platform":
{{
    "modules": [
        "User Authentication (email/phone signup, social login, OTP verification, session management)",
        "Customer App Features (restaurant browsing, menu viewing, cart management, order placement, order tracking)",
        "Restaurant Management (menu builder, pricing, availability hours, order acceptance, prep time management)",
        "Driver Management (onboarding, availability toggle, order assignment, navigation, earnings tracking)",
        "Real-time Order Tracking (GPS tracking, status updates, ETA calculation, live map)",
        "Payment Processing (multiple payment methods, wallet, tips, refunds, restaurant payouts)",
        "Search & Discovery (restaurant search, cuisine filters, ratings sort, location-based results)",
        "Rating & Review System (restaurant ratings, driver ratings, food ratings, review moderation)",
        "Notification System (order updates, promotions, driver alerts, push/SMS/email)",
        "Promotions & Discounts (coupon codes, referral program, loyalty points, restaurant deals)",
        "Admin Dashboard (user management, restaurant approval, driver verification, analytics, dispute handling)",
        "Customer Support (help center, live chat, ticket system, refund processing)"
    ],
    "reasoning": "Food delivery requires three user types (customer, restaurant, driver) each with distinct features, plus real-time tracking, payments, and admin oversight"
}}"""

    messages = [
        {
            "role": "system", 
            "content": "You are a senior solutions architect. Generate comprehensive feature modules for software projects. Return valid JSON only."
        },
        {"role": "user", "content": prompt}
    ]
    
    try:
        parsed = await llm_complete_json(messages=messages, max_tokens=3000)
        modules = parsed.get("modules", [])
        reasoning = parsed.get("reasoning", "")
        
        logger.info(f"Generated {len(modules)} fallback modules for domain: {domain}. Reasoning: {reasoning}")
        
        if not modules:
            logger.warning("No modules returned from LLM, using basic fallback")
            return _get_basic_fallback_modules()
        
        return modules
    except Exception as e:
        logger.error(f"Error generating fallback modules: {e}. Using basic fallback.")
        return _get_basic_fallback_modules()


def _get_basic_fallback_modules() -> List[str]:
    """
    Return basic fallback modules when LLM is unavailable.
    These are generic modules that apply to most software projects.
    """
    return [
        "User Authentication & Authorization (OAuth2, JWT, role-based access, MFA)",
        "Admin Dashboard (user management, content management, analytics)",
        "Database & Data Management (CRUD operations, data validation, migrations)",
        "API Layer (RESTful endpoints, error handling, rate limiting)",
        "Search & Filtering (text search, filters, sorting, pagination)",
        "Notification System (email, in-app notifications, alerts)",
        "Settings & Configuration (application settings, user preferences)",
        "Logging & Monitoring (audit logs, error tracking, performance monitoring)",
    ]
