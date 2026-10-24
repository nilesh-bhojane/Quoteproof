import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    correlation_id = Column(String, nullable=True)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=True, index=True)
    actor = Column(String, nullable=False)  # ai, human, system
    action = Column(String, nullable=False)
    before = Column(JSONB, nullable=False, default=dict)
    after = Column(JSONB, nullable=False, default=dict)
    at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    quote = relationship("Quote", back_populates="audit_events")
