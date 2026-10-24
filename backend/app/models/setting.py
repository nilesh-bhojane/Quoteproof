from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Numeric, Boolean, DateTime
from app.db.session import Base


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    hourly_rate = Column(Numeric(12, 2), nullable=False, default=300.00)
    stale_days = Column(Integer, nullable=False, default=30)
    gst_pct = Column(Numeric(5, 2), nullable=False, default=18.00)
    basic_mode = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
