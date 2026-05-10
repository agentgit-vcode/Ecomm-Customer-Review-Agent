"""Seed the database with 15 realistic customer reviews."""

import os
import sys
from datetime import datetime, timedelta, timezone

from database import init_db, get_session
from models import Review, Analysis

# fmt: off
SEED_REVIEWS = [
    # --- POSITIVE REVIEWS (7) ---
    {
        "customer_name": "Sarah Mitchell",
        "customer_email": "sarah.mitchell@email.com",
        "product_name": "Bluetooth Speaker Pro",
        "product_category": "Electronics",
        "order_total": 49.99,
        "star_rating": 5,
        "review_text": "Absolutely love this speaker! The sound quality is incredible for the price. Bass is punchy and clear even at high volumes. Been using it daily for two weeks now and battery life is amazing.",
        "days_ago": 30,
    },
    {
        "customer_name": "James Rodriguez",
        "customer_email": "j.rodriguez@email.com",
        "product_name": "Ergonomic Office Chair",
        "product_category": "Furniture",
        "order_total": 189.99,
        "star_rating": 5,
        "review_text": "Best chair I've ever owned. Assembly took about 20 minutes and the lumbar support is perfect. My back pain has significantly reduced since switching to this. Highly recommend for anyone working from home.",
        "days_ago": 25,
    },
    {
        "customer_name": "Emily Watson",
        "customer_email": "emily.w@email.com",
        "product_name": "Stainless Steel Water Bottle",
        "product_category": "Home & Kitchen",
        "order_total": 24.99,
        "star_rating": 4,
        "review_text": "Good quality bottle, keeps water cold all day. The lid is easy to open and close. Only reason for 4 stars instead of 5 is the color was slightly different from the picture, but still looks nice.",
        "days_ago": 22,
    },
    {
        "customer_name": "Michael Chen",
        "customer_email": "m.chen@email.com",
        "product_name": "Wireless Mouse",
        "product_category": "Electronics",
        "order_total": 29.99,
        "star_rating": 4,
        "review_text": "Smooth and responsive, works great for daily use. Connected instantly via Bluetooth. Comfortable grip even after long hours. Would buy again.",
        "days_ago": 18,
    },
    {
        "customer_name": "Lisa Park",
        "customer_email": "lisa.park@email.com",
        "product_name": "Yoga Mat Premium",
        "product_category": "Fitness",
        "order_total": 34.99,
        "star_rating": 5,
        "review_text": "Excellent grip and thickness. No sliding during poses even with sweaty hands. The carrying strap is a nice bonus. Great value for a premium mat.",
        "days_ago": 15,
    },
    {
        "customer_name": "David Thompson",
        "customer_email": "d.thompson@email.com",
        "product_name": "LED Desk Lamp",
        "product_category": "Home & Kitchen",
        "order_total": 42.99,
        "star_rating": 4,
        "review_text": "Nice lamp with good brightness levels. The USB charging port on the base is super convenient. Touch controls are responsive. Modern design fits my desk setup well.",
        "days_ago": 12,
    },
    {
        "customer_name": "Rachel Green",
        "customer_email": "rachel.g@email.com",
        "product_name": "Running Shoes CloudStep",
        "product_category": "Clothing",
        "order_total": 119.99,
        "star_rating": 5,
        "review_text": "These shoes are incredibly comfortable right out of the box. No break-in period needed. Used them for a half marathon and my feet felt great afterwards. The cushioning is perfect.",
        "days_ago": 8,
    },

    # --- NEUTRAL REVIEWS (3) ---
    {
        "customer_name": "Tom Baker",
        "customer_email": "tom.baker@email.com",
        "product_name": "USB-C Hub 7-in-1",
        "product_category": "Electronics",
        "order_total": 39.99,
        "star_rating": 3,
        "review_text": "It works but nothing special. All ports function as described. Gets a bit warm after extended use which concerns me slightly. For the price its okay I guess.",
        "days_ago": 20,
    },
    {
        "customer_name": "Nancy Kim",
        "customer_email": "nancy.kim@email.com",
        "product_name": "Cotton T-Shirt Pack",
        "product_category": "Clothing",
        "order_total": 29.99,
        "star_rating": 3,
        "review_text": "Average quality t-shirts. Fit is true to size but the fabric feels thinner than expected. They're fine for everyday wear but nothing premium about them. You get what you pay for.",
        "days_ago": 14,
    },
    {
        "customer_name": "Kevin Patel",
        "customer_email": "k.patel@email.com",
        "product_name": "Phone Case ArmorShield",
        "product_category": "Electronics",
        "order_total": 19.99,
        "star_rating": 3,
        "review_text": "Does the job of protecting my phone. The grip could be better and the buttons are a bit stiff. Camera cutout fits fine. Its an average case, not bad not great.",
        "days_ago": 10,
    },

    # --- NEGATIVE REVIEWS (5) ---
    {
        "customer_name": "Amanda Foster",
        "customer_email": "amanda.foster@email.com",
        "product_name": "Smart Watch FitTrack",
        "product_category": "Electronics",
        "order_total": 159.99,
        "star_rating": 1,
        "review_text": "Terrible product. The screen stopped working after just 3 days of normal use. Won't turn on anymore no matter what I try. For $160 I expected something that actually lasts. I want a full refund immediately. Complete waste of money.",
        "days_ago": 7,
    },
    {
        "customer_name": "Robert Singh",
        "customer_email": "r.singh@email.com",
        "product_name": "Air Fryer Deluxe",
        "product_category": "Home & Kitchen",
        "order_total": 89.99,
        "star_rating": 2,
        "review_text": "Very disappointed. The temperature control is inaccurate, food comes out either undercooked or burnt. The basket coating started peeling after two weeks. This feels like a cheap knockoff product. Considering returning it.",
        "days_ago": 6,
    },
    {
        "customer_name": "Jennifer Lopez",
        "customer_email": "jen.lopez@email.com",
        "product_name": "Backpack TravelMax",
        "product_category": "Clothing",
        "order_total": 64.99,
        "star_rating": 1,
        "review_text": "The product arrived with a broken zipper on the main compartment and a small tear on the side pocket. Clearly this was not inspected before shipping. I need a replacement or my money back. Very frustrating experience.",
        "days_ago": 4,
    },
    {
        "customer_name": "Chris Williams",
        "customer_email": "chris.w@email.com",
        "product_name": "Noise Cancelling Headphones",
        "product_category": "Electronics",
        "order_total": 199.99,
        "star_rating": 1,
        "review_text": "The noise cancellation barely works and theres a constant buzzing in the left ear. For $200 these should be flawless. Tried resetting multiple times, same issue. The build quality feels plasticky and cheap. Want a refund, these are defective.",
        "days_ago": 3,
    },
    {
        "customer_name": "Maria Gonzalez",
        "customer_email": "maria.g@email.com",
        "product_name": "Face Serum Vitamin C",
        "product_category": "Beauty",
        "order_total": 32.99,
        "star_rating": 2,
        "review_text": "Caused redness and irritation on my skin after first use. The product smells off, like it might be expired. The packaging also looked tampered with when it arrived. I'm worried about the quality control on this item.",
        "days_ago": 2,
    },
]
# fmt: on

