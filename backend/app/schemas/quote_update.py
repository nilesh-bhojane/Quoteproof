from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class QuoteItemUpdate(BaseModel):
    item_id: UUID
    qty: Optional[Decimal] = Field(None, gt=0, description="New quantity")
    unit_price_snapshot: Optional[Decimal] = Field(None, ge=0, description="Override unit price in INR")


class QuoteUpdateRequest(BaseModel):
    items: Optional[List[QuoteItemUpdate]] = Field(None, description="Updated item list")
    discount_pct: Optional[Decimal] = Field(None, ge=0, le=100, description="Overall quotation discount percentage")
