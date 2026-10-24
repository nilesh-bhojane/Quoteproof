"""Deterministic Stock Verification Service.

Per CONTEXT.md Section 5 & 6:
- Stock formula: available = stock_on_hand - reserved.
- Owner edits stock by hand; quotes do NOT auto-reserve inventory.
- If track_stock is False: skip stock check entirely (untracked service/product).
- 3 Outcomes:
  1. available >= requested: Normal draft (status: ok).
  2. 0 < available < requested: Stop and require owner decision (status: short, blocks approval).
  3. available <= 0: Out of stock (status: out_of_stock, blocks approval).
     Offers a copyable customer notification template with placeholder for restock date.
"""

from decimal import Decimal
from typing import Dict, Any, Optional


def check_item_stock(
    product: Dict[str, Any],
    requested_qty: Decimal,
) -> Dict[str, Any]:
    """Evaluate inventory availability for a line item.

    Args:
        product: Dict containing stock_on_hand, reserved, track_stock, name, unit.
        requested_qty: Decimal quantity requested by the customer.

    Returns:
        Dict containing:
            - stock_status: "ok" | "short" | "out_of_stock" | "untracked"
            - available: Available integer inventory (or None if untracked)
            - requested: Numerical requested quantity
            - flags: List of validation flags (if shortage detected)
            - decision_required: True if owner must choose an action before approval
            - copyable_reply: Ready-to-copy customer message if out-of-stock
    """
    track_stock = product.get("track_stock", True)
    prod_name = product.get("name", "Product")
    unit = product.get("unit", "pcs")

    # If stock tracking is disabled for this item
    if not track_stock:
        return {
            "stock_status": "untracked",
            "available": None,
            "requested": requested_qty,
            "flags": [],
            "decision_required": False,
            "copyable_reply": None,
        }

    stock_on_hand = int(product.get("stock_on_hand", 0) or 0)
    reserved = int(product.get("reserved", 0) or 0)
    available = max(0, stock_on_hand - reserved)
    req_int = int(requested_qty)

    # Case 1: Available >= requested
    if available >= req_int:
        return {
            "stock_status": "ok",
            "available": available,
            "requested": requested_qty,
            "flags": [],
            "decision_required": False,
            "copyable_reply": None,
        }

    # Case 2: Partial Stock Shortage (0 < available < requested)
    if 0 < available < req_int:
        shortfall = req_int - available
        return {
            "stock_status": "short",
            "available": available,
            "requested": requested_qty,
            "flags": [
                {
                    "code": "STOCK_SHORT",
                    "severity": "blocking",
                    "message": (
                        f"Stock shortage for '{prod_name}': {available} {unit} available on hand, "
                        f"but customer requested {req_int} {unit} (shortfall of {shortfall} {unit})."
                    ),
                    "suggested_action": (
                        f"Choose one: (1) Quote partial qty ({available} {unit}), "
                        f"(2) Schedule backorder for remaining {shortfall} {unit}, "
                        f"(3) Recommend alternative product, or (4) Decline."
                    ),
                    "blocks_approval": True,
                }
            ],
            "decision_required": True,
            "copyable_reply": None,
        }

    # Case 3: Completely Out of Stock (available <= 0)
    out_of_stock_message = (
        f"Hello, thank you for reaching out to us. Regarding your inquiry for '{prod_name}', "
        f"this item is currently out of stock. We expect fresh production/replenishment by [Expected Date]. "
        f"Please let us know if you would like to reserve from the upcoming batch or explore an alternative size/material."
    )

    return {
        "stock_status": "out_of_stock",
        "available": 0,
        "requested": requested_qty,
        "flags": [
            {
                "code": "OUT_OF_STOCK",
                "severity": "blocking",
                "message": f"Product '{prod_name}' is completely out of stock with 0 available units.",
                "suggested_action": "Notify customer using the out-of-stock message or propose an alternative.",
                "blocks_approval": True,
            }
        ],
        "decision_required": True,
        "copyable_reply": out_of_stock_message,
    }
