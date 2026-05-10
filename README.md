# ReviewIQ — E-Commerce Customer Review Agent

A web-based AI agent that monitors e-commerce customer reviews, classifies sentiment, and automatically drafts personalized apology emails for negative reviews — ready for customer support reps to review and send.

## How It Works

```
Customer Review (from DB)
        │
        ▼
  ┌─────────────────┐
  │  Claude Sonnet   │  Classifies sentiment + drafts email in one call
  │  (AI Agent)      │
  └────────┬────────┘
           │
     ┌─────┴─────┐
     │           │
  POSITIVE/    NEGATIVE
  NEUTRAL      (ALERT)
     │           │
    LOG       Draft Email
    done      for Rep to
              Review & Send
```

## Features

- **Dashboard** — stats, pending reviews, recent alerts, one-click agent processing
- **Reviews** — filterable list with expandable detail view showing agent analysis
- **Email Queue** — review, edit, approve/reject, and send AI-drafted emails

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit |
| Database | SQLite + SQLAlchemy ORM |
| AI Agent | Claude API (Anthropic SDK) |
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
# Edit .env and add your Anthropic API key

# Seed the database with sample reviews
python seed.py

# Run the app
streamlit run app.py
```

## Database Schema

3 tables — kept simple and flat:

- **`reviews`** — customer name, email, product, rating, review text, processed flag
- **`analyses`** — sentiment, severity, action, reasoning, draft email + status
- **`agent_runs`** — audit log of processing runs

## Agent Decision Logic

| Condition | Sentiment | Action | Severity |
|-----------|-----------|--------|----------|
| 4-5 stars, positive text | POSITIVE | LOG | — |
| 3 stars, neutral text | NEUTRAL | LOG | — |
| 1-2 stars, defective/safety/refund | NEGATIVE | ALERT | HIGH |
| 1-2 stars, minor complaint | NEGATIVE | ALERT | LOW |

For ALERT reviews, the agent drafts a personalized email that:
- Addresses the customer by first name
- References the specific product and issue
- Offers a resolution (refund, replacement, or discount)

## Project Structure

```
├── app.py              # Streamlit app (Dashboard, Reviews, Email Queue)
├── agent.py            # Claude API integration (classify + draft)
├── models.py           # SQLAlchemy ORM models (3 tables)
├── database.py         # DB engine and session management
├── seed.py             # Sample data (15 realistic reviews)
├── prompt.txt          # Original Zapier agent prompt (reference)
├── data/
│   └── Ecommerce negative review agent.xlsx  # Original Excel dataset
├── requirements.txt
├── .env.example
└── README.md
```

## Documentation

- **[Product Requirements Document (PRD)](docs/PRD.md)** — problem statement, user stories, functional requirements, success metrics
- **[Technical Specification](docs/TECH_SPEC.md)** — architecture, data model, AI agent design, UI wireframes, ADRs

## Background

This project started as a Zapier-based automation (see `prompt.txt` for the original agent prompt) and was rebuilt into a full-stack web application with a real database and direct Claude API integration.
