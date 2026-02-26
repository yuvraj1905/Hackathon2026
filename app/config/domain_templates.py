from typing import Dict, List


DOMAIN_TEMPLATES: Dict[str, List[str]] = {
    "ecommerce": [
        "User Authentication & Authorization (OAuth2, JWT, role-based access)",
        "Product Catalog Management (CRUD, categories, variants, inventory)",
        "Shopping Cart & Session Management",
        "Order Management System (order processing, status tracking, history)",
        "Payment Gateway Integration (Stripe/PayPal, webhooks, refunds)",
        "Admin Dashboard (analytics, user management, product management)",
        "Search & Filtering (product search, faceted filters, sorting)",
        "Customer Profile Management (addresses, preferences, order history)",
        "Email Notifications (order confirmations, shipping updates)",
        "Review & Rating System",
    ],
    
    "saas": [
        "User Authentication & Authorization (SSO, MFA, RBAC)",
        "Multi-tenant Architecture (tenant isolation, data segregation)",
        "Subscription & Billing Management (plans, invoicing, payment processing)",
        "Admin Dashboard (tenant management, analytics, system monitoring)",
        "User Management (invitations, roles, permissions, teams)",
        "API Gateway & Rate Limiting",
        "Audit Logging & Activity Tracking",
        "Email & Notification System",
        "Onboarding Flow & User Setup",
        "Settings & Configuration Management",
    ],
    
    "marketplace": [
        "User Authentication & Authorization (buyers, sellers, admin roles)",
        "Vendor/Seller Onboarding & Management",
        "Product Listing Management (multi-vendor catalog, approval workflow)",
        "Search & Discovery (advanced filters, recommendations)",
        "Order Management (split orders, vendor routing, fulfillment)",
        "Payment Processing (split payments, escrow, commission handling)",
        "Review & Rating System (buyers and sellers)",
        "Admin Dashboard (vendor approval, dispute resolution, analytics)",
        "Messaging System (buyer-seller communication)",
        "Commission & Payout Management",
    ],
    
    "healthcare": [
        "User Authentication & Authorization (patient, provider, admin roles)",
        "Patient Management System (demographics, medical history, records)",
        "Appointment Scheduling & Calendar Management",
        "Electronic Health Records (EHR) Management",
        "Provider/Doctor Management (profiles, availability, specializations)",
        "Prescription Management System",
        "Billing & Insurance Processing",
        "Admin Dashboard (analytics, compliance reporting, user management)",
        "HIPAA Compliance Features (encryption, audit logs, access controls)",
        "Notification System (appointment reminders, alerts)",
        "Telemedicine Integration (video consultations, chat)",
    ],
    
    "fintech": [
        "User Authentication & Authorization (KYC, MFA, biometric)",
        "Account Management (user accounts, profiles, verification)",
        "Transaction Processing Engine (real-time, idempotent)",
        "Payment Gateway Integration (multiple providers, fallback)",
        "Wallet & Balance Management",
        "Transaction History & Reporting",
        "Admin Dashboard (fraud monitoring, compliance, analytics)",
        "Compliance & Regulatory Features (AML, KYC, audit trails)",
        "Security Features (encryption, tokenization, fraud detection)",
        "Notification System (transaction alerts, security notifications)",
        "Reconciliation & Settlement System",
    ],
}
