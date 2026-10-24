import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Integer, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from app.db.session import Base, GUID


class Product(Base):
    __tablename__ = "products"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    aliases = Column(ARRAY(String).with_variant(JSON, "sqlite"), nullable=False, default=list)
    unit = Column(String, nullable=False, default="pcs")
    sell_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)
    min_margin_pct = Column(Numeric(5, 2), nullable=False, default=15.00)
    bulk_tiers = Column(JSON, nullable=False, default=list)
    stock_on_hand = Column(Integer, nullable=False, default=0)
    reserved = Column(Integer, nullable=False, default=0)
    track_stock = Column(Boolean, nullable=False, default=True)
    price_updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    @property
    def available_stock(self) -> int:
        return max(0, (self.stock_on_hand or 0) - (self.reserved or 0))