# Pre-built analyses for the first 5 reviews (so dashboard has data on first load)
PRE_ANALYZED = [
    {
        "review_index": 0,
        "sentiment": "POSITIVE",
        "action": "LOG",
        "severity": None,
        "category": None,
        "reason": "Customer is highly satisfied with sound quality, bass, and battery life.",
        "confidence": 0.97,
    },
    {
        "review_index": 1,
        "sentiment": "POSITIVE",
        "action": "LOG",
        "severity": None,
        "category": None,
        "reason": "Customer reports excellent product quality and health benefits from the chair.",
        "confidence": 0.98,
    },
    {
        "review_index": 2,
        "sentiment": "POSITIVE",
        "action": "LOG",
        "severity": None,
        "category": None,
        "reason": "Satisfied customer with minor cosmetic concern about color accuracy.",
        "confidence": 0.90,
    },
    {
        "review_index": 7,
        "sentiment": "NEUTRAL",
        "action": "LOG",
        "severity": None,
        "category": "quality",
        "reason": "Customer finds the product functional but unremarkable with minor heat concern.",
        "confidence": 0.85,
    },
    {
        "review_index": 10,
        "sentiment": "NEGATIVE",
        "action": "ALERT",
        "severity": "HIGH",
        "category": "defective",
        "reason": "Product stopped working after 3 days — likely defective unit requiring immediate refund.",
        "confidence": 0.96,
        "draft_email_subject": "We're sorry about your FitTrack Smart Watch experience",
        "draft_email_body": (
            "Hi Amanda,\n\n"
            "I'm truly sorry to hear that your Smart Watch FitTrack stopped working after just three days. "
            "That is absolutely not the experience we want for our customers, and I completely understand your frustration.\n\n"
            "I've initiated a full refund of $159.99 to your original payment method. You should see it reflected "
            "within 3-5 business days. You do not need to return the defective unit.\n\n"
            "If you'd prefer a replacement instead, please let me know and I'll have one shipped out with priority "
            "delivery at no extra cost.\n\n"
            "Again, I sincerely apologize for the inconvenience.\n\n"
            "Best regards,\n"
            "Customer Support Team"
        ),
    },
]


def seed_database():
    """Populate the database with sample reviews and pre-built analyses."""
    session = get_session()

    # Check if already seeded
    existing = session.query(Review).count()
    if existing > 0:
        print(f"Database already has {existing} reviews. Skipping seed.")
        session.close()
        return

    now = datetime.now(timezone.utc)

    # Insert reviews
    reviews = []
    for data in SEED_REVIEWS:
        review = Review(
            customer_name=data["customer_name"],
            customer_email=data["customer_email"],
            product_name=data["product_name"],
            product_category=data["product_category"],
            order_total=data["order_total"],
            star_rating=data["star_rating"],
            review_text=data["review_text"],
            submitted_at=now - timedelta(days=data["days_ago"]),
            processed=False,
        )
        session.add(review)
        reviews.append(review)

    session.flush()  # Get IDs assigned

    # Mark pre-analyzed reviews as processed and create analyses
    for pre in PRE_ANALYZED:
        review = reviews[pre["review_index"]]
        review.processed = True
        review.processed_at = now - timedelta(days=1)

        analysis = Analysis(
            review_id=review.id,
            sentiment=pre["sentiment"],
            severity=pre.get("severity"),
            action=pre["action"],
            category=pre.get("category"),
            reason=pre["reason"],
            confidence=pre.get("confidence"),
            draft_email_subject=pre.get("draft_email_subject"),
            draft_email_body=pre.get("draft_email_body"),
            email_status="draft" if pre["action"] == "ALERT" else None,
            model_used="pre-seeded",
        )
        session.add(analysis)

    session.commit()
    session.close()

    processed_count = len(PRE_ANALYZED)
    remaining = len(SEED_REVIEWS) - processed_count
    print(f"Seeded {len(SEED_REVIEWS)} reviews ({processed_count} pre-analyzed, {remaining} pending).")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    init_db()
    seed_database()
    print("Done!")
