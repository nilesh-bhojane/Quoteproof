"""Draft Quotation Pipeline Orchestrator and Person B Handshakes.

Per CONTEXT.md Section 3, 4, 8 & 9:
- Handshake 1: A's draft creates quotes and quote_items rows with price snapshots; B reads them.
- Handshake 2: evidence_service.log_event records traceable events.
- Handshake 3: draft_service.recheck_quote(quote_id) returns blocking flags & stock status.
- Handshake 4: draft_service.draft_from_text(text, mode) for interactive drafts & trust tests.
- Handshake 6: Writes ai_usage rows for Person B's cost-per-quote meter.
"""

import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.quote import Quote, QuoteItem
from app.models.product import Product
from app.models.ai_usage import AiUsage
from app.schemas.draft import QuoteDraftResponse, QuoteItemDraft, StockDecisionRequest
from app.services.masking_service import mask_pii
from app.services.gemini_service import extract_inquiry_with_ai
from app.services.product_matching_service import match_product
from app.services.stock_service import check_item_stock
from app.services.pricing_service import calculate_line_item, calculate_quotation_totals
from app.services.evidence_service import log_event

# In-memory catalogue fallback if database session is not passed (for pure unit tests)
FALLBACK_CATALOG = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Corrugated Box 12x10x8 (3-Ply)",
        "aliases": ["box 12x10x8", "carton 12x10x8", "standard shipping box", "3-ply box"],
        "unit": "pcs",
        "sell_price": Decimal("24.00"),
        "cost_price": Decimal("18.00"),
        "min_margin_pct": Decimal("15.00"),
        "bulk_tiers": [{"min_qty": 500, "unit_price": Decimal("22.00")}, {"min_qty": 2000, "unit_price": Decimal("20.00")}],
        "stock_on_hand": 5000,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": None,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Heavy Duty Box 18x14x12 (5-Ply)",
        "aliases": ["5-ply box", "heavy duty carton", "box 18x14x12", "large box"],
        "unit": "pcs",
        "sell_price": Decimal("48.00"),
        "cost_price": Decimal("36.00"),
        "min_margin_pct": Decimal("20.00"),
        "bulk_tiers": [{"min_qty": 200, "unit_price": Decimal("44.00")}],
        "stock_on_hand": 120,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": None,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "name": "Die-Cut Mailer Box 10x8x3 (White E-Flute)",
        "aliases": ["white mailer", "mailer box", "e-commerce box", "die cut box"],
        "unit": "pcs",
        "sell_price": Decimal("32.00"),
        "cost_price": Decimal("24.00"),
        "min_margin_pct": Decimal("20.00"),
        "bulk_tiers": [],
        "stock_on_hand": 0,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": None,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
        "name": "Air Bubble Roll 100m x 1m (50 GSM)",
        "aliases": ["bubble wrap", "bubble roll", "air bubble packaging"],
        "unit": "roll",
        "sell_price": Decimal("850.00"),
        "cost_price": Decimal("680.00"),
        "min_margin_pct": Decimal("15.00"),
        "bulk_tiers": [{"min_qty": 10, "unit_price": Decimal("800.00")}],
        "stock_on_hand": 80,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": None,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000005"),
        "name": "Custom Brand Logo Printing (1-Color Screen)",
        "aliases": ["logo printing", "screen print", "brand printing"],
        "unit": "job",
        "sell_price": Decimal("1200.00"),
        "cost_price": Decimal("600.00"),
        "min_margin_pct": Decimal("40.00"),
        "bulk_tiers": [],
        "stock_on_hand": 0,
        "reserved": 0,
        "track_stock": False,
        "price_updated_at": None,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000006"),
        "name": "BOPP Brown Packaging Tape (48mm x 65m)",
        "aliases": ["brown tape", "bopp tape", "packing tape", "carton tape"],
        "unit": "roll",
        "sell_price": Decimal("65.00"),
        "cost_price": Decimal("48.00"),
        "min_margin_pct": Decimal("20.00"),
        "bulk_tiers": [{"min_qty": 72, "unit_price": Decimal("58.00")}],
        "stock_on_hand": 600,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": None,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000007"),
        "name": "Manual Stretch Film Roll (4kg, 23 Micron)",
        "aliases": ["stretch film", "pallet wrap", "cling film packaging"],
        "unit": "roll",
        "sell_price": Decimal("620.00"),
        "cost_price": Decimal("510.00"),
        "min_margin_pct": Decimal("15.00"),
        "bulk_tiers": [{"min_qty": 20, "unit_price": Decimal("580.00")}],
        "stock_on_hand": 150,
        "reserved": 10,
        "track_stock": True,
        "price_updated_at": None,
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000008"),
        "name": "Corrugated Partition Dividers 12x10",
        "aliases": ["partition", "box divider", "separator sheet"],
        "unit": "pcs",
        "sell_price": Decimal("8.50"),
        "cost_price": Decimal("6.00"),
        "min_margin_pct": Decimal("25.00"),
        "bulk_tiers": [{"min_qty": 1000, "unit_price": Decimal("7.50")}],
        "stock_on_hand": 2500,
        "reserved": 0,
        "track_stock": True,
        "price_updated_at": None,
    },
]


