# Technical Specification

## ReviewIQ — E-Commerce Customer Review Agent

| Field | Details |
|-------|---------|
| **Author** | Vaibhav Lad |
| **Date** | May 2026 |
| **PRD Reference** | [PRD.md](PRD.md) |
| **Status** | Implemented |

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    Streamlit App                      │
│                                                      │
│  ┌─────────┐   ┌──────────┐   ┌───────────────┐     │
│  │Dashboard │   │ Reviews  │   │ Email Queue   │     │
│  │  Page    │   │  Page    │   │    Page       │     │
│  └────┬─────┘   └────┬─────┘   └──────┬────────┘     │
│       │              │                │              │
│       └──────────┬───┘────────────────┘              │
│                  │                                    │
│          ┌───────▼────────┐                           │
│          │  SQLAlchemy    │                           │
│          │  ORM Layer     │                           │
│          └───────┬────────┘                           │
│                  │                                    │
│          ┌───────▼────────┐    ┌─────────────────┐   │
│          │   SQLite DB    │    │  OpenAI API      │   │
│          │ (reviewiq.db)  │    │  (OpenAI SDK)    │   │
│          └────────────────┘    └─────────────────┘   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Design Principle:** Single-process, file-based architecture. No microservices, no message queues, no external databases. Everything runs in one Python process with a SQLite file for persistence.

---

## 2. Tech Stack

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| UI Framework | Streamlit | >= 1.38 | Rapid prototyping, built-in components for data apps |
| Database | SQLite | Built-in | Zero setup, file-based, sufficient for demo scale |
| ORM | SQLAlchemy | >= 2.0 | Type-safe queries, relationship management, DB-agnostic |
| AI Model | GPT-4o | gpt-4o | Best balance of quality and cost for classification + generation |
| AI SDK | OpenAI Python SDK | >= 1.0 | Official SDK, direct API access without framework overhead |
| Language | Python | >= 3.10 | Single language for entire stack |

### Why No LLM Framework (LangChain, LangGraph)?

