import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class Timing(Base):
    __tablename__ = "timings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=True, index=True)
    kind = Column(String, nullable=False)  # manual, assisted
    seconds = Column(Numeric(10, 2), nullable=False)
    at = Column(DateTime(timezone=True), nullable=False, default=func.now())
