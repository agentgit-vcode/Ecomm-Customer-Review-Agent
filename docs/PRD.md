# Product Requirements Document (PRD)

## ReviewIQ — E-Commerce Customer Review Agent

| Field | Details |
|-------|---------|
| **Author** | Vaibhav Lad |
| **Date** | May 2026 |
| **Status** | MVP |
| **Version** | 1.0 |

---

## 1. Problem Statement

E-commerce companies receive hundreds of customer reviews daily. Customer support teams manually read each review, identify negative experiences, and draft personalized response emails. This process is:

- **Slow** — reps spend 5-10 minutes per negative review drafting an appropriate response
- **Inconsistent** — email quality varies by rep experience, mood, and workload
- **Reactive** — critical issues (defective products, safety concerns) get buried among routine reviews
- **Unscalable** — hiring more reps is the only way to handle volume spikes (holidays, product launches)

### Impact

| Metric | Current State | Problem |
|--------|--------------|---------|
| Response time to negative reviews | 24-48 hours | Unhappy customers churn before hearing back |
| Email drafting time per review | 5-10 min | Reps spend 60% of shift writing emails |
| Critical issue detection | Manual scanning | HIGH severity issues missed during peak volume |
| Response consistency | Varies by rep | Some emails miss apology, resolution, or empathy |

---

## 2. Proposed Solution

An AI-powered agent that automatically:

1. **Classifies** every review by sentiment (positive, negative, neutral)
2. **Triages** negative reviews by severity (high, low)
3. **Drafts** personalized apology emails for negative reviews
4. **Queues** drafts for human review before sending

The agent handles the analysis and writing. The human makes the final call.

### What This Is NOT

- Not a fully autonomous system — humans review and approve every email
- Not a chatbot — it processes batch reviews, not real-time conversations
- Not a replacement for customer support — it's a tool that makes reps faster

---

## 3. Target Users

| User | Role | How They Use ReviewIQ |
|------|------|----------------------|
| **Customer Support Rep** | Reviews and sends emails | Opens dashboard daily, processes new reviews, edits/approves draft emails |
| **Support Team Lead** | Monitors team performance | Checks dashboard for alert volume, severity trends, agent run history |

---

## 4. User Stories

### Customer Support Rep

| ID | Story | Priority |
|----|-------|----------|
| US-1 | As a rep, I want to see how many reviews are pending so I know my workload | P0 |
| US-2 | As a rep, I want to process all pending reviews with one click so I don't handle them one by one | P0 |
| US-3 | As a rep, I want to see the AI's sentiment classification and reasoning so I can trust its judgment | P0 |
| US-4 | As a rep, I want to review and edit draft emails before sending so I maintain quality control | P0 |
| US-5 | As a rep, I want to approve or reject draft emails so only appropriate responses go out | P0 |
| US-6 | As a rep, I want to filter reviews by sentiment and category so I can prioritize critical issues | P1 |
| US-7 | As a rep, I want to see the customer's order details alongside their review so I have full context | P1 |

### Support Team Lead

| ID | Story | Priority |
|----|-------|----------|
| US-8 | As a lead, I want to see alert counts and average ratings on a dashboard so I can spot trends | P1 |
| US-9 | As a lead, I want to see agent run history so I know when reviews were last processed | P2 |

---

## 5. Functional Requirements

### FR-1: Review Ingestion

- System stores customer reviews with: customer name, email, product name, product category, order total, star rating (1-5), review text, submission date
- Each review has a `processed` flag to track whether the agent has analyzed it
- System is pre-loaded with seed data for demonstration

### FR-2: AI Agent Processing

- Agent processes all unprocessed reviews when triggered by the user
- For each review, the agent returns:
  - **Sentiment**: POSITIVE, NEGATIVE, or NEUTRAL
  - **Severity**: HIGH or LOW (for negative reviews only)
  - **Action**: ALERT (needs email) or LOG (no action needed)
  - **Category**: shipping, quality, defective, service, pricing, or other
  - **Reason**: one-sentence explanation of the decision
  - **Confidence**: 0.0 to 1.0 score
- For ALERT reviews, the agent also drafts a personalized email
- Agent tracks each processing run (start time, end time, count of reviews processed, alerts generated)

### FR-3: Email Drafting

- Draft emails must address the customer by first name
- Draft emails must reference the specific product and issue
- Draft emails must offer a concrete resolution (refund, replacement, or discount)
- Draft emails must be under 150 words
- Tone: sincere, professional, not overly formal

### FR-4: Email Queue Workflow

- Draft emails enter the queue with status `draft`
- Reps can transition emails through: `draft` → `approved` → `sent`
- Reps can reject emails: `draft` → `rejected`
- Reps can edit the email body before approving
- Sent and rejected emails are read-only

### FR-5: Dashboard

- Display summary stats: total reviews, pending count, alert count, average star rating
- Show recent alerts with severity, customer name, product, and email status
- Provide a "Process New Reviews" button with real-time progress feedback
- Show recent agent run history

### FR-6: Reviews List

- Display all reviews in a sortable, filterable list
- Filter by: processing status (all, processed, pending), sentiment, product category
- Expandable row showing full review text, agent analysis, and draft email (if applicable)

---

## 6. Non-Functional Requirements

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| **Setup time** | Under 5 minutes | Reviewer should be able to clone and run without Docker or external DBs |
| **Processing speed** | Under 5 seconds per review | Acceptable wait time for batch processing of 10-15 reviews |
| **Agent accuracy** | 90%+ sentiment classification | Negative reviews must not be classified as positive |
| **Email quality** | Coherent, empathetic, actionable | Drafted emails should require minimal editing |
| **Data persistence** | SQLite file-based | Survives app restarts, zero infrastructure needed |

---

## 7. Agent Decision Matrix

| Star Rating | Review Content | Sentiment | Action | Severity |
|-------------|---------------|-----------|--------|----------|
| 4-5 | Praise, satisfaction | POSITIVE | LOG | — |
| 3 | Lukewarm, mixed feelings | NEUTRAL | LOG | — |
| 1-2 | Defective, safety, refund request | NEGATIVE | ALERT | HIGH |
| 1-2 | Slow shipping, minor cosmetic issue | NEGATIVE | ALERT | LOW |
| 1-2 | Order total > $100 | NEGATIVE | ALERT | HIGH |

---

## 8. Success Metrics

| Metric | How to Measure | Target |
|--------|---------------|--------|
| **Classification accuracy** | Manually verify sentiment on 15 seed reviews | 90%+ correct |
| **Email acceptance rate** | % of drafts approved without edits | 70%+ |
| **Time to process** | Clock the "Process New Reviews" flow | Under 60 seconds for 10 reviews |
| **Setup success rate** | Can a new user run it from README instructions | 100% |

---

## 9. Out of Scope (V1)

- Real email delivery (SendGrid, SES) — emails are marked "sent" but not actually dispatched
- User authentication and role-based access
- Real-time review ingestion via API/webhook
- Multi-language review support
- Review response tracking (did the customer reply?)
- Analytics and reporting charts
- Mobile-responsive design

---

## 10. Future Enhancements (V2+)

| Enhancement | Value |
|-------------|-------|
| Connect to real email service (SendGrid) | Emails actually reach customers |
| Webhook/API for real-time review ingestion | Process reviews as they arrive, not in batches |
| Sentiment trend charts over time | Team leads can spot product quality issues early |
| Multi-agent setup: classifier agent + writer agent + reviewer agent | Better separation of concerns, specialized prompts |
| Integration with Shopify/Amazon review APIs | Pull real review data automatically |
