import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from app.db.session import Base, GUID


class Timing(Base):
    __tablename__ = "timings"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    quote_id = Column(GUID, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=True, index=True)
    kind = Column(String, nullable=False)  # manual, assisted
    seconds = Column(Numeric(10, 2), nullable=False)
    at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
