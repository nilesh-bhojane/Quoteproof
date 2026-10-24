import uuid
from sqlalchemy import Column, String, Numeric, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False, default="draft")  # draft, approved, rejected
    inquiry_masked = Column(Text, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0.00)
    gst = Column(Numeric(12, 2), nullable=False, default=0.00)
    total = Column(Numeric(12, 2), nullable=False, default=0.00)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    audit_events = relationship("AuditLog", back_populates="quote", cascade="all, delete-orphan")


class QuoteItem(Base):
    __tablename__ = "quote_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    raw_text = Column(Text, nullable=False)
    qty = Column(Numeric(12, 2), nullable=False, default=1.00)
    unit = Column(String, nullable=False, default="pcs")
    unit_price_snapshot = Column(Numeric(12, 2), nullable=True)
    line_total = Column(Numeric(12, 2), nullable=False, default=0.00)
    ai_proposed = Column(JSONB, nullable=False, default=dict)
    final = Column(JSONB, nullable=False, default=dict)
    flags = Column(JSONB, nullable=False, default=list)
    stock_status = Column(String, nullable=False, default="ok")  # ok, short, out_of_stock, untracked
    explain_text = Column(Text, nullable=True)

    quote = relationship("Quote", back_populates="items")
    product = relationship("Product")