def _product_to_dict(p: Any) -> Dict[str, Any]:
    """Normalize SQLAlchemy Product or dict to standard dictionary."""
    if isinstance(p, dict):
        return p
    return {
        "id": p.id,
        "name": p.name,
        "aliases": p.aliases or [],
        "unit": p.unit or "pcs",
        "sell_price": Decimal(str(p.sell_price)),
        "cost_price": Decimal(str(p.cost_price)),
        "min_margin_pct": Decimal(str(p.min_margin_pct or 15.00)),
        "bulk_tiers": p.bulk_tiers or [],
        "stock_on_hand": p.stock_on_hand or 0,
        "reserved": p.reserved or 0,
        "track_stock": p.track_stock,
        "price_updated_at": p.price_updated_at,
    }


def draft_from_text(
    inquiry_text: str,
    mode: str = "gemini",
    db: Optional[Session] = None,
    client: Optional[object] = None,
) -> QuoteDraftResponse:
    """Full pipeline: Masking -> Extraction -> Matching -> Stock -> Pricing -> Validation.

    Handshake #4: Used by interactive UI and Trust Scorecard runner.
    """
    # 1. Mask PII before any AI call
    masked_text, pii_mapping = mask_pii(inquiry_text)

    # 2. Extract line items
    force_basic = (mode == "basic")
    extraction = extract_inquiry_with_ai(masked_text, force_basic_mode=force_basic, client=client)

    # 3. Fetch catalogue products
    if db is not None:
        db_prods = db.query(Product).all()
        catalog = [_product_to_dict(p) for p in db_prods]
    else:
        catalog = FALLBACK_CATALOG

    draft_items: List[QuoteItemDraft] = []
    line_totals_for_calc = []
    all_blocking_flags = []
    all_warning_flags = []

    # 4. Process each extracted line item
    for item in extraction.items:
        item_flags = []

        # Check for missing quantity
        if item.quantity is None or item.quantity <= Decimal("0"):
            item_flags.append({
                "code": "MISSING_QUANTITY",
                "severity": "blocking",
                "message": f"Quantity is missing for item '{item.description}'.",
                "suggested_action": "Specify an integer quantity before approval.",
                "blocks_approval": True,
            })
            qty = Decimal("1.00")
        else:
            qty = item.quantity

        # Match to catalogue
        match_res = match_product(item.description, catalog, item.specifications)
        matched_prod = match_res.get("product")
        item_flags.extend(match_res.get("flags", []))

        if matched_prod:
            # Check Stock
            stock_res = check_item_stock(matched_prod, qty)
            stock_status = stock_res["stock_status"]
            available = stock_res["available"]
            decision_req = stock_res["decision_required"]
            copyable_reply = stock_res["copyable_reply"]
            item_flags.extend(stock_res.get("flags", []))

            # Calculate Pricing in Python Decimal
            pricing_res = calculate_line_item(qty, matched_prod)
            unit_price = pricing_res["unit_price_snapshot"]
            line_total = pricing_res["line_total"]
            explain_text = pricing_res["explain_text"]
            item_flags.extend(pricing_res.get("flags", []))
            prod_id = matched_prod["id"]
        else:
            stock_status = "unknown"
            available = None
            decision_req = False
            copyable_reply = None
            unit_price = None
            line_total = Decimal("0.00")
            explain_text = "Item could not be priced because it was not found in the price list."
            prod_id = None

        line_totals_for_calc.append({"line_total": line_total})

        # Segregate flags
        for f in item_flags:
            if f.get("blocks_approval"):
                all_blocking_flags.append(f)
            else:
                all_warning_flags.append(f)

        draft_items.append(
            QuoteItemDraft(
                id=uuid.uuid4(),
                product_id=prod_id,
                raw_text=item.description,
                description=item.description,
                qty=qty,
                unit=item.unit or "pcs",
                unit_price_snapshot=unit_price,
                line_total=line_total,
                stock_status=stock_status,
                available_stock=available,
                flags=item_flags,
                explain_text=explain_text,
                decision_required=decision_req,
                copyable_reply=copyable_reply,
            )
        )

    # 5. Calculate overall Quotation Totals
    totals = calculate_quotation_totals(line_totals_for_calc)
    subtotal = totals["subtotal"]
    gst = totals["gst"]
    total = totals["total"]

    # Incorporate extraction level warnings/flags
    if extraction.prompt_injection_detected:
        all_warning_flags.append({
            "code": "PROMPT_INJECTION_DETECTED",
            "severity": "warning",
            "message": "Prompt injection detected in inquiry text; instructions ignored.",
            "suggested_action": "Review inquiry text manually.",
            "blocks_approval": False,
        })

    can_approve = (len(all_blocking_flags) == 0) and (len(draft_items) > 0)
    quote_id = uuid.uuid4()

    # 6. Persist to Database if DB session is active (Handshake #1 & #6)
    if db is not None:
        try:
            db_quote = Quote(
                id=quote_id,
                status="draft",
                inquiry_masked=masked_text,
                subtotal=subtotal,
                gst=gst,
                total=total,
            )
            db.add(db_quote)
            db.flush()

            for it in draft_items:
                db_item = QuoteItem(
                    id=it.id,
                    quote_id=quote_id,
                    product_id=it.product_id,
                    raw_text=it.raw_text,
                    qty=it.qty,
                    unit=it.unit,
                    unit_price_snapshot=it.unit_price_snapshot,
                    line_total=it.line_total,
                    ai_proposed={"qty": float(it.qty), "description": it.description},
                    final={"qty": float(it.qty), "unit_price": float(it.unit_price_snapshot or 0)},
                    flags=it.flags,
                    stock_status=it.stock_status,
                    explain_text=it.explain_text,
                )
                db.add(db_item)

            # Record AI Usage (Handshake #6)
            if extraction.tokens_in > 0 or extraction.tokens_out > 0:
                ai_log = AiUsage(
                    id=uuid.uuid4(),
                    quote_id=quote_id,
                    tokens_in=extraction.tokens_in,
                    tokens_out=extraction.tokens_out,
                    cost_inr=extraction.cost_inr,
                )
                db.add(ai_log)

            # Log Audit Trail Event (Handshake #2)
            log_event(
                action="draft_extracted",
                actor="ai" if extraction.mode == "gemini" else "system",
                quote_id=quote_id,
                after={"items_count": len(draft_items), "total": float(total)},
                db=db,
            )

            db.commit()
        except Exception:
            db.rollback()

    return QuoteDraftResponse(
        id=quote_id,
        status="draft",
        inquiry_masked=masked_text,
        items=draft_items,
        subtotal=subtotal,
        gst_rate_pct=totals["gst_rate_pct"],
        gst=gst,
        total=total,
        blocking_flags=all_blocking_flags,
        warning_flags=all_warning_flags,
        can_approve=can_approve,
        mode_used=extraction.mode,
        tokens_in=extraction.tokens_in,
        tokens_out=extraction.tokens_out,
        cost_inr=extraction.cost_inr,
    )