The agent flow is a simple linear pipeline: classify → optionally draft email. There is no tool selection, no multi-agent orchestration, no retrieval, no conversation memory. Adding a framework would introduce 15+ transitive dependencies to wrap what is a single API call. See [ADR-1](#adr-1-no-llm-framework) below.

---

## 3. Data Model

### 3.1 Entity Relationship Diagram

```
┌──────────────┐        ┌──────────────────┐
│   reviews    │        │    analyses       │
├──────────────┤        ├──────────────────┤
│ id (PK)      │───1:1──│ id (PK)          │
│ customer_name│        │ review_id (FK)   │
│ customer_email        │ sentiment        │
│ product_name │        │ severity         │
│ product_cat  │        │ action           │
│ order_total  │        │ category         │
│ star_rating  │        │ reason           │
│ review_text  │        │ confidence       │
│ submitted_at │        │ draft_email_subj │
│ processed    │        │ draft_email_body │
│ processed_at │        │ email_status     │
└──────────────┘        │ analyzed_at      │
                        │ model_used       │
┌──────────────┐        └──────────────────┘
│  agent_runs  │
├──────────────┤
│ id (PK)      │
│ started_at   │
│ completed_at │
│ reviews_proc │
│ alerts_gen   │
│ status       │
│ error_message│
└──────────────┘
```

### 3.2 Table Definitions

#### `reviews`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, auto-increment | Unique review identifier |
| customer_name | VARCHAR(100) | NOT NULL | Customer's full name |
| customer_email | VARCHAR(255) | NOT NULL | Customer's email address |
| product_name | VARCHAR(255) | NOT NULL | Product being reviewed |
| product_category | VARCHAR(100) | NOT NULL | Product category (Electronics, Clothing, etc.) |
| order_total | FLOAT | NOT NULL | Order amount in USD |
| star_rating | INTEGER | NOT NULL, 1-5 | Customer's star rating |
| review_text | TEXT | NOT NULL | Full review text |
| submitted_at | DATETIME | DEFAULT now | When the review was submitted |
| processed | BOOLEAN | DEFAULT FALSE | Whether the agent has analyzed this review |
| processed_at | DATETIME | NULLABLE | When the agent processed this review |

#### `analyses`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, auto-increment | Unique analysis identifier |
| review_id | INTEGER | FK → reviews.id, UNIQUE | One analysis per review |
| sentiment | VARCHAR(20) | NOT NULL | POSITIVE, NEGATIVE, NEUTRAL, MIXED, or SPAM |
| severity | VARCHAR(10) | NULLABLE | HIGH or LOW (null for non-negative) |
| action | VARCHAR(10) | NOT NULL | ALERT, THANK, LOG, or FLAG |
| category | VARCHAR(50) | NULLABLE | Issue category (shipping, delivery_delay, wrong_item, quality, defective, safety, service, pricing, other) |
| reason | TEXT | NOT NULL | Agent's one-sentence reasoning |
| confidence | FLOAT | NULLABLE | 0.0 to 1.0 confidence score |
| draft_email_subject | VARCHAR(255) | NULLABLE | Email subject (ALERT and THANK reviews) |
| draft_email_body | TEXT | NULLABLE | Email body (ALERT and THANK reviews) |
| email_status | VARCHAR(20) | NULLABLE | draft, approved, sent, rejected |
| analyzed_at | DATETIME | DEFAULT now | When the analysis was created |
| model_used | VARCHAR(50) | NULLABLE | Model identifier used (e.g. gpt-4o) |

#### `agent_runs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, auto-increment | Unique run identifier |
| started_at | DATETIME | DEFAULT now | Run start time |
| completed_at | DATETIME | NULLABLE | Run completion time |
| reviews_processed | INTEGER | DEFAULT 0 | Count of reviews processed |
| alerts_generated | INTEGER | DEFAULT 0 | Count of ALERT actions |
| status | VARCHAR(20) | DEFAULT 'running' | running, completed, failed |
| error_message | TEXT | NULLABLE | Error details if failed |

### 3.3 Design Decision: Denormalized Schema

A normalized schema would have separate `customers`, `products`, and `orders` tables. We chose denormalization (embedding customer/product data directly in `reviews`) because:

- **3 tables vs 6** — less code, fewer relationships, simpler queries
- **No JOIN queries needed** — every review row is self-contained
- **Realistic for the use case** — review data in real systems often arrives pre-joined from APIs (Shopify, Amazon)
- **Trade-off accepted** — duplicate customer data across reviews is acceptable at demo scale

---

## 4. AI Agent Design

### 4.1 Single-Call Architecture

```
┌─────────────────────────────────────────────────┐
│              GPT-4o API Call                       │
│                                                   │
│  Input:                    Output (JSON):          │
│  ├── customer_name         ├── sentiment           │
│  ├── customer_email        ├── severity            │
│  ├── product_name          ├── action              │
│  ├── product_category      ├── category            │
│  ├── order_total           ├── reason              │
│  ├── star_rating           ├── confidence           │
│  └── review_text           ├── draft_email_subject │
│                            └── draft_email_body    │
└─────────────────────────────────────────────────┘
```

One API call handles classification, routing, and email drafting. The model returns `null` for email fields when no email is needed (LOG/FLAG actions).

### 4.2 Prompt Design

The system prompt instructs the model to:

1. Classify sentiment into 5 categories (POSITIVE, NEGATIVE, NEUTRAL, MIXED, SPAM)
2. Route to the correct action (ALERT, THANK, LOG, FLAG)
3. Assess severity using decision rules (defective → HIGH, order > $100 → HIGH)
4. Draft appropriate email: apology + request for details (ALERT) or thank-you (THANK)
5. Return structured JSON via `response_format: json_object`

**Key prompt principles:**
- Explicit output schema with field descriptions
- Clear decision rules (not vague guidelines)
- Separate email templates for ALERT vs THANK actions
- Guardrails: no admitting liability, no inventing details, no leaking customer email in body
- Conservative classification: prefer MIXED over POSITIVE when complaints exist
- Brand identity: all emails signed by "The ShopEase Team"
- "Return ONLY valid JSON" to prevent wrapper text

### 4.3 Processing Flow

```
process_reviews()
    │
    ├── Create AgentRun record (status: running)
    │
    ├── Query: SELECT * FROM reviews WHERE processed = FALSE
    │
    ├── For each review:
    │   ├── Call OpenAI API (classify_and_draft)
    │   ├── Parse JSON response
    │   ├── INSERT INTO analyses
    │   ├── UPDATE review SET processed = TRUE
    │   ├── Update AgentRun counters
    │   ├── COMMIT (per-review, not batched)
    │   └── Report progress via callback
    │
    ├── Update AgentRun (status: completed)
    └── COMMIT
```

**Per-review commits:** Each review is committed individually so that if the agent fails mid-batch, already-processed reviews are not lost and won't be re-processed on retry.

### 4.4 Error Handling

| Failure | Handling |
|---------|----------|
| OpenAI API error (rate limit, timeout) | AgentRun marked `failed` with error message, partial progress preserved |
| Invalid JSON response | Caught by `json.loads`, AgentRun marked `failed` |
| Database error | Exception propagates, AgentRun marked `failed` |

---

## 5. UI Specification

### 5.1 Page Structure

```
┌─────────────────────────────────────────────┐
│  ReviewIQ          [Sidebar Navigation]      │
│  E-Commerce        ┌──────────────────────┐  │
│  Review Agent      │                      │  │
│                    │   Page Content        │  │
│  ○ Dashboard       │                      │  │
│  ○ Reviews         │                      │  │
│  ○ Email Queue     │                      │  │
│                    │                      │  │
│  ── Test a Review  │                      │  │
│  [textarea]        │                      │  │
│  [Submit Review]   │                      │  │
│                    └──────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 5.2 Dashboard Page

```
┌──────────┬──────────┬──────────┬──────────┐
│  Total   │ Pending  │  Alerts  │ Avg      │
│ Reviews  │          │          │ Rating   │
│   15     │   10     │    1     │  3.2 ★   │
└──────────┴──────────┴──────────┴──────────┘

┌─────────────────────────┬──────────────────┐
│ Agent Processing        │ Recent Runs      │
│                         │                  │
│ [10 reviews pending]    │ ✅ May 10 14:30  │
│                         │    10 rev, 4 alt │
│ [Process New Reviews]   │                  │
│                         │                  │
│ ████████░░ 80%          │                  │
│ 🔴 Amanda — NEGATIVE    │                  │
└─────────────────────────┴──────────────────┘

┌─────────────────────────────────────────────┐
│ Recent Alerts                                │
│                                              │
│ Amanda Foster — Smart Watch FitTrack  HIGH   │
│ "Product stopped working after 3 days..."    │
└─────────────────────────────────────────────┘
```

### 5.3 Reviews Page

```
┌────────────┬────────────┬────────────────────┐
│ Status: All│ Sentiment: │ Category: All    ▼ │
│          ▼ │ All      ▼ │                    │
└────────────┴────────────┴────────────────────┘

Showing 15 reviews

▸ ★★★★★  Sarah Mitchell — Bluetooth Speaker  ✅ Processed
▸ ★★★★★  James Rodriguez — Ergonomic Chair   ✅ Processed
▾ ★☆☆☆☆  Amanda Foster — Smart Watch FitTrack ✅ Processed
  ┌─────────────────────────────────────────────┐
  │ Product: Smart Watch FitTrack (Electronics)  │
  │ Order: $159.99  |  Email: amanda.foster@...  │
  │ Sentiment: 🔴 NEGATIVE  Severity: HIGH       │
  │                                               │
  │ Review: "Terrible product. Screen stopped..." │
  │                                               │
  │ Agent: Product stopped working after 3 days   │
  │ Confidence: ████████████████░░░ 96%           │
  │                                               │
  │ 📧 Draft Email — Status: draft                │
  │ Subject: We're sorry about your FitTrack...   │
  │ [Email body text area]                        │
  └─────────────────────────────────────────────┘
▸ ★★☆☆☆  Robert Singh — Air Fryer Deluxe      ⏳ Pending
```

### 5.4 Email Queue Page

```
┌──────────────────────────────────────┐
│ Filter by Status: All              ▼ │
└──────────────────────────────────────┘

Showing 1 email

┌──────────────────────────────────────────────┐
│ Amanda Foster — Smart Watch FitTrack          │
│ (1★, $159.99)     Severity: HIGH    📝 draft │
│                                               │
│ Agent: Product stopped working after 3 days   │
│                                               │
│ Subject: We're sorry about your FitTrack...   │
│ ┌──────────────────────────────────────────┐  │
│ │ Hi Amanda,                               │  │
│ │                                          │  │
│ │ I'm truly sorry to hear that your        │  │
│ │ Smart Watch FitTrack stopped working...  │  │
│ └──────────────────────────────────────────┘  │
│                                               │
│ [✅ Approve]  [📬 Approve & Send]  [❌ Reject] │
└──────────────────────────────────────────────┘
```

### 5.5 Email Status Transitions

```
         ┌──────────┐
         │  draft   │
         └────┬─────┘
              │
        ┌─────┼──────────┐
        │     │          │
        ▼     ▼          ▼
  ┌─────────┐ │   ┌──────────┐
  │approved │ │   │ rejected │
  └────┬────┘ │   └──────────┘
       │      │
       ▼      ▼
    ┌──────┐
    │ sent │
    └──────┘
```

---

## 6. Project Structure

```
Ecomm-Customer-Review-Agent/
├── docs/
│   ├── PRD.md              # Product requirements document
│   └── TECH_SPEC.md        # This file
├── data/
│   └── Ecommerce negative review agent.xlsx  # Original dataset
├── app.py                  # Streamlit entry point (all 3 pages)
├── agent.py                # OpenAI API — classify + draft
├── models.py               # SQLAlchemy ORM (3 tables)
├── database.py             # DB engine + session factory
├── seed.py                 # Seed 15 demo reviews
├── prompt.txt              # Original Zapier prompt (reference)
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── .gitignore
└── README.md               # Setup instructions
```

---

## 7. Architectural Decision Records

### ADR-1: No LLM Framework

**Decision:** Use OpenAI SDK directly instead of LangChain/LangGraph.

**Context:** The agent makes 1 API call per review with no tool use, no memory, no retrieval, and no multi-step reasoning.

**Consequences:**
- (+) Fewer dependencies (1 vs 15+)
- (+) Easier to debug — no abstraction layers
- (+) Full control over prompt and response parsing
- (-) Would need to add framework if agent grows to need tools or multi-step flows

### ADR-2: Single LLM Call (Not Two)

**Decision:** Classify and draft email in one API call, not separate classify → draft calls.

**Context:** An earlier design used a cheaper model for classification and a better model for drafting. At demo scale (15 reviews), the cost savings of two-model routing is negligible (< $0.01).

**Consequences:**
- (+) Simpler code — one function, one prompt, one response
- (+) Faster — one round trip instead of two
- (+) Single prompt handles all 4 action types (ALERT, THANK, LOG, FLAG) with appropriate email templates
- (-) Slightly higher cost per positive review — irrelevant at demo scale

### ADR-3: SQLite Over PostgreSQL

**Decision:** Use SQLite instead of PostgreSQL.

**Context:** The app serves a single user processing 15-50 reviews. PostgreSQL would require Docker or a cloud instance.

**Consequences:**
- (+) Zero infrastructure — runs from `pip install` and `python seed.py`
- (+) Portable — database is a single file
- (+) SQLAlchemy makes this a one-line swap if PostgreSQL is needed later
- (-) No concurrent write support — irrelevant for single-user demo

### ADR-4: Denormalized Schema

**Decision:** Embed customer and product data directly in the `reviews` table instead of normalizing into separate tables.

**Context:** A normalized schema (customers, products, orders, reviews) would have 6 tables. The relationships add complexity without adding value at demo scale.

**Consequences:**
- (+) 3 tables instead of 6
- (+) No JOIN queries — simpler ORM code
- (+) Self-contained review records
- (-) Duplicate customer data if same customer leaves multiple reviews — acceptable at demo scale

### ADR-5: Streamlit Over React + FastAPI

**Decision:** Use Streamlit for the full UI instead of a React frontend with FastAPI backend.

**Context:** The dashboard is a data-centric internal tool with tables, filters, forms, and metrics. Streamlit provides all of these as built-in components.

**Consequences:**
- (+) 1 file for entire UI vs 15+ React components + API routes
- (+) All Python — no JavaScript/TypeScript context switching
- (+) Built-in state management, widgets, and layout
- (-) Limited layout customization compared to React
- (-) Not representative of production frontend architecture — acceptable for an AI agent portfolio project

---

## 8. Seed Data Summary

| Category | Count | Star Ratings | Pre-Processed? |
|----------|-------|-------------|----------------|
| Positive reviews | 7 | 4-5 ★ | 3 yes, 4 no |
| Neutral reviews | 3 | 3 ★ | 1 yes, 2 no |
| Negative reviews | 5 | 1-2 ★ | 1 yes, 4 no |
| **Total** | **15** | | **5 yes, 10 no** |

Products span 6 categories: Electronics, Furniture, Home & Kitchen, Fitness, Clothing, Beauty.
Order totals range from $19.99 to $199.99.

---

## 9. Dependencies

| Package | Purpose | License |
|---------|---------|---------|
| streamlit | Web UI framework | Apache 2.0 |
| sqlalchemy | ORM and database access | MIT |
| openai | OpenAI API client | MIT |
| python-dotenv | Load .env file for API key | BSD |
| pandas | Data manipulation for Streamlit tables | BSD |
