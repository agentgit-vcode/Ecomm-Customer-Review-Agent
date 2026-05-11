"""ReviewIQ — E-Commerce Customer Review Agent Dashboard."""

import os
from datetime import datetime, timezone

import streamlit as st
import pandas as pd
from sqlalchemy import func

from database import init_db, get_session
from models import Review, Analysis, AgentRun
from agent import process_reviews

# --- Page Config ---
st.set_page_config(
    page_title="ReviewIQ",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Initialize DB ---
os.makedirs("data", exist_ok=True)
init_db()

# --- Sidebar ---
st.sidebar.title("ReviewIQ")
st.sidebar.caption("E-Commerce Review Agent")
st.sidebar.divider()
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Reviews", "Email Queue"],
    label_visibility="collapsed",
)

# --- Test a Review ---
st.sidebar.divider()
st.sidebar.subheader("Test a Review")
test_review = st.sidebar.text_area("Paste or write a review", height=120, placeholder="e.g. The product broke after 2 days. Very disappointed...")

if st.sidebar.button("Submit Review", type="primary", use_container_width=True, disabled=not test_review):
    session = get_session()
    review = Review(
        customer_name="Test Customer",
        customer_email="test@example.com",
        product_name="Sample Product",
        product_category="General",
        order_total=49.99,
        star_rating=3,
        review_text=test_review,
        submitted_at=datetime.now(timezone.utc),
        processed=False,
    )
    session.add(review)
    session.commit()
    session.close()
    st.sidebar.success("Review added! Go to Dashboard to process it.")
    st.rerun()


