import uuid
from sqlalchemy import Column, String, Numeric, Integer, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.types import JSON
from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    aliases = Column(ARRAY(String), nullable=False, default=list)
    unit = Column(String, nullable=False, default="pcs")
    sell_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)
    min_margin_pct = Column(Numeric(5, 2), nullable=False, default=15.00)
    bulk_tiers = Column(JSONB, nullable=False, default=list)
    stock_on_hand = Column(Integer, nullable=False, default=0)
    reserved = Column(Integer, nullable=False, default=0)
    track_stock = Column(Boolean, nullable=False, default=True)
    price_updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    @property
    def available_stock(self) -> int:
        return max(0, (self.stock_on_hand or 0) - (self.reserved or 0))
