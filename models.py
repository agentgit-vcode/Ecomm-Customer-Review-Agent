"""SQLAlchemy ORM models — 3 tables."""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float,
    DateTime, ForeignKey
)
from sqlalchemy.orm import relationship

from database import Base


class Review(Base):
    """Customer review with embedded customer/product info."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(255), nullable=False)
    product_name = Column(String(255), nullable=False)
    product_category = Column(String(100), nullable=False)
    order_total = Column(Float, nullable=False)
    star_rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)

    # Relationship to analysis
    analysis = relationship("Analysis", back_populates="review", uselist=False)

    def __repr__(self):
        return f"<Review {self.id} by {self.customer_name} — {self.star_rating}★>"


class Analysis(Base):
    """Agent analysis result + optional draft email (merged into one table)."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), unique=True, nullable=False)

    # Classification fields
    sentiment = Column(String(20), nullable=False)       # POSITIVE, NEGATIVE, NEUTRAL
    severity = Column(String(10), nullable=True)          # HIGH, LOW (null for positive)
    action = Column(String(10), nullable=False)            # ALERT, LOG
    category = Column(String(50), nullable=True)           # shipping, quality, defective, service, pricing
    reason = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)

    # Draft email fields (only populated for ALERT reviews)
    draft_email_subject = Column(String(255), nullable=True)
    draft_email_body = Column(Text, nullable=True)
    email_status = Column(String(20), nullable=True)        # draft, approved, sent, rejected (null for non-ALERT)

    # Metadata
    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    model_used = Column(String(50), nullable=True)

    # Relationship
    review = relationship("Review", back_populates="analysis")

    def __repr__(self):
        return f"<Analysis {self.id} — {self.sentiment}/{self.action}>"


class AgentRun(Base):
    """Log of each agent processing run."""
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    reviews_processed = Column(Integer, default=0)
    alerts_generated = Column(Integer, default=0)
    status = Column(String(20), default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AgentRun {self.id} — {self.status}>"
