from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    aliases: List[str] = Field(default_factory=list)
    unit: str = Field(default="pcs", min_length=1, max_length=50)
    sell_price: Decimal = Field(..., ge=0, description="Selling price in INR")
    cost_price: Decimal = Field(..., ge=0, description="Cost price in INR")
    min_margin_pct: Decimal = Field(default=Decimal("15.00"), ge=0, le=100)
    bulk_tiers: List[Dict[str, Any]] = Field(default_factory=list)
    stock_on_hand: int = Field(default=0, ge=0)
    reserved: int = Field(default=0, ge=0)
    track_stock: bool = Field(default=True)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    aliases: Optional[List[str]] = None
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    sell_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    min_margin_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    bulk_tiers: Optional[List[Dict[str, Any]]] = None
    stock_on_hand: Optional[int] = Field(None, ge=0)
    reserved: Optional[int] = Field(None, ge=0)
    track_stock: Optional[bool] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    aliases: List[str] = []
    unit: str
    sell_price: Decimal
    cost_price: Decimal
    min_margin_pct: Decimal
    bulk_tiers: List[Dict[str, Any]] = []
    stock_on_hand: int
    reserved: int
    available_stock: int
    track_stock: bool
    price_updated_at: Optional[datetime] = None
    is_stale: bool = False
    days_since_price_update: Optional[int] = None

