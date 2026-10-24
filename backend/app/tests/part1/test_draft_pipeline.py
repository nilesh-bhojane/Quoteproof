from decimal import Decimal
import pytest
from app.services.draft_service import draft_from_text, recheck_quote


def test_draft_pipeline_with_sample_inquiry():
    # Inquiry with 500 regular boxes (in stock) and PII
    inquiry = "Need 500 boxes 12x10x8, 3-ply. Delivery to Pune. Call Rajesh at +91 9876543210."
    draft = draft_from_text(inquiry, mode="basic")

    # 1. PII Masking checked
    assert "+91 9876543210" not in draft.inquiry_masked
    assert "[PHONE_" in draft.inquiry_masked

    # 2. Extracted and Matched item
    assert len(draft.items) >= 1
    box_item = draft.items[0]
    assert "boxes" in box_item.description.lower()
    assert box_item.qty == Decimal("500")

    # 3. Pricing applied bulk tier (>= 500 is Rs 22.00)
    assert box_item.unit_price_snapshot == Decimal("22.00")
    assert box_item.line_total == Decimal("11000.00")
    assert "Bulk tier applied" in box_item.explain_text

    # 4. Stock checked (5000 in stock -> ok)
    assert box_item.stock_status == "ok"

    # 5. Totals calculated in Decimal with 18% GST
    # Subtotal 11,000 + GST 1,980 = Total 12,980
    assert draft.subtotal == Decimal("11000.00")
    assert draft.gst == Decimal("1980.00")
    assert draft.total == Decimal("12980.00")
    assert isinstance(draft.total, Decimal)


def test_draft_pipeline_detects_stock_shortage():
    # 500 heavy duty 5-ply cartons (only 120 in stock in fallback catalog)
    inquiry = "Need 500 5-ply box cartons urgently."
    draft = draft_from_text(inquiry, mode="basic")

    assert len(draft.items) >= 1
    short_item = draft.items[0]
    assert short_item.stock_status == "short"
    assert short_item.available_stock == 120
    assert short_item.decision_required is True

    # Critical flag blocks approval
    assert any(f["code"] == "STOCK_SHORT" and f["blocks_approval"] for f in draft.blocking_flags)
    assert draft.can_approve is False


def test_draft_pipeline_unknown_product():
    # Product not in catalog
    inquiry = "Need 50 steel shipping containers."
    draft = draft_from_text(inquiry, mode="basic")

    assert len(draft.items) >= 1
    unknown_item = draft.items[0]
    assert unknown_item.stock_status == "unknown"
    assert unknown_item.unit_price_snapshot is None
    assert any(f["code"] == "UNKNOWN_PRODUCT" and f["blocks_approval"] for f in draft.blocking_flags)
    assert draft.can_approve is False