# ============================================================
#  DASHBOARD PAGE
# ============================================================
def render_dashboard():
    st.title("Dashboard")

    session = get_session()

    # Stats
    total_reviews = session.query(Review).count()
    pending_reviews = session.query(Review).filter(Review.processed == False).count()  # noqa: E712
    total_alerts = session.query(Analysis).filter(Analysis.action == "ALERT").count()
    avg_rating = session.query(func.avg(Review.star_rating)).scalar() or 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reviews", total_reviews)
    col2.metric("Pending", pending_reviews, delta=f"-{total_reviews - pending_reviews} processed", delta_color="normal")
    col3.metric("Alerts", total_alerts)
    col4.metric("Avg Rating", f"{avg_rating:.1f} ★")

    st.divider()

    # --- Process Reviews Button ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Agent Processing")
        if pending_reviews == 0:
            st.success("All reviews have been processed!")
        else:
            st.info(f"{pending_reviews} reviews waiting to be processed.")

            if st.button("Process New Reviews", type="primary", use_container_width=True):
                progress_bar = st.progress(0, text="Starting agent...")
                status_text = st.empty()

                def on_progress(current, total, customer_name, sentiment):
                    progress_bar.progress(
                        current / total,
                        text=f"Processing {current}/{total}...",
                    )
                    emoji = {"POSITIVE": "✅", "NEGATIVE": "🚨", "NEUTRAL": "➖", "MIXED": "⚠️", "SPAM": "🚫"}.get(sentiment, "")
                    status_text.text(f"{emoji} {customer_name} — {sentiment}")

                try:
                    result = process_reviews(progress_callback=on_progress)
                    progress_bar.progress(1.0, text="Complete!")
                    st.success(
                        f"Processed {result['reviews_processed']} reviews. "
                        f"{result['alerts_generated']} alerts generated."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Agent failed: {e}")

    with col_right:
        st.subheader("Recent Runs")
        runs = session.query(AgentRun).order_by(AgentRun.started_at.desc()).limit(5).all()
        if runs:
            for run in runs:
                status_emoji = {"completed": "✅", "failed": "❌", "running": "⏳"}.get(run.status, "")
                st.text(
                    f"{status_emoji} {run.started_at.strftime('%b %d %H:%M')} — "
                    f"{run.reviews_processed} reviews, {run.alerts_generated} alerts"
                )
        else:
            st.caption("No agent runs yet.")

    st.divider()

    # --- Recent Alerts ---
    st.subheader("Recent Alerts")
    alerts = (
        session.query(Analysis, Review)
        .join(Review)
        .filter(Analysis.action == "ALERT")
        .order_by(Analysis.analyzed_at.desc())
        .limit(10)
        .all()
    )

    if alerts:
        for analysis, review in alerts:
            severity_color = "red" if analysis.severity == "HIGH" else "orange"
            email_icon = {"draft": "📝", "approved": "✅", "sent": "📬", "rejected": "❌"}.get(
                analysis.email_status, ""
            )
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                c1.markdown(f"**{review.customer_name}** — {review.product_name}")
                c2.text(analysis.reason[:80])
                c3.markdown(f":{severity_color}[{analysis.severity}]")
                c4.text(f"{email_icon} {analysis.email_status or ''}")
    else:
        st.caption("No alerts yet. Process some reviews to get started.")

    session.close()


# ============================================================
#  REVIEWS PAGE
# ============================================================
def render_reviews():
    st.title("Reviews")

    session = get_session()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox("Status", ["All", "Processed", "Pending"])
    with col2:
        filter_sentiment = st.selectbox("Sentiment", ["All", "POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "SPAM"])
    with col3:
        filter_category = st.selectbox(
            "Product Category",
            ["All", "Electronics", "Home & Kitchen", "Clothing", "Furniture", "Fitness", "Beauty"],
        )

    # Build query
    query = session.query(Review).order_by(Review.submitted_at.desc())

    if filter_status == "Processed":
        query = query.filter(Review.processed == True)  # noqa: E712
    elif filter_status == "Pending":
        query = query.filter(Review.processed == False)  # noqa: E712

    if filter_category != "All":
        query = query.filter(Review.product_category == filter_category)

    reviews = query.all()

    # Apply sentiment filter (requires join with analysis)
    if filter_sentiment != "All":
        review_ids_with_sentiment = [
            a.review_id
            for a in session.query(Analysis).filter(Analysis.sentiment == filter_sentiment).all()
        ]
        reviews = [r for r in reviews if r.id in review_ids_with_sentiment]

    st.caption(f"Showing {len(reviews)} reviews")

    # Display reviews
    for review in reviews:
        analysis = review.analysis

        # Build header
        stars = "★" * review.star_rating + "☆" * (5 - review.star_rating)
        status_badge = "✅ Processed" if review.processed else "⏳ Pending"

        with st.expander(
            f"{stars}  **{review.customer_name}** — {review.product_name}  |  {status_badge}"
        ):
            # Review details
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**Product:** {review.product_name} ({review.product_category})")
                st.markdown(f"**Order Total:** ${review.order_total:.2f}")
                st.markdown(f"**Date:** {review.submitted_at.strftime('%b %d, %Y')}")
            with col2:
                st.markdown(f"**Email:** {review.customer_email}")
                st.markdown(f"**Rating:** {review.star_rating}/5")
            with col3:
                if analysis:
                    sentiment_emoji = {"POSITIVE": "🟢", "NEGATIVE": "🔴", "NEUTRAL": "🟡", "MIXED": "🟠", "SPAM": "⛔"}.get(
                        analysis.sentiment, ""
                    )
                    st.markdown(f"**Sentiment:** {sentiment_emoji} {analysis.sentiment}")
                    if analysis.severity:
                        st.markdown(f"**Severity:** {analysis.severity}")
                    st.markdown(f"**Action:** {analysis.action}")

            st.divider()
            st.markdown("**Review:**")
            st.text(review.review_text)

            # Show analysis if available
            if analysis:
                st.divider()
                st.markdown(f"**Agent Reasoning:** {analysis.reason}")
                if analysis.confidence:
                    st.progress(analysis.confidence, text=f"Confidence: {analysis.confidence:.0%}")

                # Show draft email if exists
                if analysis.draft_email_body:
                    st.divider()
                    st.markdown(f"**📧 Draft Email** — Status: `{analysis.email_status}`")
                    st.markdown(f"**Subject:** {analysis.draft_email_subject}")
                    st.text_area(
                        "Email Body",
                        value=analysis.draft_email_body,
                        height=200,
                        disabled=True,
                        key=f"review_email_{review.id}",
                    )

    session.close()


# ============================================================
#  EMAIL QUEUE PAGE
# ============================================================
def render_email_queue():
    st.title("Email Queue")

    session = get_session()

    # Filter by status
    filter_status = st.selectbox("Filter by Status", ["All", "draft", "approved", "sent", "rejected"])

    query = (
        session.query(Analysis, Review)
        .join(Review)
        .filter(Analysis.action.in_(["ALERT", "THANK"]))
        .filter(Analysis.draft_email_body.isnot(None))
        .order_by(Analysis.analyzed_at.desc())
    )

    if filter_status != "All":
        query = query.filter(Analysis.email_status == filter_status)

    emails = query.all()

    st.caption(f"Showing {len(emails)} emails")

    if not emails:
        st.info("No emails to display. Process some reviews with negative sentiment to generate draft emails.")
        session.close()
        return

    for analysis, review in emails:
        status_emoji = {"draft": "📝", "approved": "✅", "sent": "📬", "rejected": "❌"}.get(
            analysis.email_status, ""
        )

        with st.container(border=True):
            # Header row
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(
                    f"**{review.customer_name}** — {review.product_name}  "
                    f"({review.star_rating}★, ${review.order_total:.2f})"
                )
            with col2:
                if analysis.action == "THANK":
                    st.markdown(f"Type: :green[**THANK YOU**]")
                elif analysis.severity:
                    severity_color = "red" if analysis.severity == "HIGH" else "orange"
                    st.markdown(f"Severity: :{severity_color}[**{analysis.severity}**]")
            with col3:
                st.markdown(f"Status: {status_emoji} **{analysis.email_status}**")

            # Reason
            st.caption(f"Agent reasoning: {analysis.reason}")

            # Email content
            st.markdown(f"**Subject:** {analysis.draft_email_subject}")

            # Editable email body
            edited_body = st.text_area(
                "Email Body",
                value=analysis.draft_email_body,
                height=200,
                key=f"email_body_{analysis.id}",
                disabled=analysis.email_status in ("sent", "rejected"),
            )

            # Action buttons
            if analysis.email_status == "draft":
                btn_col1, btn_col2, btn_col3 = st.columns(3)

                with btn_col1:
                    if st.button("✅ Approve", key=f"approve_{analysis.id}", type="primary"):
                        analysis.draft_email_body = edited_body
                        analysis.email_status = "approved"
                        session.commit()
                        st.rerun()

                with btn_col2:
                    if st.button("📬 Approve & Send", key=f"send_{analysis.id}"):
                        analysis.draft_email_body = edited_body
                        analysis.email_status = "sent"
                        session.commit()
                        st.rerun()

                with btn_col3:
                    if st.button("❌ Reject", key=f"reject_{analysis.id}"):
                        analysis.email_status = "rejected"
                        session.commit()
                        st.rerun()

            elif analysis.email_status == "approved":
                if st.button("📬 Send Now", key=f"send_approved_{analysis.id}", type="primary"):
                    analysis.email_status = "sent"
                    session.commit()
                    st.rerun()

    session.close()


# ============================================================
#  PAGE ROUTER
# ============================================================
if page == "Dashboard":
    render_dashboard()
elif page == "Reviews":
    render_reviews()
elif page == "Email Queue":
    render_email_queue()
