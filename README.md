# ReviewIQ — E-Commerce Customer Review Agent

A web-based AI agent for ShopEase that monitors customer reviews, classifies sentiment, drafts apology emails for negative reviews (requesting details before committing to resolutions), and sends thank-you notes for positive reviews — all ready for customer support reps to review and send.

## How It Works

```
Customer Review (from DB or manual input)
        │
        ▼
  ┌─────────────────┐
  │     GPT-4o       │  Classifies sentiment + drafts email in one call
  │   (AI Agent)     │
  └────────┬────────┘
           │
   ┌───────┼───────┬──────────┐
   │       │       │          │
POSITIVE NEUTRAL NEGATIVE   SPAM
 (THANK)  (LOG)  (ALERT)   (FLAG)
   │       │       │          │
Thank-you  No    Apology +  Flag for
 email   action  ask for    manual
                 details    review
```

## Features

- **Dashboard** — stats, pending reviews, recent alerts, one-click agent processing
- **Reviews** — filterable list (5 sentiments, 9 categories) with expandable detail view
- **Email Queue** — review, edit, approve/reject AI-drafted emails (apologies + thank-yous)
- **Test a Review** — paste any review text in the sidebar to test the agent instantly

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit |
| Database | SQLite + SQLAlchemy ORM |
| AI Agent | OpenAI GPT-4o (OpenAI SDK) |
| Language | 100% Python |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/agentgit-vcode/Ecomm-Customer-Review-Agent.git
cd Ecomm-Customer-Review-Agent

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your OpenAI API key

# Seed the database with sample reviews
python seed.py

# Run the app
streamlit run app.py
```

## Database Schema

3 tables — kept simple and flat:

- **`reviews`** — customer name, email, product, rating, review text, processed flag
- **`analyses`** — sentiment, severity, action, category, reasoning, draft email + status
- **`agent_runs`** — audit log of processing runs

## Agent Decision Logic

| Condition | Sentiment | Action | Severity | Email |
|-----------|-----------|--------|----------|-------|
| 4-5 stars, praise | POSITIVE | THANK | — | Thank-you note |
| 3 stars, lukewarm | NEUTRAL | LOG | — | None |
| Mixed praise + complaint | MIXED | ALERT | LOW | Apology + ask for details |
| 1-2 stars, defective/safety/refund | NEGATIVE | ALERT | HIGH | Apology + ask for details |
| 1-2 stars, minor complaint | NEGATIVE | ALERT | LOW | Apology + ask for details |
| Irrelevant or nonsensical | SPAM | FLAG | — | None (flagged) |

**For ALERT emails, the agent:**
- Addresses the customer by first name
- Acknowledges the specific product and issue
- Does NOT promise refunds or replacements upfront
- Asks for additional details (order number, photos, description)
- Assures prompt follow-up once details are received

**Guardrails:**
- Never admits fault or liability on behalf of ShopEase
- Never invents product details not in the review
- Never includes the customer's email in the email body

## Project Structure

```
├── app.py              # Streamlit app (Dashboard, Reviews, Email Queue)
├── agent.py            # OpenAI API integration (classify + draft)
├── models.py           # SQLAlchemy ORM models (3 tables)
├── database.py         # DB engine and session management
├── seed.py             # Sample data (15 realistic reviews)
├── docs/
│   ├── PRD.md          # Product Requirements Document
│   └── TECH_SPEC.md    # Technical Specification
├── requirements.txt
├── .env.example
└── README.md
```

## Documentation

- **[Product Requirements Document (PRD)](docs/PRD.md)** — problem statement, user stories, functional requirements, decision matrix, success metrics
- **[Technical Specification](docs/TECH_SPEC.md)** — architecture, data model, AI agent prompt design, UI wireframes, ADRs

## Background

This project started as a Zapier-based automation and was rebuilt into a full-stack web application with a real database and direct OpenAI API integration.
