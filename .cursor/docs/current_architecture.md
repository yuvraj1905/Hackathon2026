# Presales Estimation Engine - Current Architecture

> **GeekyAnts Presales Estimation Tool**  
> Takes a project description (manual text OR uploaded PRD documents) and generates a complete estimation with hours breakdown, tech stack recommendations, and a client-ready proposal.

---

## Table of Contents

1. [High-Level Flow](#high-level-flow)
2. [Input Processing (Document Parsing)](#input-processing)
3. [Component Classification (LLM vs Static)](#component-classification)
4. [Detailed Component Breakdown](#detailed-component-breakdown)
5. [API Endpoints](#api-endpoints)
6. [Data Flow Summary](#data-flow-summary)
7. [Static Data Sources](#static-data-sources)
8. [Key Design Decisions](#key-design-decisions)
9. [Dependencies](#dependencies)

---

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PROJECT PIPELINE v2.0                               │
│                                                                                 │
│  Input: Manual Description AND/OR Uploaded PRD (PDF/DOCX/Excel)                 │
│         + build_options + timeline_constraint + additional_context              │
│          ↓                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐                                   │
│  │ 0. DOCUMENT     │────►│ 0b. INPUT       │                                   │
│  │    PARSER       │     │     FUSION      │                                   │
│  │    (Static)     │     │     (Static)    │                                   │
│  └─────────────────┘     └─────────────────┘                                   │
│          ↓                      ↓                                               │
│          └──────────────────────┘                                               │
│                    ↓                                                            │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │ 1. DOMAIN       │────►│ 1b. DOMAIN      │────►│ 2. SMART        │           │
│  │    DETECTION    │     │     ALIAS       │     │    TEMPLATE     │           │
│  │    (LLM+Context)│     │    RESOLVER     │     │    EXPANDER     │           │
│  └─────────────────┘     └─────────────────┘     │    (LLM)        │           │
│                                                  └─────────────────┘           │
│                                                         │                       │
│                                          ┌──────────────┴──────────────┐       │
│                                          ↓                              ↓       │
│                               ┌─────────────────┐           ┌─────────────────┐│
│                               │ 2a. MODULE      │           │ 2b. FALLBACK    ││
│                               │     SELECTOR    │           │     GENERATOR   ││
│                               │     (LLM)       │           │     (LLM)       ││
│                               └─────────────────┘           └─────────────────┘│
│                                          ↓                              ↓       │
│                                          └──────────────┬───────────────┘       │
│                                                         ↓                       │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │ 3. FEATURE      │◄────│ (Enriched       │     │                 │           │
│  │    STRUCTURING  │     │  Description)   │     │                 │           │
│  │    (LLM)        │     │                 │     │                 │           │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘           │
│          ↓                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │ 4. ESTIMATION   │◄────│ CALIBRATION     │     │ 5. TECH STACK   │           │
│  │    (Static+Cal) │     │ ENGINE (Static) │     │    (Static/LLM) │           │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘           │
│          ↓                                              ↓                       │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │ 6. CONFIDENCE   │────►│ 7. PROPOSAL     │────►│ 8. PLANNING     │           │
│  │    ENGINE       │     │    GENERATION   │     │    ENGINE       │           │
│  │    (Static)     │     │    (LLM)        │     │    (Static)     │           │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘           │
│                                                         ↓                       │
│                                              Final Response                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Input Processing

The system supports **three input modes**:

| Mode          | Description                                                |
| ------------- | ---------------------------------------------------------- |
| `manual_only` | User provides text description directly                    |
| `file_only`   | User uploads PRD document (PDF/DOCX/Excel)                 |
| `hybrid`      | User provides both manual description AND uploads document |

### Document Parser

**File:** `app/services/document_parser.py`  
**Type:** Static/Deterministic + Optional LLM Cleanup

Extracts text from uploaded business documents (PRDs, specifications, etc.)

**Supported Formats:**

- `.pdf` - PDF documents (using `pdfplumber` with table extraction)
- `.docx` - Word documents (using `python-docx` with tables and headers/footers)
- `.xlsx` / `.xls` - Excel spreadsheets (using `pandas` + `openpyxl`/`xlrd`)

**Constraints:**

```python
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_OUTPUT_CHARS = 12000
PARSE_TIMEOUT_SECONDS = 30
```

**Features:**

- **PDF:** Layout-aware extraction with table support (pdfplumber)
- **DOCX:** Extracts paragraphs, tables, headers, and footers
- **Tables:** Formatted as markdown-style pipe-separated rows
- **LLM Cleanup:** Optional post-processing to fix OCR errors and normalize formatting

**Text Cleaning:**

- Removes null characters
- Collapses multiple spaces/tabs
- Limits consecutive newlines to 2
- Adds truncation marker when content exceeds limit

### Input Fusion Service

**File:** `app/services/input_fusion_service.py`  
**Type:** Static/Deterministic

Combines manual description with extracted document text into a single normalized input.

**Fusion Rules:**

```python
MAX_INPUT_CHARS = 20000

# Both present: manual + document context
if has_manual and has_extracted:
    final = f"{manual}\n\nAdditional context from client documents:\n{extracted}"

# Only manual: use as-is
elif has_manual:
    final = manual

# Only extracted: use as-is
elif has_extracted:
    final = extracted

# Neither: ValueError
else:
    raise ValueError("Either manual_description or extracted_text is required")
```

---

## Component Classification

### LLM-Powered Components (6)

| Component                     | File                                    | Model       | Purpose                                              |
| ----------------------------- | --------------------------------------- | ----------- | ---------------------------------------------------- |
| Domain Detection Agent        | `agents/domain_detection_agent.py`      | GPT-4o-mini | Classify project into domains with full context      |
| **Smart Template Expander**   | `services/template_expander.py`         | GPT-4o-mini | Intelligently select relevant modules from templates |
| **Fallback Module Generator** | `services/fallback_module_generator.py` | GPT-4o-mini | Generate modules for unknown/unmapped domains        |
| Feature Structuring Agent     | `agents/feature_structuring_agent.py`   | GPT-4o-mini | Extract and normalize features                       |
| Proposal Agent                | `agents/proposal_agent.py`              | GPT-4o-mini | Generate client-ready proposal                       |
| Modification Agent            | `agents/modification_agent.py`          | GPT-4o-mini | Modify scope based on instruction                    |

### Static/Deterministic Components (8)

| Component                 | File                               | Purpose                                    |
| ------------------------- | ---------------------------------- | ------------------------------------------ |
| **Document Parser**       | `services/document_parser.py`      | Extract text from PDF/DOCX/Excel PRDs      |
| **Input Fusion Service**  | `services/input_fusion_service.py` | Combine manual + extracted inputs          |
| **Database Manager**      | `services/database.py`             | PostgreSQL connection pool management      |
| **Domain Alias Resolver** | `config/domain_aliases.py`         | Map detected domains to template domains   |
| Estimation Agent          | `agents/estimation_agent.py`       | Apply base hours + calibration + buffer    |
| Calibration Engine        | `services/calibration_engine.py`   | Historical data lookup with fuzzy matching |
| Confidence Engine         | `services/confidence_engine.py`    | Formula-based confidence calculation       |
| Planning Engine           | `services/planning_engine.py`      | Fixed ratios for phases/team sizing        |

### Hybrid Components (1)

| Component        | File                         | Purpose                                                     |
| ---------------- | ---------------------------- | ----------------------------------------------------------- |
| Tech Stack Agent | `agents/tech_stack_agent.py` | Static mapping for known domains, LLM fallback for unknowns |

---

## Detailed Component Breakdown

### 0. Document Parser (UPGRADED)

**File:** `app/services/document_parser.py`  
**Type:** Static/Deterministic + Optional LLM Cleanup

**Purpose:** Extract clean text from uploaded PRD documents for feature extraction.

**Supported File Types:**

| Extension | Library               | Notes                                            |
| --------- | --------------------- | ------------------------------------------------ |
| `.pdf`    | `pdfplumber`          | Layout-aware extraction with table support       |
| `.docx`   | `python-docx`         | Extracts paragraphs, tables, headers, footers    |
| `.xlsx`   | `pandas` + `openpyxl` | Converts all sheets to text with pipe separators |
| `.xls`    | `pandas` + `xlrd`     | Legacy Excel format support                      |

**PDF Extraction (with tables):**

```python
def _extract_pdf_text(content: bytes) -> str:
    with pdfplumber.open(BytesIO(content)) as pdf:
        for page in pdf.pages:
            # Extract tables first
            tables = page.extract_tables()
            for table in tables:
                table_text = _format_table_as_text(table)
            # Extract text with layout awareness
            page_text = page.extract_text(layout=True)
```

**DOCX Extraction (with tables and headers):**

```python
def _extract_docx_text(content: bytes) -> str:
    doc = Document(BytesIO(content))
    # Extract headers
    for section in doc.sections:
        header_text = _extract_docx_header_footer(section.header)
    # Extract paragraphs and tables in document order
    for element in doc.element.body:
        # Handle paragraphs and tables
    # Extract footers
```

### 0a. Document Cleaner (NEW)

**File:** `app/services/document_cleaner.py`  
**Type:** LLM-Powered (GPT-4o-mini)

**Purpose:** Clean and structure extracted document text using LLM.

**Features:**

- Fix OCR/layout errors (garbled text, split words)
- Normalize formatting (headings, bullets, numbered lists)
- Preserve all original content
- Auto-triggered based on extraction quality heuristics

**Quality Check Heuristics:**

- Short extraction from large file (< 500 chars from > 100KB)
- High special character ratio (> 30%)

---

### 0b. Input Fusion Service (NEW)

**File:** `app/services/input_fusion_service.py`  
**Type:** Static/Deterministic

**Purpose:** Combine manual description with extracted document text into a unified input for the pipeline.

**Input Modes:**

| Mode          | Manual | File | Result                                                           |
| ------------- | ------ | ---- | ---------------------------------------------------------------- |
| `hybrid`      | ✓      | ✓    | Manual + "Additional context from client documents:" + Extracted |
| `manual_only` | ✓      | ✗    | Manual only                                                      |
| `file_only`   | ✗      | ✓    | Extracted only                                                   |

**Truncation:** Final description is truncated to `MAX_INPUT_CHARS = 20000` characters.

---

### 0c. Database Manager (NEW)

**File:** `app/services/database.py`  
**Type:** Static/Deterministic

**Purpose:** PostgreSQL connection pool management using `asyncpg`.

**Configuration:**

```python
pool = await asyncpg.create_pool(
    dsn=database_url,
    min_size=1,
    max_size=5,
    command_timeout=30,
)
```

**Features:**

- Async connection pooling
- Health check endpoint
- Automatic cleanup of unsupported query params (e.g., `channel_binding`)

---

### 1. Domain Detection Agent (UPGRADED)

**File:** `app/agents/domain_detection_agent.py`  
**Type:** LLM-powered (GPT-4o-mini via OpenRouter)

**Input:** Project description + additional_details + extracted_text + build_options + timeline_constraint + additional_context  
**Output:** Domain classification + confidence score + reasoning

**Context-Aware Classification:**
The upgraded agent receives full project context for better classification:

- `description` - Fused description from manual input + extracted document text
- `additional_details` - Raw manual requirement text (verbatim)
- `extracted_text` - Raw parsed document text (verbatim)
- `build_options` - Platforms to build (mobile, web, admin, backend, design)
- `timeline_constraint` - Project timeline (passed to later stages)
- `additional_context` - Any extra context from user

**Available Domains (24):**

| Category              | Domains                                                                                                                                  |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Industry-Specific** | `ecommerce`, `fintech`, `healthcare`, `education`, `marketplace`, `logistics`, `insurance`, `enterprise`                                 |
| **Platform-Type**     | `saas`, `iot`, `social_media`                                                                                                            |
| **Generic**           | `mobile_app`, `web_app`, `ai_ml`, `blockchain`, `unknown`                                                                                |
| **Domain Templates**  | `edtech`, `crm`, `hrms`, `real_estate`, `project_management`, `social_media_platform`, `food_delivery`, `travel_booking`, `iot_platform` |

**Classification Rules:**

1. Always prefer specific industry domain over generic
2. Multi-vendor/seller → `marketplace` (not `ecommerce`)
3. Consider what the END USER does, not just the technology
4. Use keywords: "patients" → `healthcare`, "courses/students" → `education`

**Confidence Normalization:**

```python
# Raw LLM confidence (0-1) is scaled to realistic range (0.65-0.95)
normalized = 0.65 + (raw_confidence * 0.30)
```

---

### 1b. Domain Alias Resolver (NEW)

**File:** `app/config/domain_aliases.py`  
**Type:** Static/Deterministic

**Purpose:** Maps detected domain names to template domain names, handling mismatches between what the Domain Detection Agent outputs and what exists in `DOMAIN_TEMPLATES`.

**Alias Mappings:**

```python
DOMAIN_ALIASES = {
    "education": "edtech",
    "social_media": "social_media_platform",
    "iot": "iot_platform",
    "enterprise": "saas",
    "mobile_app": "mobile_app",  # Has own template
    "web_app": "web_app",        # Has own template
    "ai_ml": "ai_ml",            # Has own template
    "blockchain": "blockchain",  # Has own template
}
```

**Functions:**

- `resolve_domain_alias(detected_domain)` - Returns template domain name
- `should_use_fallback(detected_domain)` - Returns True if LLM fallback needed

---

### 2. Smart Template Expander (UPGRADED)

**File:** `app/services/template_expander.py`  
**Type:** LLM-powered with static fallback

**Input:** Detected domain + description + build_options + additional_context  
**Output:** Tuple of (enriched_description, selected_modules)

**How it works:**

1. **Domain Resolution:** Uses `resolve_domain_alias()` to map detected domain to template domain
2. **Template Lookup:** Gets all modules from `DOMAIN_TEMPLATES` for the resolved domain
3. **LLM Module Selection:** Uses LLM to intelligently select relevant modules based on:
   - Project description
   - Build options (mobile/web/admin/backend/design)
   - Additional context
4. **Fallback Generation:** If no template exists, uses `Fallback Module Generator` to create modules from scratch
5. **Enriched Description:** Builds description with selected modules appended

**Module Selection Criteria:**

- **Explicitly Required** - Directly mentioned or implied in description
- **Core Dependencies** - Required for other features (e.g., Auth for user features)
- **Industry Standard** - Expected in any product of that domain
- **Platform Requirements** - Needed based on build_options

**Exclusion Criteria:**

- Clearly out of scope based on description
- Advanced features not mentioned for basic projects
- Platform-specific features for platforms not being built

**Key Improvement:** No longer dumps all modules blindly. Selects only essential modules based on actual business needs.

---

### 2a. Fallback Module Generator (NEW)

**File:** `app/services/fallback_module_generator.py`  
**Type:** LLM-powered (GPT-4o-mini)

**Purpose:** Generates domain-specific modules from scratch when no template exists (e.g., for `unknown` domain or novel project types).

**Input:** Domain + description + build_options  
**Output:** List of generated module strings with sub-features

**Generation Approach (Solutions Architect Mindset):**

1. **Core Business Logic** - Primary features that make the product work
2. **User Management** - Authentication, roles, permissions
3. **Data & Content** - Storage, management, search, display
4. **Transactions & Workflows** - Payments, bookings, multi-step processes
5. **Communication** - Notifications, messaging, emails
6. **Administration** - Admin/operator management tools
7. **Integrations** - Third-party services (payments, maps, analytics)
8. **Security & Compliance** - Industry-specific requirements
9. **Platform-Specific** - Mobile/web/admin specific features

**Fallback (if LLM unavailable):** Returns basic 8 modules covering Auth, Admin, Database, API, Search, Notifications, Settings, Logging.

---

### Static Templates (Domain Templates)

**File:** `app/config/domain_templates.py`

| Domain        | # Modules | Key Modules                                                                                                                                            |
| ------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ecommerce`   | 12        | Auth, Product Catalog, Cart, Orders, Payments, Admin, Search, Profile, Email, Reviews, Coupons, Shipping                                               |
| `saas`        | 12        | Auth (SSO/MFA/RBAC), Multi-tenant, Subscriptions, Admin, Users, API Gateway, Audit, Email, Onboarding, Settings, Analytics, Workspace                  |
| `marketplace` | 12        | Multi-role Auth, Vendor Onboarding, Listings, Search, Orders, Split Payments, Reviews, Admin, Messaging, Commission, Disputes, Vendor Analytics        |
| `healthcare`  | 12        | Auth, Patient Management, Appointments, EHR, Provider Management, Prescriptions, Billing, Admin, HIPAA, Notifications, Telemedicine, Care Coordination |
| `fintech`     | 12        | Auth (KYC), Accounts, Transactions, Payments, Wallet, History, Admin, Compliance, Security, Notifications, Reconciliation, Disputes                    |
| `mobile_app`  | 10        | Auth, Push Notifications, Offline Sync, Navigation, Device Features, State Management, IAP, Analytics, Settings, Version Management                    |
| `web_app`     | 10        | Auth, Responsive Design, Admin Dashboard, API Integration, Search, Data Visualization, Notifications, Settings, File Management, SEO                   |
| `ai_ml`       | 10        | Auth/API Keys, Data Pipeline, Training Interface, Model Registry, Deployment, Inference API, Monitoring, Dashboard, Dataset Management, Cost Tracking  |
| `blockchain`  | 10        | Wallet Integration, Smart Contracts, Auth, Transactions, Token Management, NFT Marketplace, DeFi, Admin, Explorer Integration, Security                |
| `unknown`     | 8         | Auth, Admin Dashboard, Database, API Layer, Search, Notifications, Settings, Logging                                                                   |

---

### 3. Feature Structuring Agent (UPGRADED)

**File:** `app/agents/feature_structuring_agent.py`  
**Type:** LLM-powered

**Input:** Raw context (additional_details, extracted_text, selected_modules, build_options, domain)  
**Output:** Structured feature list

**Feature Structure:**

```json
{
  "name": "User Authentication",
  "complexity": "Medium"
}
```

**Note:** Category field has been removed. Features are now grouped by complexity level only.

**Complexity Levels:** Low, Medium, High

**Complexity Assessment Guidelines:**

- **Low:** Standard CRUD, basic forms, static pages, simple auth
- **Medium:** Business logic with conditions, third-party APIs, real-time features, role-based access, dashboards with charts
- **High:** Compliance (HIPAA, PCI-DSS), GPS/tracking, AI/ML, complex algorithms, multi-tenant architecture, offline-first sync

**Domain-Specific Considerations:**

- Healthcare: Patient data handling is HIGH (HIPAA compliance)
- Fintech: Payment/transaction features are HIGH (PCI, fraud prevention)
- Marketplace: Multi-party transactions add complexity
- Real-time apps: Location/tracking features are HIGH

---

### 4. Estimation Agent

**File:** `app/agents/estimation_agent.py`  
**Type:** Static/Deterministic (NO LLM calls)

**Input:** Feature list  
**Output:** Hours per feature + totals

**Static Base Hours by Complexity:**

```python
COMPLEXITY_BASE_HOURS = {
    "low": 28,
    "medium": 72,
    "high": 140
}

COMPLEXITY_FLOOR_HOURS = {
    "low": 16,
    "medium": 32,
    "high": 64
}

BUFFER_MULTIPLIER = 1.15  # 15% buffer for unforeseen complexity
```

**Estimation Formula:**

```
final_hours = calibrated_hours × BUFFER_MULTIPLIER × mvp_factor
```

**MVP Detection:**
If description contains keywords like "basic", "simple", "mvp", "minimal", "boutique", "small business", a scope reduction factor (0.75-0.85) is applied.

```python
MVP_SIGNALS = [
    "basic", "simple", "small", "mvp", "minimal",
    "flower", "flowers", "boutique", "shop", "local",
    "small business", "startup", "beginner"
]
```

**Range Calculation:**

```python
min_hours = total_hours * 0.85
max_hours = total_hours * 1.15
```

---

### 5. Calibration Engine

**File:** `app/services/calibration_engine.py`  
**Type:** Static/Deterministic

**Data Source:** Excel files in `app/data/calibration/`

**How it works:**

1. On startup, `CSVCalibrationLoader` reads all Excel files
2. Extracts feature names and actual hours from historical projects
3. Aggregates into average hours per normalized feature name
4. During estimation, fuzzy-matches features to historical data

**Matching Strategy (Priority Order):**

1. **Exact match:** Normalized feature name matches exactly
2. **Contains match:** One name contains the other as substring
3. **Token overlap >= 60%:** Jaccard similarity of words

**Calibration Requirement:**
Only applies calibration if `sample_size >= 2` (at least 2 historical data points)

**Stopwords Removed During Matching:**

```python
STOPWORDS = ["user", "management", "system", "module", "service",
             "and", "&", "the", "a", "an", "for", "with"]
```

---

### 6. CSV Calibration Loader

**File:** `app/services/csv_calibration_loader.py`  
**Type:** Static/Deterministic

**Purpose:** Load historical project data from Excel files for calibration

**Excel Parsing Strategy:**

1. Primary: `openpyxl` engine
2. Fallback: `calamine` engine (for files with corrupt/invalid stylesheet XML)
3. Legacy: `xlrd` engine (for older .xls files)

**Column Detection:**

```python
FEATURE_COLUMN_CANDIDATES = ["name", "module name", "feature", "module"]
TOTAL_HOURS_CANDIDATES = ["total hours", "total", "hours"]
COMPONENT_HOUR_COLUMNS = ["web mobile", "backend", "wireframe", "visual design"]
```

**Skip Row Keywords:**

```python
SKIP_ROW_KEYWORDS = ["total", "subtotal", "summary", "grand total",
                    "sub-total", "sub total", "grand-total"]
```

**Current Calibration Files (14):**

- Al-Yousuf (Service Providers).xlsx
- Chanced Web App (2).xlsx
- Hobbes Health Reference.xlsx
- Kaizen Tender - Coimisiún na Meán.xlsx
- Nutralis App_Dev Estimations.xlsx
- Pink Umbrella \_ Phase-1 - Website.xlsx
- Rajshree Mobile- P1 (Revised - 27.11.24).xlsx
- Taout (1).xlsx
- Tiffynai - Development.xlsx
- Two Cents Corporation.xlsx
- Unreserved (2) (1).xlsx
- xcd Tech - Must Have - Development (1).xlsx

---

### 7. Tech Stack Agent

**File:** `app/agents/tech_stack_agent.py`  
**Type:** Hybrid (Static with LLM fallback)

**Input:** Domain + features  
**Output:** Frontend, Backend, Database, Infrastructure, Third-party services

**Static Mapping for Known Domains:**

| Domain        | Frontend                       | Backend                          | Database                   | Third-party                  |
| ------------- | ------------------------------ | -------------------------------- | -------------------------- | ---------------------------- |
| `ecommerce`   | React, Next.js, Tailwind       | Node.js, Express/NestJS, FastAPI | PostgreSQL, Redis          | Stripe, SendGrid, Cloudinary |
| `saas`        | React, TypeScript, Tailwind    | Node.js/NestJS, FastAPI          | PostgreSQL, Redis          | Stripe, Auth0, Segment       |
| `marketplace` | React, Next.js, Tailwind       | Node.js, FastAPI                 | PostgreSQL, MongoDB, Redis | Stripe Connect, Twilio       |
| `healthcare`  | React, TypeScript, Material-UI | FastAPI, Node.js                 | PostgreSQL, Redis          | Twilio Video, AWS KMS        |
| `fintech`     | React, TypeScript, Material-UI | FastAPI, Node.js                 | PostgreSQL, Redis          | Plaid, Stripe, AWS KMS       |

**Fallback:** For unknown domains, calls LLM to generate custom stack recommendation.

---

### 8. Confidence Engine

**File:** `app/services/confidence_engine.py`  
**Type:** 100% Static/Deterministic

**Formula:**

```python
confidence = (coverage_score * 0.6 + strength_score * 0.4) * 100
```

**Coverage Score:**

```python
coverage_score = calibrated_features / total_features
```

**Strength Score:**

```python
strength_score = features_with_sample_size_gte_3 / total_features
```

**Cap:** Never exceeds 95% (never claims 100% confidence)

---

### 9. Proposal Agent

**File:** `app/agents/proposal_agent.py`  
**Type:** LLM-powered

**Input:** Domain, features, total hours, tech stack  
**Output:** Client-ready proposal

**Generated Sections:**

- Executive summary (2-3 sentences)
- Scope of work (3-4 sentences)
- Deliverables (5-7 items)
- Timeline in weeks
- Team composition
- Risks (3-4 items)
- Mitigation strategies (3-4 items)

**LLM Settings:**

- Temperature: 0.3 (slightly creative for natural text)
- Max tokens: 1000

---

### 10. Planning Engine (UPGRADED)

**File:** `app/services/planning_engine.py`  
**Type:** 100% Static/Deterministic

**Input:** Total hours, timeline, features  
**Output:** Phase breakdown, team recommendation, complexity totals

**Static Phase Ratios:**

```python
PHASE_RATIOS = {
    "frontend": 0.40,  # 40% of hours
    "backend": 0.35,   # 35%
    "qa": 0.15,        # 15%
    "pm_ba": 0.10      # 10%
}
```

**Complexity Breakdown:**
Hours are now aggregated by complexity level (High, Medium, Low) instead of category:

```python
complexity_totals = {
    "High": 280.0,    # Hours for high complexity features
    "Medium": 144.5,  # Hours for medium complexity features
    "Low": 56.0       # Hours for low complexity features
}
```

**Team Calculation:**

```python
HOURS_PER_WEEK = 40

total_engineers = ceil(total_hours / (timeline_weeks * 40))
total_engineers = max(2, total_engineers)  # Minimum 2

frontend_devs = max(1, ceil(total_engineers * 0.5))
backend_devs = max(1, ceil(total_engineers * 0.5))
qa_engineers = max(1, total_engineers // 3)
pm_count = 1
```

---

### 11. Modification Agent

**File:** `app/agents/modification_agent.py`  
**Type:** LLM-powered

**Input:** Current feature list + modification instruction  
**Output:** Updated feature list

**Operations:**

- **ADD:** Add new features (e.g., "Add analytics dashboard")
- **REMOVE:** Remove features (e.g., "Remove social login")
- **MODIFY:** Change complexity/description (e.g., "Make admin dashboard more complex")

**Behavior:**

- Preserves existing features unless explicitly asked to remove/modify
- Uses same category and complexity standards as original features

---

## API Endpoints

**File:** `app/main.py`

| Endpoint      | Method | Content-Type          | Description                                      |
| ------------- | ------ | --------------------- | ------------------------------------------------ |
| `/health`     | GET    | -                     | Health check (pipeline + database status)        |
| `/auth/login` | POST   | `application/json`    | Authenticate user, return JWT token              |
| `/estimate`   | POST   | `application/json`    | Estimation from manual input (JWT required)      |
| `/estimate`   | POST   | `multipart/form-data` | Estimation with optional PRD file (JWT required) |
| `/modify`     | POST   | `application/json`    | Modify features and re-estimate                  |

### `/auth/login` Endpoint (NEW)

**Request:**

```json
{
  "email": "admin@geekyants.com",
  "password": "Test@123"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "admin@geekyants.com",
    "created_at": "2026-02-27T..."
  }
}
```

### `/estimate` Endpoint

**Requires JWT authentication** (Authorization: Bearer &lt;token&gt;).

Supports **two content types** and **four input modes** (manual-only, file-only, hybrid, re-estimation):

**JSON (application/json):**

```json
{
  "additional_details": "Build an e-commerce platform...",
  "build_options": ["mobile", "web", "admin"],
  "additional_context": "Focus on mobile users",
  "preferred_tech_stack": ["React", "Node.js"],
  "timeline_constraint": "3 months",
  "project_id": "uuid-of-existing-project"
}
```

- At least one of `additional_details` (min 10 chars) or a file is required; for JSON-only, `additional_details` is required.
- `project_id` is optional - if provided, fetches stored data from that project as defaults.

**Multipart (multipart/form-data):**

```
file: <PRD.pdf | PRD.docx | PRD.xlsx>   (optional)
additional_details: "Optional manual description"
build_options: JSON array string, e.g. "[\"mobile\",\"web\"]"
timeline_constraint: "3 months"
additional_context: "Optional context"
preferred_tech_stack: "React, Node.js"
project_id: "uuid-of-existing-project" (optional)
```

**Input modes:**

- Both `additional_details` (min 10 chars) and `file` → `hybrid`
- Only `file` → `file_only`
- Only `additional_details` → `manual_only`
- `project_id` provided → `re-estimation` (uses stored data as defaults)

**Re-estimation with project_id:**
When `project_id` is provided:

1. Fetches stored `additional_details`, `build_options`, `timeline_constraint` from `projects` table
2. Fetches stored `extracted_text` from `documents` table (if document exists)
3. Uses stored values as defaults - new inputs override stored values
4. Runs full pipeline with combined context

**Behaviour:**

- Parses file (PDF/DOCX/XLSX/XLS) with document parser; applies LLM cleanup when extraction quality is poor.
- Fuses manual + extracted text via Input Fusion, runs full pipeline, returns `FinalPipelineResponse`.
- Passes `build_options` and `timeline_constraint` through the pipeline for context-aware processing.
- After success, inserts a row into `projects` (user_id, additional_details, build_options, timeline_constraint) and, if a file was uploaded, a row into `documents` (user_id, project_id, filename, file_type, extracted_text).

**Response structure (`FinalPipelineResponse`):**

- `request_id` (str), `domain_detection` (detected_domain, confidence, secondary_domains, reasoning), `estimation` (total_hours, min_hours, max_hours, features, overall_complexity, confidence_score, assumptions), `tech_stack` (frontend, backend, database, infrastructure, third_party_services, justification as nested dicts or lists), `proposal` (executive_summary, scope_of_work, deliverables, timeline_weeks, team_composition, risks, mitigation_strategies), `planning` (phase_split, team_recommendation, complexity_breakdown), `metadata`.
- Each feature in `estimation.features` has: `name`, `complexity`, `total_hours`, `subfeatures` (list of `{ name, effort }`), `confidence_score`.

**Download Proposal & Proposal Generation:**

- `/proposal/pdf/{request_id}`, `/proposal/html/{request_id}`, and `/proposal/google-doc/{request_id}` use the cached estimation result for that `request_id` (same structure as above). Context for the proposal template is built via `_build_proposal_context()`: features are normalized (description from subfeature names, total_hours for hours), and tech_stack layers are flattened to lists for display in the HTML template.

### `/health` Endpoint

**Response:**

```json
{
  "status": "healthy",
  "pipeline_initialized": true,
  "database_connected": true
}
```

**Status Values:**

- `healthy` - All systems operational
- `degraded` - Database connection failed

### `/modify` Endpoint

**Request:**

```json
{
  "current_features": [{ "name": "User Auth", "complexity": "Medium" }],
  "instruction": "Add analytics dashboard"
}
```

---

## Data Flow Summary

1. **User submits** additional details (manual text) + build_options (mobile, web, design, backend, admin) + timeline_constraint + optional PRD document + optional project_id
2. **Project Reuse** (if project_id provided) → fetches stored additional_details, build_options, timeline_constraint, extracted_text from database as defaults
3. **Document Parser** (Static) → extracts text from PDF/DOCX/Excel if file uploaded
4. **Input Fusion** (Static) → combines manual + extracted text into unified description
5. **Domain Detection** (LLM + Context) → identifies domain using description + additional_details + extracted_text + build_options + additional_context
6. **Domain Alias Resolver** (Static) → maps detected domain to template domain name
7. **Smart Template Expander** (LLM) → intelligently selects relevant modules from template based on:
   - Project description
   - Build options (mobile/web/admin)
   - Additional context
   - OR generates modules from scratch via Fallback Generator for unknown domains
8. **Feature Structuring** (LLM) → extracts features with complexity levels from raw context (selected_modules, build_options, domain, additional_details, extracted_text)
9. **Estimation** (Static) → applies base hours + calibration + buffer
10. **Confidence** (Static) → calculates 0-95% based on calibration coverage
11. **Tech Stack** (Static/LLM) → recommends stack based on domain
12. **Proposal** (LLM) → generates executive summary, deliverables, risks (receives timeline_constraint for context)
13. **Planning** (Static) → splits hours by phase, recommends team size
14. **Response** → complete estimation package with metadata (build_options, timeline_constraint, modules_selected) returned to user; request data stored in `projects` and `documents` tables

---

## Database Schema

### Users Table

Stores admin users for authentication (seeded, no signup).

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Projects Table

Stores one row per estimation request (created after each successful `/estimate` call).

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    additional_details TEXT,
    build_options TEXT[],  -- 'mobile', 'web', 'design', 'backend', 'admin'
    timeline_constraint TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Points:**

- One project row per estimate; holds user input (additional_details, build_options, timeline_constraint).
- `build_options`: User's selections as Postgres text array.

### Documents Table

Stores uploaded PRD files and extracted text; each row is linked to a project (created when `/estimate` is called with a file).

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_type VARCHAR(10),  -- 'pdf', 'docx', 'xlsx', 'xls'
    extracted_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Points:**

- `project_id`: Links to the project row created for that estimate.
- `extracted_text`: LLM-cleaned (or raw) text from the document parser.

---

## Static Data Sources

### 1. Domain Templates (`config/domain_templates.py`)

Static dictionary mapping domains to required modules:

```python
DOMAIN_TEMPLATES = {
    "ecommerce": [...],  # 10 modules
    "saas": [...],       # 10 modules
    "marketplace": [...], # 10 modules
    "healthcare": [...],  # 11 modules
    "fintech": [...],     # 11 modules
}
```

### 2. Tech Stack Mappings (`agents/tech_stack_agent.py`)

Static dictionary mapping domains to recommended tech stacks:

```python
DOMAIN_STACK_MAPPING = {
    "ecommerce": {"frontend": [...], "backend": [...], ...},
    "saas": {...},
    "marketplace": {...},
    "healthcare": {...},
    "fintech": {...}
}
```

### 3. Calibration Data (`data/calibration/*.xlsx`)

14 Excel files containing historical project estimations used for calibration.

---

## Key Design Decisions

1. **Hybrid Approach:** LLM for interpretation/generation, static for calculations
2. **PRD Document Support:** Accept PDF, DOCX, Excel uploads containing project requirements
3. **Input Fusion:** Combine manual description with extracted document text for richer context
4. **Calibration from Real Data:** 14 historical Excel files improve accuracy
5. **Fuzzy Matching:** Handles variations in feature naming across projects
6. **Conservative Confidence:** Never exceeds 95%, requires sample_size >= 2
7. **Buffer Built-in:** 15% buffer automatically added to all estimates
8. **MVP Detection:** Reduces scope for small/simple projects (0.75-0.85x)
9. **Fallback Engines:** Multiple Excel/PDF parsing engines for robustness
10. **Database Integration:** PostgreSQL with async connection pooling

---

## Dependencies

**File:** `requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
pydantic-settings==2.6.0
httpx==0.27.2
python-dotenv==1.0.1
pandas==2.2.3
openpyxl==3.1.5
asyncpg==0.30.0
pdfplumber==0.11.4
python-docx==1.1.0
xlrd==2.0.1
python-calamine>=0.2.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```

**Key Libraries:**

- **FastAPI:** Web framework with multipart/form-data support
- **httpx:** Async HTTP client for OpenRouter API calls
- **pdfplumber:** PDF text extraction with table support (replaces pypdf)
- **python-docx:** DOCX text extraction from PRD documents
- **pandas + openpyxl + calamine + xlrd:** Excel file parsing (calibration + PRDs)
- **asyncpg:** Async PostgreSQL driver
- **pydantic:** Data validation and serialization
- **passlib[bcrypt]:** Password hashing for authentication
- **python-jose:** JWT token creation and validation

---

## File Structure

```
app/
├── main.py                          # FastAPI entry point, endpoints (auth, estimate, modify)
├── agents/
│   ├── base_agent.py                # Base class with LLM call logic
│   ├── domain_detection_agent.py    # LLM: Domain classification (UPGRADED - context-aware)
│   ├── feature_structuring_agent.py # LLM: Feature extraction
│   ├── estimation_agent.py          # STATIC: Hours calculation
│   ├── tech_stack_agent.py          # HYBRID: Tech recommendations
│   ├── proposal_agent.py            # LLM: Proposal generation
│   └── modification_agent.py        # LLM: Scope modification
├── services/
│   ├── document_parser.py           # STATIC+LLM: PDF/DOCX/Excel extraction (pdfplumber)
│   ├── document_cleaner.py          # LLM: Post-processing cleanup
│   ├── input_fusion_service.py      # STATIC: Combine manual + extracted text
│   ├── database.py                  # STATIC: PostgreSQL connection pool
│   ├── auth_service.py              # STATIC: JWT + password utilities
│   ├── template_expander.py         # LLM: Smart template expansion (UPGRADED)
│   ├── fallback_module_generator.py # LLM: Generate modules for unknown domains (NEW)
│   ├── calibration_engine.py        # STATIC: Historical data matching
│   ├── csv_calibration_loader.py    # STATIC: Excel file parsing for calibration
│   ├── confidence_engine.py         # STATIC: Confidence calculation
│   └── planning_engine.py           # STATIC: Phase/team planning
├── config/
│   ├── domain_templates.py          # Static domain module templates (EXPANDED)
│   └── domain_aliases.py            # Domain alias mappings (NEW)
├── models/
│   ├── project_models.py            # Pydantic models for estimation
│   ├── modification_models.py       # Pydantic models for modification
│   ├── user_models.py               # Pydantic models for auth
│   └── document_models.py           # Pydantic models for documents (project-linked)
├── orchestrator/
│   └── project_pipeline.py          # Main pipeline orchestrator (UPGRADED v2.0)
└── data/
    └── calibration/                 # Historical Excel files (14 files)
```

---

## Environment Variables

```bash
OPENROUTER_API_KEY=sk-...  # Required for LLM calls
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # Required for PostgreSQL
JWT_SECRET_KEY=your-secret-key  # Required for JWT token signing (change in production!)
```

---

_Last updated: February 28, 2026 - Smart Template Engine v2.0 + Feature Structuring v2.0 (complexity-based)_
