from typing import Dict, Any, List, Set
from app.agents.base_agent import BaseAgent


class TechStackAgent(BaseAgent):
    """
    Intelligent Tech Stack Recommendation Agent
    
    Recommends technology stack based on:
    - Target platforms (web, mobile, admin, backend)
    - Features and sub-features
    - Complexity of UI/animations
    - Third-party service requirements
    """
    
    # ==========================================================================
    # PLATFORM-BASED FRONTEND MAPPING
    # ==========================================================================
    
    PLATFORM_FRONTEND_MAPPING = {
        "web": {
            "framework": "Next.js",
            "language": "TypeScript",
            "styling": "TailwindCSS",
            "state_management": "Zustand/Redux Toolkit",
            "justification": "Next.js provides SSR/SSG for SEO, fast page loads, and excellent developer experience with TypeScript."
        },
        "admin": {
            "framework": "Next.js",
            "language": "TypeScript", 
            "styling": "TailwindCSS",
            "ui_library": "Shadcn/UI or Ant Design",
            "state_management": "Zustand/Redux Toolkit",
            "justification": "Next.js with component libraries enables rapid admin dashboard development with pre-built UI components."
        },
        "mobile_simple": {
            "framework": "React Native",
            "language": "TypeScript",
            "styling": "StyleSheet/NativeWind",
            "navigation": "React Navigation",
            "state_management": "Zustand/Redux Toolkit",
            "build_service": "Expo EAS",
            "justification": "React Native is ideal for apps with simple UI/animations. Code sharing with web (Next.js) and faster development cycle."
        },
        "mobile_complex": {
            "framework": "Flutter",
            "language": "Dart",
            "styling": "Flutter Widgets",
            "state_management": "Riverpod/BLoC",
            "build_service": "Codemagic/Fastlane",
            "justification": "Flutter excels at complex animations, custom UI, and pixel-perfect designs with 60fps performance."
        },
        "mobile_with_web": {
            "framework": "React Native",
            "language": "TypeScript",
            "styling": "StyleSheet/NativeWind",
            "navigation": "React Navigation",
            "state_management": "Zustand/Redux Toolkit",
            "build_service": "Expo EAS",
            "justification": "React Native chosen for maximum code sharing with Next.js web app. Shared business logic and similar developer experience."
        }
    }
    
    # ==========================================================================
    # BACKEND CONFIGURATION (NestJS Only)
    # ==========================================================================
    
    BACKEND_CONFIG = {
        "framework": "NestJS",
        "language": "TypeScript",
        "orm": "Prisma",
        "api_style": "REST + GraphQL (optional)",
        "authentication": "Passport.js + JWT",
        "validation": "class-validator",
        "documentation": "Swagger/OpenAPI",
        "testing": "Jest",
        "logging": "Winston/Pino",
        "justification": "NestJS provides enterprise-grade architecture with dependency injection, modularity, and excellent TypeScript support."
    }
    
    # ==========================================================================
    # DATABASE RECOMMENDATIONS
    # ==========================================================================
    
    DATABASE_RULES = {
        "relational_triggers": [
            "payment", "transaction", "order", "invoice", "billing",
            "user_management", "role", "permission", "subscription",
            "booking", "reservation", "inventory", "audit", "compliance",
            "financial", "accounting", "reporting", "analytics"
        ],
        "nosql_triggers": [
            "content_management", "cms", "blog", "article",
            "product_catalog", "catalog", "flexible_schema",
            "real_time", "chat", "messaging", "feed", "timeline",
            "iot", "sensor_data", "logging", "event_sourcing"
        ],
        "cache_triggers": [
            "session", "authentication", "otp", "verification",
            "rate_limiting", "leaderboard", "real_time", "queue",
            "temporary_data", "cart", "wishlist"
        ],
        "search_triggers": [
            "search", "full_text_search", "product_search",
            "autocomplete", "filtering", "faceted_search"
        ]
    }
    
    DATABASE_OPTIONS = {
        "postgresql": {
            "name": "PostgreSQL",
            "use_case": "Primary relational database",
            "justification": "ACID compliance, complex queries, transactions, JSON support, excellent for structured data with relationships."
        },
        "mongodb": {
            "name": "MongoDB",
            "use_case": "Document storage, flexible schemas",
            "justification": "Schema flexibility, horizontal scaling, ideal for content-heavy apps and rapid prototyping."
        },
        "redis": {
            "name": "Redis",
            "use_case": "Caching, sessions, real-time data",
            "justification": "In-memory storage for lightning-fast reads, session management, rate limiting, and pub/sub messaging."
        },
        "elasticsearch": {
            "name": "Elasticsearch",
            "use_case": "Full-text search, analytics",
            "justification": "Powerful search capabilities, autocomplete, faceted search, and log analytics."
        }
    }
    
    # ==========================================================================
    # INFRASTRUCTURE OPTIONS
    # ==========================================================================
    
    INFRASTRUCTURE_OPTIONS = {
        "aws": {
            "name": "AWS",
            "services": ["EC2/ECS", "RDS", "S3", "CloudFront", "Lambda"],
            "best_for": ["enterprise", "scalability", "global_reach", "compliance"],
            "justification": "Industry standard with comprehensive services, excellent scalability, and compliance certifications."
        },
        "gcp": {
            "name": "Google Cloud Platform",
            "services": ["Cloud Run", "Cloud SQL", "Cloud Storage", "Firebase"],
            "best_for": ["ml_ai", "data_analytics", "firebase_integration"],
            "justification": "Superior for ML/AI workloads, BigQuery analytics, and seamless Firebase integration."
        },
        "docker": {
            "name": "Docker",
            "use_case": "Containerization",
            "justification": "Consistent environments across development and production, easy scaling, and deployment."
        },
        "kubernetes": {
            "name": "Kubernetes",
            "use_case": "Container orchestration",
            "best_for": ["microservices", "high_availability", "auto_scaling"],
            "justification": "Production-grade container orchestration for complex deployments and auto-scaling."
        },
        "nginx": {
            "name": "Nginx",
            "use_case": "Reverse proxy, load balancing",
            "justification": "High-performance reverse proxy, SSL termination, and load balancing."
        },
        "vercel": {
            "name": "Vercel",
            "use_case": "Frontend deployment",
            "best_for": ["nextjs", "static_sites", "edge_functions"],
            "justification": "Optimized for Next.js with automatic deployments, edge network, and zero-config."
        },
        # Mobile App Deployment Infrastructure
        "expo_eas": {
            "name": "Expo EAS (Expo Application Services)",
            "use_case": "React Native app build and deployment",
            "services": {
                "eas_build": "Cloud builds for iOS and Android without local setup",
                "eas_submit": "Automated submission to App Store and Google Play",
                "eas_update": "Over-the-air updates for instant deployments"
            },
            "justification": "Streamlined React Native deployment with cloud builds, OTA updates, and automated store submissions."
        },
        "codemagic": {
            "name": "Codemagic",
            "use_case": "Flutter app CI/CD",
            "services": {
                "build": "Cloud builds for iOS and Android",
                "test": "Automated testing",
                "deploy": "App Store and Google Play deployment"
            },
            "justification": "Purpose-built CI/CD for Flutter with native Apple Silicon builds and fast compilation."
        },
        "fastlane": {
            "name": "Fastlane",
            "use_case": "Mobile app automation",
            "services": {
                "match": "Code signing management",
                "pilot": "TestFlight deployment",
                "deliver": "App Store metadata and submission",
                "supply": "Google Play deployment"
            },
            "justification": "Industry-standard mobile automation for certificates, screenshots, and store deployments."
        },
        "app_store_connect": {
            "name": "Apple App Store Connect",
            "use_case": "iOS app distribution",
            "services": ["TestFlight", "App Store Distribution", "App Analytics"],
            "justification": "Required for iOS app distribution with TestFlight beta testing."
        },
        "google_play_console": {
            "name": "Google Play Console",
            "use_case": "Android app distribution",
            "services": ["Internal Testing", "Closed Testing", "Open Testing", "Production"],
            "justification": "Required for Android app distribution with staged rollouts."
        }
    }
    
    # ==========================================================================
    # THIRD-PARTY SERVICES MAPPING (Feature/Sub-feature based)
    # ==========================================================================
    
    THIRD_PARTY_SERVICES = {
        # Authentication & Authorization
        "authentication": {
            "services": [
                {"name": "Firebase Auth", "platforms": ["web", "mobile"], "justification": "Easy integration, social logins, phone auth"},
                {"name": "Auth0", "platforms": ["web", "mobile"], "justification": "Enterprise-grade, SSO, MFA support"},
                {"name": "Clerk", "platforms": ["web"], "justification": "Modern auth with great DX for Next.js"}
            ],
            "triggers": ["login", "signup", "authentication", "auth", "social_login", "sso", "mfa", "2fa"]
        },
        
        # Payments (Global Payment Providers)
        "payments": {
            "services": [
                {"name": "Stripe", "platforms": ["web", "mobile", "backend"], "justification": "Industry standard, comprehensive payment APIs, 135+ currencies, global coverage"},
                {"name": "PayPal", "platforms": ["web", "mobile"], "justification": "Trusted worldwide, buyer protection, 400M+ active users"},
                {"name": "Braintree", "platforms": ["web", "mobile"], "justification": "PayPal-owned, supports PayPal + cards + Venmo, great for marketplaces"},
                {"name": "Square", "platforms": ["web", "mobile"], "justification": "Excellent for in-person + online payments, POS integration"},
                {"name": "Adyen", "platforms": ["web", "mobile", "backend"], "justification": "Enterprise-grade, unified commerce, used by Netflix, Uber, Spotify"},
                {"name": "Worldpay", "platforms": ["web", "backend"], "justification": "Global reach, 120+ currencies, strong in Europe"},
                {"name": "Checkout.com", "platforms": ["web", "mobile", "backend"], "justification": "High-growth companies, excellent API, competitive rates"},
                {"name": "Razorpay", "platforms": ["web", "mobile"], "justification": "Best for Indian market with UPI, net banking support"}
            ],
            "triggers": ["payment", "checkout", "transaction", "billing", "invoice", "credit_card", "debit_card"]
        },
        
        # Subscriptions (Platform-specific)
        "subscriptions": {
            "services": [
                {"name": "Stripe Billing", "platforms": ["web", "backend"], "justification": "Subscription management, recurring payments, invoicing, usage-based billing"},
                {"name": "RevenueCat", "platforms": ["react_native"], "justification": "Cross-platform subscription management, analytics, A/B testing for React Native"},
                {"name": "purchases_flutter", "platforms": ["flutter"], "justification": "Native IAP wrapper for Flutter apps with unified API for iOS and Android"}
            ],
            "triggers": ["subscription", "recurring", "membership", "plan", "premium", "in_app_purchase", "iap"]
        },
        
        # KYC & Verification (Stripe Identity Only)
        "kyc": {
            "services": [
                {"name": "Stripe Identity", "platforms": ["web", "mobile", "backend"], "justification": "Document verification, selfie verification, identity checks, seamless Stripe integration, global ID support"}
            ],
            "triggers": ["kyc", "identity_verification", "document_verification", "aml", "compliance", "id_verification"]
        },
        
        # Push Notifications
        "push_notifications": {
            "services": [
                {"name": "Firebase Cloud Messaging (FCM)", "platforms": ["web", "flutter"], "justification": "Free, reliable push notifications, analytics"},
                {"name": "Expo Notifications", "platforms": ["react_native"], "justification": "Simplified push for React Native/Expo with unified API"},
                {"name": "OneSignal", "platforms": ["web", "mobile"], "justification": "Cross-platform with rich analytics, segmentation, A/B testing"}
            ],
            "triggers": ["push_notification", "notification", "alert", "reminder"]
        },
        
        # Email Notifications (SendGrid Only)
        "email_notifications": {
            "services": [
                {"name": "SendGrid", "platforms": ["backend"], "justification": "Reliable transactional emails, email templates, analytics, high deliverability, 100B+ emails/month"}
            ],
            "triggers": ["email", "email_notification", "transactional_email", "newsletter", "email_marketing"]
        },
        
        # SMS Notifications (Twilio Only)
        "sms_notifications": {
            "services": [
                {"name": "Twilio", "platforms": ["backend"], "justification": "Global SMS coverage 180+ countries, voice, WhatsApp, programmable messaging, OTP verification"}
            ],
            "triggers": ["sms", "otp", "phone_verification", "text_message", "whatsapp"]
        },
        
        # Real-time Features
        "realtime": {
            "services": [
                {"name": "Socket.io", "platforms": ["web", "mobile", "backend"], "justification": "Real-time bidirectional communication, fallback support"},
                {"name": "Pusher", "platforms": ["web", "mobile"], "justification": "Managed real-time infrastructure, presence channels"},
                {"name": "Firebase Realtime DB", "platforms": ["web", "mobile"], "justification": "Real-time sync with offline support"},
                {"name": "Ably", "platforms": ["web", "mobile"], "justification": "Enterprise real-time messaging, guaranteed delivery"}
            ],
            "triggers": ["real_time", "realtime", "live_update", "websocket", "chat", "messaging", "live_tracking"]
        },
        
        # File Storage & Media
        "file_storage": {
            "services": [
                {"name": "AWS S3", "platforms": ["backend"], "justification": "Scalable object storage, industry standard, 99.999999999% durability"},
                {"name": "Cloudinary", "platforms": ["web", "mobile"], "justification": "Image/video optimization, transformations, CDN delivery"},
                {"name": "Firebase Storage", "platforms": ["web", "mobile"], "justification": "Easy integration with Firebase ecosystem, security rules"}
            ],
            "triggers": ["file_upload", "image_upload", "media", "storage", "document_upload", "attachment", "video_upload"]
        },
        
        # Maps & Location
        "maps": {
            "services": [
                {"name": "Google Maps", "platforms": ["web", "mobile"], "justification": "Comprehensive mapping, places API, directions, geocoding"},
                {"name": "Mapbox", "platforms": ["web", "mobile"], "justification": "Customizable maps, better pricing, offline support"}
            ],
            "triggers": ["map", "location", "geolocation", "tracking", "navigation", "places", "address", "directions"]
        },
        
        # Analytics & Monitoring
        "analytics": {
            "services": [
                {"name": "Google Analytics", "platforms": ["web"], "justification": "Industry standard web analytics, free tier"},
                {"name": "Mixpanel", "platforms": ["web", "mobile"], "justification": "Product analytics, user behavior, funnels"},
                {"name": "Amplitude", "platforms": ["web", "mobile"], "justification": "Advanced product analytics, cohort analysis"},
                {"name": "Firebase Analytics", "platforms": ["mobile"], "justification": "Free mobile analytics, crash reporting integration"}
            ],
            "triggers": ["analytics", "tracking", "user_behavior", "metrics", "reporting", "funnel"]
        },
        
        # Error Monitoring
        "error_monitoring": {
            "services": [
                {"name": "Sentry", "platforms": ["web", "mobile", "backend"], "justification": "Error tracking, performance monitoring, release tracking"},
                {"name": "LogRocket", "platforms": ["web"], "justification": "Session replay, error tracking, user insights"}
            ],
            "triggers": ["error_tracking", "monitoring", "debugging", "crash_reporting", "performance"]
        },
        
        # Video & Streaming
        "video": {
            "services": [
                {"name": "Twilio Video", "platforms": ["web", "mobile"], "justification": "Video calls, conferencing, recording"},
                {"name": "Agora", "platforms": ["web", "mobile"], "justification": "Real-time video, low latency, large scale"},
                {"name": "Mux", "platforms": ["web", "mobile"], "justification": "Video streaming, encoding, analytics"},
                {"name": "Daily.co", "platforms": ["web", "mobile"], "justification": "Video calls API, simple integration"}
            ],
            "triggers": ["video_call", "video_conference", "streaming", "live_video", "webrtc", "video_chat"]
        },
        
        # Search
        "search": {
            "services": [
                {"name": "Algolia", "platforms": ["web", "mobile"], "justification": "Fast search, autocomplete, faceting, typo tolerance"},
                {"name": "Elasticsearch", "platforms": ["backend"], "justification": "Self-hosted powerful search, full control"},
                {"name": "Meilisearch", "platforms": ["backend"], "justification": "Open-source, easy to deploy, fast"}
            ],
            "triggers": ["search", "full_text_search", "autocomplete", "product_search", "filtering"]
        },
        
        # AI & ML
        "ai_ml": {
            "services": [
                {"name": "OpenAI API", "platforms": ["backend"], "justification": "GPT models, embeddings, DALL-E, Whisper"},
                {"name": "Anthropic Claude", "platforms": ["backend"], "justification": "Advanced reasoning, long context, safe AI"},
                {"name": "AWS Bedrock", "platforms": ["backend"], "justification": "Multiple AI models, enterprise-ready"},
                {"name": "Google Vertex AI", "platforms": ["backend"], "justification": "ML platform, custom models, AutoML"}
            ],
            "triggers": ["ai", "ml", "chatbot", "recommendation", "nlp", "image_generation", "llm", "gpt"]
        },
        
        # CMS (Strapi Only)
        "cms": {
            "services": [
                {"name": "Strapi", "platforms": ["backend"], "justification": "Open-source headless CMS, self-hosted, customizable, REST + GraphQL APIs, admin panel included"}
            ],
            "triggers": ["cms", "content_management", "blog", "article", "content", "headless_cms"]
        },
        
        # Social Features
        "social": {
            "services": [
                {"name": "Stream", "platforms": ["web", "mobile"], "justification": "Activity feeds, chat, notifications"},
                {"name": "Firebase", "platforms": ["web", "mobile"], "justification": "Real-time database, auth, social features"}
            ],
            "triggers": ["feed", "activity_feed", "social", "following", "likes", "comments", "share"]
        },
        
        # Calendar & Scheduling
        "calendar": {
            "services": [
                {"name": "Calendly API", "platforms": ["web", "backend"], "justification": "Scheduling, calendar integrations"},
                {"name": "Cal.com", "platforms": ["web", "backend"], "justification": "Open-source scheduling, self-hostable"},
                {"name": "Nylas", "platforms": ["backend"], "justification": "Calendar, email, contacts APIs"}
            ],
            "triggers": ["calendar", "scheduling", "booking", "appointment", "meeting", "availability"]
        }
    }
    
    # ==========================================================================
    # COMPLEXITY INDICATORS FOR MOBILE FRAMEWORK SELECTION
    # ==========================================================================
    
    COMPLEX_UI_INDICATORS = [
        "complex_animation", "custom_animation", "particle_effect",
        "3d", "ar", "vr", "augmented_reality", "virtual_reality",
        "custom_ui", "custom_widget", "pixel_perfect",
        "game", "gaming", "interactive_graphics",
        "complex_gesture", "multi_touch", "drawing",
        "video_editing", "image_editing", "photo_editor",
        "custom_chart", "data_visualization", "canvas",
        "shader", "opengl", "metal", "skia"
    ]
    
    SIMPLE_UI_INDICATORS = [
        "crud", "list", "form", "table", "basic_animation",
        "standard_ui", "material_design", "simple_navigation",
        "basic_chart", "simple_transition", "standard_components"
    ]

    # ==========================================================================
    # MAIN EXECUTION METHOD
    # ==========================================================================
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive tech stack recommendation.
        
        Args:
            input_data: Dict containing:
                - platforms: List of target platforms ["web", "mobile", "admin", "backend"]
                - features: List of feature dicts with 'name' and 'sub_features'
                - domain: Optional domain type (ecommerce, fintech, etc.)
                
        Returns:
            Dict with complete tech stack recommendation
        """
        platforms = input_data.get("platforms", [])
        features = input_data.get("features", [])
        domain = input_data.get("domain", "").lower()
        
        # Normalize platforms
        platforms = [p.lower() for p in platforms]
        
        # Extract all feature names and sub-features for analysis
        all_features = self._extract_all_features(features)
        
        # Determine mobile complexity
        mobile_complexity = self._determine_mobile_complexity(all_features)
        
        # Build recommendations
        frontend_stack = self._recommend_frontend(platforms, mobile_complexity)
        backend_stack = self._recommend_backend()
        database_stack = self._recommend_database(all_features, domain)
        infrastructure_stack = self._recommend_infrastructure(platforms, all_features, domain, mobile_complexity)
        third_party_services = self._recommend_third_party_services(all_features, platforms, mobile_complexity)
        
        # Generate overall justification
        overall_justification = self._generate_justification(
            platforms, frontend_stack, backend_stack, 
            database_stack, infrastructure_stack, mobile_complexity
        )
        
        return {
            "platforms": platforms,
            "frontend": frontend_stack,
            "backend": backend_stack,
            "database": database_stack,
            "infrastructure": infrastructure_stack,
            "third_party_services": third_party_services,
            "justification": overall_justification
        }
    
    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================
    
    def _extract_all_features(self, features: List[Dict]) -> Set[str]:
        """Extract all feature names and sub-features into a flat set."""
        all_features = set()
        
        for feature in features:
            # Add main feature name
            feature_name = feature.get("name", "").lower().replace(" ", "_")
            if feature_name:
                all_features.add(feature_name)
            
            # Add sub-features
            sub_features = feature.get("sub_features", [])
            for sub in sub_features:
                if isinstance(sub, dict):
                    sub_name = sub.get("name", "").lower().replace(" ", "_")
                else:
                    sub_name = str(sub).lower().replace(" ", "_")
                if sub_name:
                    all_features.add(sub_name)
        
        return all_features
    
    def _determine_mobile_complexity(self, features: Set[str]) -> str:
        """Determine if mobile app needs simple or complex UI framework."""
        complex_count = sum(1 for f in features if any(
            indicator in f for indicator in self.COMPLEX_UI_INDICATORS
        ))
        simple_count = sum(1 for f in features if any(
            indicator in f for indicator in self.SIMPLE_UI_INDICATORS
        ))
        
        # If more complex indicators or explicit complex features
        if complex_count > simple_count or complex_count >= 2:
            return "complex"
        return "simple"
    
    def _recommend_frontend(
        self, 
        platforms: List[str], 
        mobile_complexity: str
    ) -> Dict[str, Any]:
        """Recommend frontend technologies based on platforms."""
        frontend = {}
        
        has_web = "web" in platforms
        has_mobile = "mobile" in platforms
        has_admin = "admin" in platforms
        
        # Web App
        if has_web:
            frontend["web"] = {
                **self.PLATFORM_FRONTEND_MAPPING["web"],
                "type": "web_application"
            }
        
        # Admin Panel
        if has_admin:
            frontend["admin"] = {
                **self.PLATFORM_FRONTEND_MAPPING["admin"],
                "type": "admin_dashboard"
            }
        
        # Mobile App
        if has_mobile:
            # If building both web and mobile, prefer React Native for code sharing
            if has_web:
                frontend["mobile"] = {
                    **self.PLATFORM_FRONTEND_MAPPING["mobile_with_web"],
                    "type": "mobile_application"
                }
            elif mobile_complexity == "complex":
                frontend["mobile"] = {
                    **self.PLATFORM_FRONTEND_MAPPING["mobile_complex"],
                    "type": "mobile_application"
                }
            else:
                frontend["mobile"] = {
                    **self.PLATFORM_FRONTEND_MAPPING["mobile_simple"],
                    "type": "mobile_application"
                }
        
        return frontend
    
    def _recommend_backend(self) -> Dict[str, Any]:
        """Recommend backend technologies (NestJS only)."""
        return {
            **self.BACKEND_CONFIG,
            "type": "monolithic"
        }
    
    def _recommend_database(
        self, 
        features: Set[str], 
        domain: str
    ) -> Dict[str, Any]:
        """Recommend database technologies based on features."""
        databases = {
            "primary": None,
            "cache": None,
            "search": None,
            "recommendations": []
        }
        
        # Check for relational database needs
        needs_relational = any(
            trigger in feature 
            for feature in features 
            for trigger in self.DATABASE_RULES["relational_triggers"]
        )
        
        # Check for NoSQL needs
        needs_nosql = any(
            trigger in feature 
            for feature in features 
            for trigger in self.DATABASE_RULES["nosql_triggers"]
        )
        
        # Check for cache needs
        needs_cache = any(
            trigger in feature 
            for feature in features 
            for trigger in self.DATABASE_RULES["cache_triggers"]
        )
        
        # Check for search needs
        needs_search = any(
            trigger in feature 
            for feature in features 
            for trigger in self.DATABASE_RULES["search_triggers"]
        )
        
        # Domain-based defaults
        relational_domains = ["fintech", "healthcare", "ecommerce", "saas", "enterprise"]
        
        # Primary database selection
        if needs_relational or domain in relational_domains or not needs_nosql:
            databases["primary"] = {
                **self.DATABASE_OPTIONS["postgresql"],
                "recommended": True
            }
            databases["recommendations"].append(
                "PostgreSQL recommended as primary database for data integrity and complex queries."
            )
        
        # Add NoSQL if needed
        if needs_nosql:
            if databases["primary"]:
                databases["secondary"] = {
                    **self.DATABASE_OPTIONS["mongodb"],
                    "recommended": True
                }
                databases["recommendations"].append(
                    "MongoDB added for flexible schema requirements (content, catalogs)."
                )
            else:
                databases["primary"] = {
                    **self.DATABASE_OPTIONS["mongodb"],
                    "recommended": True
                }
        
        # Add cache (always recommend Redis)
        databases["cache"] = {
            **self.DATABASE_OPTIONS["redis"],
            "recommended": True
        }
        databases["recommendations"].append(
            "Redis for caching, sessions, rate limiting, and real-time features."
        )
        
        # Add search
        if needs_search:
            databases["search"] = {
                **self.DATABASE_OPTIONS["elasticsearch"],
                "recommended": True
            }
            databases["recommendations"].append(
                "Elasticsearch for full-text search and advanced filtering."
            )
        
        return databases
    
    def _recommend_infrastructure(
        self, 
        platforms: List[str],
        features: Set[str], 
        domain: str,
        mobile_complexity: str
    ) -> Dict[str, Any]:
        """Recommend infrastructure based on requirements."""
        infrastructure = {
            "cloud_provider": None,
            "containerization": None,
            "orchestration": None,
            "reverse_proxy": None,
            "frontend_hosting": None,
            "mobile_deployment": None,
            "recommendations": []
        }
        
        has_mobile = "mobile" in platforms
        has_web = "web" in platforms
        
        # Determine if using Flutter or React Native
        is_flutter = mobile_complexity == "complex" and has_mobile and not has_web
        is_react_native = has_mobile and not is_flutter
        
        # Cloud provider selection
        ml_indicators = ["ai", "ml", "machine_learning", "recommendation", "analytics"]
        has_ml = any(ind in features for ind in ml_indicators)
        
        if has_ml:
            infrastructure["cloud_provider"] = {
                **self.INFRASTRUCTURE_OPTIONS["gcp"],
                "recommended": True
            }
            infrastructure["recommendations"].append(
                "GCP recommended for ML/AI workloads and BigQuery analytics."
            )
        else:
            infrastructure["cloud_provider"] = {
                **self.INFRASTRUCTURE_OPTIONS["aws"],
                "recommended": True
            }
            infrastructure["recommendations"].append(
                "AWS recommended for comprehensive services and industry-standard reliability."
            )
        
        # Containerization (always recommend Docker)
        infrastructure["containerization"] = {
            **self.INFRASTRUCTURE_OPTIONS["docker"],
            "recommended": True
        }
        
        # Orchestration for complex apps
        complex_indicators = ["microservices", "high_availability", "auto_scaling", "enterprise"]
        if any(ind in features for ind in complex_indicators):
            infrastructure["orchestration"] = {
                **self.INFRASTRUCTURE_OPTIONS["kubernetes"],
                "recommended": True
            }
            infrastructure["recommendations"].append(
                "Kubernetes for container orchestration and auto-scaling."
            )
        
        # Reverse proxy
        infrastructure["reverse_proxy"] = {
            **self.INFRASTRUCTURE_OPTIONS["nginx"],
            "recommended": True
        }
        
        # Frontend hosting for web/admin
        if "web" in platforms or "admin" in platforms:
            infrastructure["frontend_hosting"] = {
                **self.INFRASTRUCTURE_OPTIONS["vercel"],
                "recommended": True
            }
            infrastructure["recommendations"].append(
                "Vercel for optimized Next.js deployment with edge network."
            )
        
        # Mobile app deployment infrastructure
        if has_mobile:
            mobile_deployment = {
                "app_stores": {
                    "ios": {
                        **self.INFRASTRUCTURE_OPTIONS["app_store_connect"],
                        "recommended": True
                    },
                    "android": {
                        **self.INFRASTRUCTURE_OPTIONS["google_play_console"],
                        "recommended": True
                    }
                }
            }
            
            if is_react_native:
                # React Native with Expo EAS
                mobile_deployment["build_service"] = {
                    **self.INFRASTRUCTURE_OPTIONS["expo_eas"],
                    "recommended": True
                }
                infrastructure["recommendations"].append(
                    "Expo EAS for React Native cloud builds, OTA updates, and automated store submissions."
                )
            else:
                # Flutter with Codemagic
                mobile_deployment["build_service"] = {
                    **self.INFRASTRUCTURE_OPTIONS["codemagic"],
                    "recommended": True
                }
                mobile_deployment["automation"] = {
                    **self.INFRASTRUCTURE_OPTIONS["fastlane"],
                    "recommended": True
                }
                infrastructure["recommendations"].append(
                    "Codemagic CI/CD for Flutter builds with Fastlane for app store automation."
                )
            
            infrastructure["mobile_deployment"] = mobile_deployment
        
        return infrastructure
    
    def _recommend_third_party_services(
        self,
        features: Set[str],
        platforms: List[str],
        mobile_complexity: str
    ) -> Dict[str, Any]:
        """
        Recommend third-party services: at most one service per platform.
        - Web + mobile: prefer one service that supports both; else one for web, one for mobile.
        - Web only: include backend services (one for web, one for backend when relevant).
        """
        services = {}
        has_web = "web" in platforms
        has_mobile = "mobile" in platforms
        is_flutter = mobile_complexity == "complex" and has_mobile and "web" not in platforms
        is_react_native = has_mobile and not is_flutter

        # When only web, we still want backend third-party services (e.g. Stripe on backend).
        want_backend = has_web or "backend" in platforms
        want_web = has_web
        want_mobile = has_mobile

        for category, config in self.THIRD_PARTY_SERVICES.items():
            triggers = config.get("triggers", [])
            if not any(trigger in feature for feature in features for trigger in triggers):
                continue

            applicable_services = []
            seen = set()
            for service in config["services"]:
                if id(service) in seen:
                    continue
                sp = service.get("platforms", [])
                if (
                    ("backend" in sp and want_backend)
                    or ("web" in sp and want_web)
                    or ("mobile" in sp and want_mobile)
                    or ("react_native" in sp and is_react_native)
                    or ("flutter" in sp and is_flutter)
                ):
                    applicable_services.append(service)
                    seen.add(id(service))

            if not applicable_services:
                continue

            # Pick at most one service per platform; prefer one that covers multiple.
            selected = self._pick_one_per_platform(
                applicable_services,
                want_web=want_web,
                want_mobile=want_mobile,
                want_backend=want_backend,
                is_react_native=is_react_native,
                is_flutter=is_flutter,
            )
            if selected:
                services[category] = {
                    "services": selected,
                    "triggered_by": [t for t in triggers if any(t in f for f in features)],
                }

        return services

    def _service_matches_platform(
        self,
        service: Dict,
        platform: str,
        is_react_native: bool,
        is_flutter: bool,
    ) -> bool:
        """Return True if this service supports the given platform."""
        sp = service.get("platforms", [])
        if platform == "web":
            return "web" in sp
        if platform == "mobile":
            return (
                "mobile" in sp
                or (is_react_native and "react_native" in sp)
                or (is_flutter and "flutter" in sp)
            )
        if platform == "backend":
            return "backend" in sp
        return False

    def _pick_one_per_platform(
        self,
        applicable_services: List[Dict],
        want_web: bool,
        want_mobile: bool,
        want_backend: bool,
        is_react_native: bool,
        is_flutter: bool,
    ) -> List[Dict]:
        """
        Select at most one service per platform. Prefer a single service that
        covers both web and mobile when both are wanted; else one per platform.
        """
        selected: List[Dict] = []
        used = set()  # id(service) to avoid duplicates

        def matches(s: Dict, platform: str) -> bool:
            return self._service_matches_platform(s, platform, is_react_native, is_flutter)

        # Web + mobile: prefer one service that has both
        if want_web and want_mobile:
            for s in applicable_services:
                if id(s) in used:
                    continue
                if matches(s, "web") and matches(s, "mobile"):
                    selected.append(s)
                    used.add(id(s))
                    return selected
            # Else one for web, one for mobile
            for s in applicable_services:
                if id(s) in used:
                    continue
                if matches(s, "web"):
                    selected.append(s)
                    used.add(id(s))
                    break
            for s in applicable_services:
                if id(s) in used:
                    continue
                if matches(s, "mobile"):
                    selected.append(s)
                    used.add(id(s))
                    break
            return selected

        # Web only (with backend): prefer one service that has both web and backend
        if want_web and want_backend and not want_mobile:
            for s in applicable_services:
                if id(s) in used:
                    continue
                if matches(s, "web") and matches(s, "backend"):
                    selected.append(s)
                    used.add(id(s))
                    return selected
            for s in applicable_services:
                if id(s) in used:
                    continue
                if matches(s, "web"):
                    selected.append(s)
                    used.add(id(s))
                    break
            for s in applicable_services:
                if id(s) in used:
                    continue
                if matches(s, "backend"):
                    selected.append(s)
                    used.add(id(s))
                    break
            return selected

        # Single platform or mobile + backend: one per platform
        for platform in ["web", "mobile", "backend"]:
            if platform == "web" and not want_web:
                continue
            if platform == "mobile" and not want_mobile:
                continue
            if platform == "backend" and not want_backend:
                continue
            for s in applicable_services:
                if id(s) in used:
                    continue
                if matches(s, platform):
                    selected.append(s)
                    used.add(id(s))
                    break

        return selected
    
    def _generate_justification(
        self,
        platforms: List[str],
        frontend: Dict,
        backend: Dict,
        database: Dict,
        infrastructure: Dict,
        mobile_complexity: str
    ) -> str:
        """Generate overall justification for the tech stack."""
        justifications = []
        
        # Platform justification
        if len(platforms) > 1:
            justifications.append(
                f"Multi-platform architecture targeting {', '.join(platforms)} with optimal code sharing."
            )
        
        # Frontend justification
        if "web" in frontend:
            justifications.append(frontend["web"].get("justification", ""))
        if "mobile" in frontend:
            justifications.append(frontend["mobile"].get("justification", ""))
        
        # Backend justification
        justifications.append(backend.get("justification", ""))
        
        # Database justification
        if database.get("recommendations"):
            justifications.extend(database["recommendations"][:2])
        
        # Infrastructure justification
        if infrastructure.get("recommendations"):
            justifications.extend(infrastructure["recommendations"][:2])
        
        # Mobile deployment justification
        if "mobile" in platforms:
            if mobile_complexity == "complex" and "web" not in platforms:
                justifications.append(
                    "Flutter selected for complex UI/animations with Codemagic for CI/CD."
                )
            else:
                justifications.append(
                    "React Native with Expo EAS for streamlined mobile deployment and OTA updates."
                )
        
        return " ".join(filter(None, justifications))


# ==========================================================================
# USAGE EXAMPLE
# ==========================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        agent = TechStackAgent()
        
        # Example input
        input_data = {
            "platforms": ["web", "mobile", "admin", "backend"],
            "domain": "ecommerce",
            "features": [
                {
                    "name": "User Authentication",
                    "sub_features": [
                        {"name": "Social Login"},
                        {"name": "Phone OTP"},
                        {"name": "2FA"}
                    ]
                },
                {
                    "name": "Payment",
                    "sub_features": [
                        {"name": "Credit Card"},
                        {"name": "Subscription"},
                        {"name": "In App Purchase"}
                    ]
                },
                {
                    "name": "Notifications",
                    "sub_features": [
                        {"name": "Push Notification"},
                        {"name": "Email Notification"},
                        {"name": "SMS"}
                    ]
                },
                {
                    "name": "Product Search",
                    "sub_features": [
                        {"name": "Full Text Search"},
                        {"name": "Autocomplete"},
                        {"name": "Filters"}
                    ]
                },
                {
                    "name": "Chat",
                    "sub_features": [
                        {"name": "Real Time Messaging"},
                        {"name": "File Sharing"}
                    ]
                },
                {
                    "name": "KYC",
                    "sub_features": [
                        {"name": "Document Verification"},
                        {"name": "Identity Check"}
                    ]
                },
                {
                    "name": "CMS",
                    "sub_features": [
                        {"name": "Blog"},
                        {"name": "Content Management"}
                    ]
                }
            ]
        }
        
        result = await agent.execute(input_data)
        
        import json
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_agent())