def recheck_quote(quote_id: Any, db: Session) -> Dict[str, Any]:
    """Re-evaluate an existing quote's stock and pricing before approval.

    Handshake #3: Person B's /approve route calls this.
    Refuses approval if any blocking flags remain.
    """
    quote = db.query(Quote).filter(Quote.id == uuid.UUID(str(quote_id))).first()
    if not quote:
        return {
            "can_approve": False,
            "blocking_flags": [{"code": "QUOTE_NOT_FOUND", "message": "Quotation does not exist."}],
            "all_flags": [],
            "stock_status": "error",
        }

    blocking_flags = []
    all_flags = []
    overall_stock = "ok"

    for it in quote.items:
        # Check if item has unlinked product
        if not it.product_id:
            flag = {
                "code": "UNKNOWN_PRODUCT",
                "severity": "blocking",
                "message": f"Item '{it.raw_text}' has no product linked from the catalogue.",
                "blocks_approval": True,
            }
            blocking_flags.append(flag)
            all_flags.append(flag)
            continue

        # Check current product stock
        prod = it.product
        is_backorder_confirmed = (it.final or {}).get("decision") == "backorder"
        if prod and prod.track_stock and not is_backorder_confirmed:
            available = max(0, (prod.stock_on_hand or 0) - (prod.reserved or 0))
            if available < int(it.qty):
                code = "OUT_OF_STOCK" if available <= 0 else "STOCK_SHORT"
                flag = {
                    "code": code,
                    "severity": "blocking",
                    "message": f"Stock check failed for '{prod.name}': only {available} available for requested {it.qty}.",
                    "blocks_approval": True,
                }
                blocking_flags.append(flag)
                all_flags.append(flag)
                overall_stock = "short" if available > 0 else "out_of_stock"

        # Check existing item flags
        for f in it.flags or []:
            all_flags.append(f)
            if f.get("blocks_approval") and f not in blocking_flags:
                blocking_flags.append(f)

    can_approve = len(blocking_flags) == 0
    return {
        "can_approve": can_approve,
        "blocking_flags": blocking_flags,
        "all_flags": all_flags,
        "stock_status": overall_stock,
    }


