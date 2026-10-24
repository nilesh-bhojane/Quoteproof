from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExtractedItem(BaseModel):
    description: str = Field(..., description="Customer's description of the product or item")
    quantity: Optional[Decimal] = Field(None, description="Extracted numerical quantity")
    unit: str = Field(default="pcs", description="Packaging unit: pcs, roll, box, kg, etc.")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Dimensions, ply, color, GSM, etc.")


class InquiryExtractionResult(BaseModel):
    items: List[ExtractedItem] = Field(default_factory=list, description="Extracted line items")
    delivery_needs: Optional[str] = Field(None, description="Location, delivery urgency, or dispatch date")
    missing_fields: List[str] = Field(default_factory=list, description="Information gaps requiring owner review")
    warnings: List[str] = Field(default_factory=list, description="Ambiguity notices or fallback warnings")
    prompt_injection_detected: bool = Field(default=False, description="Whether untrusted instructions were found")
    mode: str = Field(default="gemini", description="Extraction mode: gemini or basic_fallback")
    tokens_in: int = Field(default=0, description="Input tokens used")
    tokens_out: int = Field(default=0, description="Output tokens used")
    cost_inr: Decimal = Field(default=Decimal("0.00"), description="Estimated Gemini cost in INR")
