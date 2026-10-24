from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any
from app.services.extraction import extract_inquiry
from app.services.quotation import validate_quote
from app.services.analytics import summary

router = APIRouter()

class ExtractRequest(BaseModel):
    inquiry_text: str = Field(min_length=1, max_length=12000)

class QuoteRequest(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    tax_rate: float = Field(default=0.0, ge=0, le=100)

class EventRequest(BaseModel):
    quote_id: str
    event_type: str
    details: dict[str, Any] = Field(default_factory=dict)

@router.post("/extract")
def extract(request: ExtractRequest):
    # Safe deterministic placeholder; replace with an LLM adapter and schema validation.
    return extract_inquiry(request.inquiry_text)

@router.post("/quotes/validate")
def validate(request: QuoteRequest):
    return validate_quote(request.items, request.tax_rate)

@router.post("/events")
def create_event(request: EventRequest):
    # TODO: persist this event to a database; this response does not claim persistence.
    return {"ok": True, "persisted": False, "event": request.model_dump()}

@router.get("/analytics/summary")
def analytics_summary():
    return summary()
