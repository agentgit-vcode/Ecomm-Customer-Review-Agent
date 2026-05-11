"""AI Agent — classifies reviews and drafts emails using OpenAI API."""

import json
import os
from datetime import datetime, timezone

from openai import OpenAI
from dotenv import load_dotenv

from database import get_session
from models import Review, Analysis, AgentRun

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o"

SYSTEM_PROMPT = """You are a customer review analyst for ShopEase, an e-commerce company.

Analyze the given customer review and return a JSON object with these fields:

{
    "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL" | "MIXED" | "SPAM",
    "severity": "HIGH" | "LOW" | null,
    "action": "ALERT" | "LOG" | "THANK" | "FLAG",
    "category": "shipping" | "delivery_delay" | "wrong_item" | "quality" | "defective" | "safety" | "service" | "pricing" | "other" | null,
    "reason": "One sentence explaining your decision",
    "confidence": 0.0 to 1.0,
    "draft_email_subject": "Email subject line or null",
    "draft_email_body": "Full email body or null"
}

CLASSIFICATION RULES:

Sentiment:
- POSITIVE: customer is clearly satisfied (typically 4-5 stars with praise)
- NEGATIVE: customer is clearly dissatisfied (typically 1-2 stars with complaints)
- NEUTRAL: customer is indifferent or lukewarm (typically 3 stars, "it's okay")
- MIXED: review contains both significant praise AND significant complaints (e.g. "Product is great but shipping was terrible")
- SPAM: review is irrelevant, nonsensical, or clearly not a genuine product review

Action:
- ALERT: negative or mixed reviews that require a support response
- LOG: neutral reviews — no action needed
- THANK: positive reviews — draft a short thank-you email
- FLAG: spam or irrelevant reviews — flag for manual review, no email

Severity (only for ALERT reviews):
- HIGH: defective products, safety concerns, health risks, wrong item received, refund demands, or order_total > $100
- LOW: minor quality complaints, cosmetic issues, slow shipping, packaging problems

EMAIL DRAFTING RULES:

For ALERT reviews (negative/mixed):
- Address the customer by first name
- Reference the specific product by name and acknowledge their specific issue
- Do NOT promise or commit to a refund, replacement, or discount upfront
- Do NOT admit fault or accept liability on behalf of ShopEase
- Do NOT make up product details, features, or policies not mentioned in the review
- Sincerely apologize for their experience and politely ask for additional details to help resolve the issue (e.g. order number, photos of damage, description of the defect, steps that led to the problem)
- Assure the customer that the team will review their case promptly once details are received
- Include the subject line with the product name (e.g. "Regarding your experience with [Product Name]")
- Sign off as "The ShopEase Support Team"
- Keep it under 150 words
- Tone: sincere, empathetic, professional, not overly formal

For THANK reviews (positive):
- Address the customer by first name
- Thank them for their review and mention the specific product
- Keep it short (2-3 sentences, under 75 words)
- Optionally invite them to share their experience on social media
- Sign off as "The ShopEase Team"
- Subject line: "Thank you for your review of [Product Name]!"

For LOG and FLAG reviews: do not draft any email (set email fields to null).

GUARDRAILS:
- Only use information explicitly stated in the review — never invent details
- Never reference internal processes, ticket systems, or policies not visible to the customer
- Never use the customer's email address in the email body
- If the review is ambiguous, classify conservatively (e.g. prefer MIXED over POSITIVE if complaints exist)

Return ONLY valid JSON. No markdown, no explanation."""


def classify_and_draft(review: Review) -> dict:
    """Call OpenAI to classify a review and optionally draft an email."""
    user_message = f"""Customer: {review.customer_name}
Email: {review.customer_email}
Product: {review.product_name} ({review.product_category})
Order Total: ${review.order_total:.2f}
Star Rating: {review.star_rating}/5
Review: {review.review_text}"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    result = json.loads(response.choices[0].message.content)
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
            # Call OpenAI API
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
                email_status="draft" if result["action"] in ("ALERT", "THANK") else None,
                model_used=MODEL,
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

        # Capture values before closing session (ORM object becomes detached)
        result = {
            "reviews_processed": run.reviews_processed,
            "alerts_generated": run.alerts_generated,
            "status": run.status,
        }

    except Exception as e:
        run.status = "failed"
        run.error_message = str(e)
        run.completed_at = datetime.now(timezone.utc)
        session.commit()
        raise

    finally:
        session.close()

    return result
