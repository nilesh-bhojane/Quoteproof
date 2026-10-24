import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base, GUID


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    correlation_id = Column(String, nullable=True)
    quote_id = Column(GUID, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=True, index=True)
    actor = Column(String, nullable=False)  # ai, human, system
    action = Column(String, nullable=False)
    before = Column(JSON, nullable=False, default=dict)
    after = Column(JSON, nullable=False, default=dict)
    at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    quote = relationship("Quote", back_populates="audit_events")
