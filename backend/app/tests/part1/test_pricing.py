from decimal import Decimal
import pytest
from app.services.pricing_service import (
    calculate_line_item,
    calculate_quotation_totals,
    resolve_unit_price,
    round_half_up,
)

SAMPLE_PRODUCT = {
    "id": "00000000-0000-0000-0000-000000000001",
    "name": "Corrugated Box 12x10x8 (3-Ply)",
    "sell_price": Decimal("24.00"),
    "cost_price": Decimal("18.00"),
    "min_margin_pct": Decimal("15.00"),
    "unit": "pcs",
    "bulk_tiers": [
        {"min_qty": 500, "unit_price": Decimal("22.00")},
        {"min_qty": 2000, "unit_price": Decimal("20.00")},
    ],
}


def test_standard_pricing_no_tier():
    # 100 boxes -> standard rate Rs 24.00
    item = calculate_line_item(Decimal("100"), SAMPLE_PRODUCT)
    assert item["unit_price_snapshot"] == Decimal("24.00")
    assert item["line_total"] == Decimal("2400.00")
    assert "Standard catalogue rate" in item["explain_text"]
    assert len(item["flags"]) == 0


def test_bulk_tier_pricing():
    # 500 boxes -> tier rate Rs 22.00
    item = calculate_line_item(Decimal("500"), SAMPLE_PRODUCT)
    assert item["unit_price_snapshot"] == Decimal("22.00")
    assert item["line_total"] == Decimal("11000.00")
    assert "Bulk tier applied for ≥ 500" in item["explain_text"]


def test_highest_bulk_tier_pricing():
    # 2500 boxes -> tier rate Rs 20.00
    item = calculate_line_item(Decimal("2500"), SAMPLE_PRODUCT)
    assert item["unit_price_snapshot"] == Decimal("20.00")
    assert item["line_total"] == Decimal("50000.00")
    assert "Bulk tier applied for ≥ 2000" in item["explain_text"]


def test_margin_guardrail_blocking_flag():
    # Selling below cost price triggers LOW_MARGIN blocking flag
    low_price_product = {
        "id": "p2",
        "name": "Custom Carton",
        "sell_price": Decimal("20.00"),
        "cost_price": Decimal("19.00"),  # cost 19, margin is 5% < min 15%
        "min_margin_pct": Decimal("15.00"),
        "unit": "pcs",
        "bulk_tiers": [],
    }
    item = calculate_line_item(Decimal("100"), low_price_product)
    assert any(f["code"] == "LOW_MARGIN" and f["blocks_approval"] for f in item["flags"])


def test_round_half_up_exactness():
    # Ensure standard banker's round is NOT used (0.005 must round UP to 0.01)
    assert round_half_up(Decimal("12.345")) == Decimal("12.35")
    assert round_half_up(Decimal("12.344")) == Decimal("12.34")


def test_quotation_totals_gst_18():
    items = [
        {"line_total": Decimal("11000.00")},
        {"line_total": Decimal("22000.00")},
    ]
    totals = calculate_quotation_totals(items, gst_rate_pct=Decimal("18.00"))
    assert totals["subtotal"] == Decimal("33000.00")
    # 33000 * 0.18 = 5940.00
    assert totals["gst"] == Decimal("5940.00")
    assert totals["total"] == Decimal("38940.00")
    # Ensure type is strictly Decimal
    assert isinstance(totals["total"], Decimal)
