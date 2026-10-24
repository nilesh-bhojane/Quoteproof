import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from app.db.session import Base, GUID


class AiUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    quote_id = Column(GUID, ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True, index=True)
    tokens_in = Column(Integer, nullable=False, default=0)
    tokens_out = Column(Integer, nullable=False, default=0)
    cost_inr = Column(Numeric(12, 2), nullable=False, default=0.00)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
