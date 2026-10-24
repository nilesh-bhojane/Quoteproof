from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any, Optional
from app.services.extraction import extract_inquiry
from app.services.quotation import validate_quote
from app.services.analytics import record_event, get_events, calculate_roi, summary

router = APIRouter()


class ExtractRequest(BaseModel):
    inquiry_text: str = Field(min_length=1, max_length=12000)


class QuoteRequest(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    tax_rate: float = Field(default=0.0, ge=0, le=100)


class EventRequest(BaseModel):
    quote_id: str = Field(default="demo-1")
    event_type: str
    details: dict[str, Any] = Field(default_factory=dict)


class RoiRequest(BaseModel):
    manual_seconds: Optional[float] = None
    assisted_seconds: Optional[float] = None
    hourly_labour_cost: Optional[float] = None


@router.post("/extract")
def extract(request: ExtractRequest):
    return extract_inquiry(request.inquiry_text)


@router.post("/quotes/validate")
def validate(request: QuoteRequest):
    return validate_quote(request.items, request.tax_rate)


@router.post("/events")
def create_event(request: EventRequest):
    event = record_event(request.quote_id, request.event_type, request.details)
    return {"ok": True, "persisted": True, "event": event}


@router.get("/events")
def list_events(quote_id: Optional[str] = None):
    return {"events": get_events(quote_id)}


@router.post("/analytics/calculate")
def calc_roi(request: RoiRequest):
    return calculate_roi(request.manual_seconds, request.assisted_seconds, request.hourly_labour_cost)


@router.get("/analytics/summary")
def analytics_summary():
    return summary()
