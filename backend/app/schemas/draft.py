from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class DraftCreateRequest(BaseModel):
    inquiry_text: str = Field(..., min_length=3, max_length=15000, description="Raw customer inquiry text")
    mode: str = Field(default="gemini", description="Extraction mode: 'gemini' or 'basic'")


class StockDecisionRequest(BaseModel):
    decision: str = Field(
        ...,
        description="One of: 'partial' (quote available qty), 'backorder' (accept with delivery date), 'alternative' (switch product), or 'decline' (decline item)",
    )
    qty: Optional[Decimal] = Field(None, description="Adjusted quantity for partial or backorder")
    alternative_product_id: Optional[UUID] = Field(None, description="New product UUID if alternative chosen")
    note: Optional[str] = Field(None, description="Note on expected backorder date or reason")


class QuoteItemDraft(BaseModel):
    id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    raw_text: str
    description: str
    qty: Decimal
    unit: str
    unit_price_snapshot: Optional[Decimal] = None
    line_total: Decimal
    stock_status: str
    available_stock: Optional[int] = None
    flags: List[Dict[str, Any]] = []
    explain_text: Optional[str] = None
    decision_required: bool = False
    copyable_reply: Optional[str] = None


class QuoteDraftResponse(BaseModel):
    id: Optional[UUID] = None
    status: str = "draft"
    inquiry_masked: str
    items: List[QuoteItemDraft] = []
    subtotal: Decimal
    gst_rate_pct: Decimal = Decimal("18.00")
    gst: Decimal
    total: Decimal
    blocking_flags: List[Dict[str, Any]] = []
    warning_flags: List[Dict[str, Any]] = []
    can_approve: bool = False
    mode_used: str = "gemini"
    tokens_in: int = 0
    tokens_out: int = 0
    cost_inr: Decimal = Decimal("0.00")
