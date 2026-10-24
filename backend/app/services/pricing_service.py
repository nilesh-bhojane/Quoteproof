"""Deterministic Pricing Service using Python Decimal.

Per CONTEXT.md Section 2, 7 & 8:
- AI NEVER decides a price, discount, tax, or total. All numbers come from DB / code.
- Python Decimal only, NEVER float.
- Rule: each line = qty * unit_price - discount, rounded to 2 places (ROUND_HALF_UP).
- GST (default 18%) is calculated on discounted subtotal and rounded once.
- Generates "Why this price?" explanation per line item (in code, not AI).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional

TWO_PLACES = Decimal("0.01")


def round_half_up(val: Decimal) -> Decimal:
    """Round a Decimal value to 2 decimal places using ROUND_HALF_UP."""
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def resolve_unit_price(qty: Decimal, product: Dict[str, Any]) -> tuple[Decimal, str]:
    """Determine the applicable unit price based on quantity and bulk tiers.

    Returns:
        (applicable_unit_price, why_this_price_text)
    """
    base_price = Decimal(str(product["sell_price"]))
    bulk_tiers = product.get("bulk_tiers") or []

    # Sort tiers descending by min_qty to match highest applicable tier first
    sorted_tiers = sorted(
        bulk_tiers,
        key=lambda t: Decimal(str(t.get("min_qty", 0))),
        reverse=True,
    )

    for tier in sorted_tiers:
        min_qty = Decimal(str(tier.get("min_qty", 0)))
        tier_price = Decimal(str(tier.get("unit_price", base_price)))
        if qty >= min_qty:
            saving = base_price - tier_price
            explain = (
                f"Bulk tier applied for \u2265 {int(min_qty)} {product.get('unit', 'pcs')}: "
                f"\u20b9{tier_price:.2f}/{product.get('unit', 'pcs')} (saves \u20b9{saving:.2f}/{product.get('unit', 'pcs')} vs base rate)."
            )
            return tier_price, explain

    explain = f"Standard catalogue rate of \u20b9{base_price:.2f}/{product.get('unit', 'pcs')}."
    return base_price, explain


def calculate_line_item(
    qty: Decimal,
    product: Dict[str, Any],
    discount_pct: Decimal = Decimal("0.00"),
) -> Dict[str, Any]:
    """Calculate line item pricing, discount, margin check, and explanation text.

    Args:
        qty: Quantity requested.
        product: Product dict with sell_price, cost_price, min_margin_pct, bulk_tiers.
        discount_pct: Optional line discount percentage.

    Returns:
        Dict with qty, unit_price, discount_pct, line_total, margin_pct, flags, explain_text.
    """
    if qty <= Decimal("0"):
        raise ValueError("Quantity must be greater than zero.")

    unit_price, explain = resolve_unit_price(qty, product)
    raw_subtotal = qty * unit_price

    # Apply discount if specified
    discount_factor = Decimal("1.00") - (discount_pct / Decimal("100.00"))
    line_total = round_half_up(raw_subtotal * discount_factor)

    # Margin guardrail check
    cost_price = Decimal(str(product.get("cost_price", "0.00")))
    min_margin = Decimal(str(product.get("min_margin_pct", "15.00")))
    effective_unit_price = line_total / qty if qty > 0 else Decimal("0.00")

    margin_pct = Decimal("0.00")
    flags: List[Dict[str, Any]] = []

    if effective_unit_price > Decimal("0"):
        margin_pct = ((effective_unit_price - cost_price) / effective_unit_price) * Decimal("100.00")
        if margin_pct < min_margin:
            flags.append({
                "code": "LOW_MARGIN",
                "severity": "blocking",
                "message": (
                    f"Margin of {margin_pct:.1f}% is below the minimum required {min_margin:.1f}% "
                    f"(cost \u20b9{cost_price:.2f}, effective sell \u20b9{effective_unit_price:.2f})."
                ),
                "suggested_action": "Reduce discount or confirm special owner override with reason.",
                "blocks_approval": True,
            })

    if discount_pct >= Decimal("15.00"):
        flags.append({
            "code": "LARGE_DISCOUNT",
            "severity": "warning",
            "message": f"Large discount of {discount_pct:.1f}% applied.",
            "suggested_action": "Review margin impact before approval.",
            "blocks_approval": False,
        })

    return {
        "product_id": product.get("id"),
        "name": product.get("name"),
        "unit": product.get("unit", "pcs"),
        "qty": qty,
        "unit_price_snapshot": unit_price,
        "discount_pct": discount_pct,
        "line_total": line_total,
        "margin_pct": round_half_up(margin_pct),
        "flags": flags,
        "explain_text": explain,
    }


def calculate_quotation_totals(
    line_items: List[Dict[str, Any]],
    gst_rate_pct: Decimal = Decimal("18.00"),
) -> Dict[str, Decimal]:
    """Recalculate entire quotation subtotal, GST, and grand total in Decimal.

    The server always recalculates every total; frontend totals are never trusted.
    """
    subtotal = sum(
        (item["line_total"] for item in line_items),
        Decimal("0.00"),
    )
    subtotal = round_half_up(subtotal)
    gst = round_half_up(subtotal * (gst_rate_pct / Decimal("100.00")))
    grand_total = subtotal + gst

    return {
        "subtotal": subtotal,
        "gst_rate_pct": gst_rate_pct,
        "gst": gst,
        "total": grand_total,
    }
