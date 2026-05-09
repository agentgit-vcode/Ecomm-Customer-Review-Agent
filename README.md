# E-Commerce Customer Review Agent

A single-agent system built on Zapier that monitors e-commerce customer reviews, categorizes them as positive or negative, and drafts email responses for negative reviews requiring customer support follow-up.

## Overview

This agent automates the customer review triage process:

1. **Reads** customer reviews from a Google Sheet
2. **Categorizes** each review as positive or negative
3. **Positive reviews** — no action required, logged only
4. **Negative reviews** — drafts a personalized apology email for a customer rep to review and send

## Architecture

```
Google Sheets (Reviews)
        │
        ▼
  Zapier Agent (AI)
   ┌────┴────┐
   │         │
Positive   Negative
 (LOG)     (ALERT)
   │         │
   ▼         ▼
  Skip    Draft Email
          for Review
```

### Agent Decision Logic

The agent evaluates each review and decides:
- **Severity**: `HIGH` or `LOW`
- **Action**: `ALERT` (requires response) or `LOG` (no action needed)

Decision factors:
- Issues during **PAYMENT** step are treated as more critical
- Higher cart values imply higher revenue impact
- Elevated baseline failure rates suggest systemic issues
- Mobile-heavy issues may indicate gateway or UX problems

### Tools Used

| Tool | Purpose |
|------|---------|
| Google Sheets | Read reviews, write agent decisions, manage state |
| Zapier Webhooks | Trigger downstream email drafting workflow |
| Zapier AI Agent | Core decision-making engine |

## Data

The sample dataset (`data/Ecommerce negative review agent.xlsx`) contains customer reviews with columns:
- **Review** — the customer's review text
- **Mail Draft** — the agent-generated email response (for negative reviews)

## Setup

1. Create a Zapier account
2. Set up a Google Sheet with review data (see sample in `data/`)
3. Create a Zapier AI Agent with the prompt from `prompt.txt`
4. Configure the following Zapier tools for the agent:
   - Google Sheets: Lookup Spreadsheet Rows (Advanced) — for state management
   - Google Sheets: Get Many Spreadsheet Rows (Advanced) — for reading reviews
   - Google Sheets: Create Spreadsheet Row — for writing decisions
   - Webhooks by Zapier: POST — for triggering email drafts
5. Set up a downstream Zap to handle webhook events and draft emails

> **Note**: Replace `<YOUR_ZAPIER_WEBHOOK_URL>` in `prompt.txt` with your actual webhook URL. Never commit real webhook URLs to version control.

## Project Structure

```
├── README.md          # This file
├── prompt.txt         # Zapier AI Agent prompt (webhook URL redacted)
├── data/
│   └── Ecommerce negative review agent.xlsx  # Sample review dataset
└── .gitignore
```
