from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.quote import Quote, QuoteItem
from app.schemas.draft import DraftCreateRequest, QuoteDraftResponse, QuoteItemDraft, StockDecisionRequest
from app.schemas.quote_update import QuoteUpdateRequest
from app.services.draft_service import draft_from_text, apply_stock_decision, recheck_quote
from app.services.pricing_service import calculate_quotation_totals, calculate_line_item
from app.services.evidence_service import log_event

router = APIRouter(prefix="/quotes", tags=["quotes"])


class StockDecisionPayload(BaseModel):
    item_id: UUID = Field(..., description="Target line item UUID")
    decision: str = Field(..., description="'partial', 'backorder', 'alternative', or 'decline'")
    qty: Optional[Decimal] = Field(None, description="Adjusted quantity")
    alternative_product_id: Optional[UUID] = Field(None, description="Product UUID if alternative selected")
    note: Optional[str] = Field(None, description="Delivery note or backorder reason")


def _format_quote_response(quote: Quote) -> Dict[str, Any]:
    """Format SQLAlchemy Quote model for JSON response."""
    items_out = []
    blocking_flags = []
    warning_flags = []

    for it in quote.items:
        for f in it.flags or []:
            if f.get("blocks_approval"):
                blocking_flags.append(f)
            else:
                warning_flags.append(f)

        items_out.append({
            "id": it.id,
            "product_id": it.product_id,
            "raw_text": it.raw_text,
            "qty": it.qty,
            "unit": it.unit,
            "unit_price_snapshot": it.unit_price_snapshot,
            "line_total": it.line_total,
            "stock_status": it.stock_status,
            "flags": it.flags or [],
            "explain_text": it.explain_text,
            "final": it.final or {},
        })

    can_approve = len(blocking_flags) == 0 and len(items_out) > 0 and quote.status == "draft"

    return {
        "id": quote.id,
        "status": quote.status,
        "inquiry_masked": quote.inquiry_masked,
        "subtotal": quote.subtotal,
        "gst": quote.gst,
        "total": quote.total,
        "approved_by": quote.approved_by,
        "approved_at": quote.approved_at,
        "created_at": quote.created_at,
        "items": items_out,
        "blocking_flags": blocking_flags,
        "warning_flags": warning_flags,
        "can_approve": can_approve,
    }


@router.post("/draft", response_model=QuoteDraftResponse)
def create_draft(request: DraftCreateRequest, db: Session = Depends(get_db)):
    """POST /api/v1/quotes/draft - Create checked draft from raw customer inquiry."""
    result = draft_from_text(
        inquiry_text=request.inquiry_text,
        mode=request.mode,
        db=db,
    )
    return result


@router.get("/{quote_id}")
def get_quote_detail(quote_id: UUID, db: Session = Depends(get_db)):
    """GET /api/v1/quotes/{id} - Retrieve quotation details, line items, and flags."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "QUOTE_NOT_FOUND", "message": f"Quote {quote_id} not found."},
        )
    return _format_quote_response(quote)


@router.patch("/{quote_id}")
def update_quote_items(quote_id: UUID, request: QuoteUpdateRequest, db: Session = Depends(get_db)):
    """PATCH /api/v1/quotes/{id} - Edit items/qty/discount; recalculates in Decimal."""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "QUOTE_NOT_FOUND", "message": f"Quote {quote_id} not found."},
        )

    # Approved quotes are immutable (CONTEXT.md section 6)
    if quote.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "IMMUTABLE_APPROVED_QUOTE",
                "message": "Approved quotes are read-only and cannot be modified.",
            },
        )

    before_state = {
        "subtotal": float(quote.subtotal),
        "total": float(quote.total),
        "items_count": len(quote.items),
    }

    # Process item edits
    if request.items:
        items_by_id = {it.id: it for it in quote.items}
        for item_edit in request.items:
            db_item = items_by_id.get(item_edit.item_id)
            if not db_item:
                continue

            if item_edit.qty is not None and item_edit.qty > 0:
                db_item.qty = item_edit.qty

            if item_edit.unit_price_snapshot is not None:
                db_item.unit_price_snapshot = item_edit.unit_price_snapshot
                # Check margin guardrail if price lowered
                if db_item.product and db_item.product.cost_price:
                    cost = db_item.product.cost_price
                    margin_pct = ((db_item.unit_price_snapshot - cost) / db_item.unit_price_snapshot * 100)
                    min_margin = db_item.product.min_margin_pct or Decimal("15.00")
                    if margin_pct < min_margin:
                        flag = {
                            "code": "LOW_MARGIN",
                            "severity": "blocking",
                            "message": f"Margin {margin_pct:.1f}% is below required {min_margin}%.",
                            "blocks_approval": True,
                        }
                        existing = [f for f in (db_item.flags or []) if f.get("code") != "LOW_MARGIN"]
                        existing.append(flag)
                        db_item.flags = existing

            # Recompute line total strictly in Decimal
            if db_item.unit_price_snapshot is not None:
                db_item.line_total = (db_item.qty * db_item.unit_price_snapshot).quantize(Decimal("0.01"))
            db_item.final = {"qty": float(db_item.qty), "unit_price": float(db_item.unit_price_snapshot or 0)}

    # Recalculate quotation totals in Decimal
    lines = [{"line_total": it.line_total} for it in quote.items]
    new_totals = calculate_quotation_totals(lines)
    quote.subtotal = new_totals["subtotal"]
    quote.gst = new_totals["gst"]
    quote.total = new_totals["total"]

    # Log human revision event
    log_event(
        action="quote_edited",
        actor="human",
        quote_id=quote.id,
        before=before_state,
        after={"subtotal": float(quote.subtotal), "total": float(quote.total)},
        db=db,
    )

    db.commit()
    db.refresh(quote)
    return _format_quote_response(quote)


@router.post("/{quote_id}/stock-decision")
def record_stock_decision(quote_id: UUID, payload: StockDecisionPayload, db: Session = Depends(get_db)):
    """POST /api/v1/quotes/{id}/stock-decision - Owner choice on short stock."""
    try:
        decision_req = StockDecisionRequest(
            decision=payload.decision,
            qty=payload.qty,
            alternative_product_id=payload.alternative_product_id,
            note=payload.note,
        )
        updated_quote = apply_stock_decision(
            quote_id=quote_id,
            item_id=payload.item_id,
            decision_req=decision_req,
            db=db,
        )
        return _format_quote_response(updated_quote)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": str(e)},
        )