def apply_stock_decision(
    quote_id: Any,
    item_id: Any,
    decision_req: StockDecisionRequest,
    db: Session,
) -> Quote:
    """Apply an owner's decision on a short-stock line item.

    Decisions:
    - 'partial': Update item quantity to available quantity.
    - 'backorder': Accept full quantity with an explicit delivery date note.
    - 'alternative': Switch product to alternative_product_id.
    - 'decline': Set quantity and line total to 0, mark declined.
    """
    quote = db.query(Quote).filter(Quote.id == uuid.UUID(str(quote_id))).first()
    if not quote:
        raise ValueError(f"Quote {quote_id} not found.")

    item = db.query(QuoteItem).filter(QuoteItem.id == uuid.UUID(str(item_id))).first()
    if not item:
        raise ValueError(f"Quote item {item_id} not found.")

    before_state = {"qty": float(item.qty), "line_total": float(item.line_total)}

    if decision_req.decision == "partial":
        if decision_req.qty is not None and decision_req.qty > 0:
            item.qty = decision_req.qty
        item.stock_status = "ok"
        item.final = {"decision": "partial", "qty": float(item.qty), "note": decision_req.note}
        item.explain_text = (item.explain_text or "") + f" [Owner confirmed partial quote: {item.qty} {item.unit}]."
        # Recalculate line total
        if item.unit_price_snapshot:
            item.line_total = (item.qty * item.unit_price_snapshot).quantize(Decimal("0.01"))

    elif decision_req.decision == "backorder":
        item.stock_status = "short"
        item.final = {"decision": "backorder", "qty": float(item.qty), "note": decision_req.note}
        item.explain_text = (item.explain_text or "") + f" [Owner confirmed backorder: {decision_req.note or 'Standard lead time'}]."

    elif decision_req.decision == "alternative":
        if decision_req.alternative_product_id:
            alt_prod = db.query(Product).filter(Product.id == decision_req.alternative_product_id).first()
            if alt_prod:
                item.product_id = alt_prod.id
                item.unit_price_snapshot = alt_prod.sell_price
                item.stock_status = "ok"
                item.final = {"decision": "alternative", "product_id": str(alt_prod.id), "name": alt_prod.name}
                item.explain_text = f"Switched to alternative product: {alt_prod.name} at ₹{alt_prod.sell_price}/{alt_prod.unit}."
                item.line_total = (item.qty * item.unit_price_snapshot).quantize(Decimal("0.01"))

    elif decision_req.decision == "decline":
        item.stock_status = "out_of_stock"
        item.final = {"decision": "decline", "note": decision_req.note}
        item.qty = Decimal("0.00")
        item.line_total = Decimal("0.00")
        item.explain_text = "Item declined due to inventory shortage."

    # Clear blocking stock flags on this item
    item.flags = [f for f in (item.flags or []) if f.get("code") not in ("STOCK_SHORT", "OUT_OF_STOCK")]

    # Recalculate quote totals
    all_lines = [{"line_total": it.line_total} for it in quote.items]
    new_totals = calculate_quotation_totals(all_lines)
    quote.subtotal = new_totals["subtotal"]
    quote.gst = new_totals["gst"]
    quote.total = new_totals["total"]

    log_event(
        action="stock_decision_applied",
        actor="human",
        quote_id=quote.id,
        before=before_state,
        after={"decision": decision_req.decision, "new_total": float(quote.total)},
        db=db,
    )

    db.commit()
    db.refresh(quote)
    return quote
