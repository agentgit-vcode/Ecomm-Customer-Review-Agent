"""AI Agent — classifies reviews and drafts emails using Claude API."""

import json
import os
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv

from database import get_session
from models import Review, Analysis, AgentRun

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a customer review analyst for an e-commerce company.

Analyze the given customer review and return a JSON object with these fields:

{
    "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
    "severity": "HIGH" | "LOW" | null,
    "action": "ALERT" | "LOG",
    "category": "shipping" | "quality" | "defective" | "service" | "pricing" | "other" | null,
    "reason": "One sentence explaining your decision",
    "confidence": 0.0 to 1.0,
    "draft_email_subject": "Email subject line or null",
    "draft_email_body": "Full email body or null"
}

Decision rules:
- POSITIVE/NEUTRAL reviews → action: LOG, severity: null, no email drafted
- NEGATIVE reviews → action: ALERT, assess severity
- HIGH severity: defective products, safety issues, refund requests, or order_total > $100
- LOW severity: minor complaints, cosmetic issues, slow shipping
- For ALERT reviews, draft a professional, empathetic apology email:
  - Address the customer by first name
  - Reference the specific product and their issue
  - Offer a concrete resolution (refund, replacement, or discount)
  - Keep it under 150 words
  - Tone: sincere, professional, not overly formal

Return ONLY valid JSON. No markdown, no explanation."""


def classify_and_draft(review: Review) -> dict:
    """Call Claude to classify a review and optionally draft an email."""
    user_message = f"""Customer: {review.customer_name}
Email: {review.customer_email}
Product: {review.product_name} ({review.product_category})
Order Total: ${review.order_total:.2f}
Star Rating: {review.star_rating}/5
Review: {review.review_text}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    result = json.loads(response.content[0].text)
    return result


def process_reviews(progress_callback=None):
    """Process all unprocessed reviews. Returns the AgentRun record."""
    session = get_session()

    # Create agent run record
    run = AgentRun(started_at=datetime.now(timezone.utc))
    session.add(run)
    session.commit()

    try:
        unprocessed = (
            session.query(Review)
            .filter(Review.processed == False)  # noqa: E712
            .order_by(Review.submitted_at)
            .all()
        )

        total = len(unprocessed)

        for i, review in enumerate(unprocessed):
            # Call Claude API
            result = classify_and_draft(review)

            # Save analysis
            analysis = Analysis(
                review_id=review.id,
                sentiment=result["sentiment"],
                severity=result.get("severity"),
                action=result["action"],
                category=result.get("category"),
                reason=result["reason"],
                confidence=result.get("confidence"),
                draft_email_subject=result.get("draft_email_subject"),
                draft_email_body=result.get("draft_email_body"),
                email_status="draft" if result["action"] == "ALERT" else None,
                model_used="claude-sonnet-4-20250514",
            )
            session.add(analysis)

            # Mark review as processed
            review.processed = True
            review.processed_at = datetime.now(timezone.utc)

            # Update run stats
            run.reviews_processed += 1
            if result["action"] == "ALERT":
                run.alerts_generated += 1

            session.commit()

            # Report progress
            if progress_callback:
                progress_callback(i + 1, total, review.customer_name, result["sentiment"])

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        session.commit()

    except Exception as e:
        run.status = "failed"
        run.error_message = str(e)
        run.completed_at = datetime.now(timezone.utc)
        session.commit()
        raise

    finally:
        session.close()

    return run
