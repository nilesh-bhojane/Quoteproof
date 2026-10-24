# Demo price list. Replace with uploaded/approved catalogue before real use.
PRICE_LIST = {
    "BOX-L": {"name": "Large box", "unit_price": 24.0, "unit": "pcs", "specs": "12x10x8, 3-ply"},
    "BOX-S": {"name": "Small box", "unit_price": 12.0, "unit": "pcs", "specs": "8x6x4, 3-ply"},
    "DEMO001": {"name": "Large box", "unit_price": 24.0, "unit": "pcs", "specs": "12x10x8, 3-ply"},
    "SMALL001": {"name": "Small box", "unit_price": 12.0, "unit": "pcs", "specs": "8x6x4, 3-ply"},
}

# Reverse lookup: map lowercase description fragments to SKU for matching
_DESCRIPTION_INDEX = {}
for _sku, _info in PRICE_LIST.items():
    _DESCRIPTION_INDEX[_info["name"].lower()] = _sku


def match_description_to_sku(description: str) -> str | None:
    """Try to match a free-text description to a known SKU.

    Uses case-insensitive substring matching against the price list.
    Returns the SKU string or None if no match is found.
    """
    if not description:
        return None
    lowered = description.strip().lower()
    # Exact match first
    if lowered in _DESCRIPTION_INDEX:
        return _DESCRIPTION_INDEX[lowered]
    # Substring match
    for name, sku in _DESCRIPTION_INDEX.items():
        if name in lowered or lowered in name:
            return sku
    return None


def validate_quote(items: list[dict], tax_rate: float = 0.0) -> dict:
    """Validate a list of quote line items against the known price list.

    Each item should have at least ``sku`` (or ``description``) and ``quantity``.
    If a ``sku`` is not provided but ``description`` is, we attempt to match it.

    Returns a dict with validated items, subtotal, tax, total, and any warnings.
    """
    validated, warnings = [], []
    subtotal = 0.0

    for item in items:
        sku = item.get("sku")
        description = item.get("description", "")
        quantity = item.get("quantity")

        # Try to resolve SKU from description if not provided
        if not sku and description:
            sku = match_description_to_sku(description)
            if sku:
                warnings.append(
                    f"Matched \"{description}\" to SKU {sku} via price list lookup."
                )

        if sku not in PRICE_LIST:
            warnings.append(f"Unknown SKU: {sku or 'missing'}; no price was assigned.")
            continue

        try:
            qty = float(quantity)
            if qty < 0:
                raise ValueError
        except (TypeError, ValueError):
            warnings.append(f"Invalid quantity for {sku}.")
            continue

        if qty == 0:
            warnings.append(f"Quantity for {sku} is zero; line will not appear in totals.")
            continue

        product = PRICE_LIST[sku]
        unit_price = product["unit_price"]
        line_total = round(qty * unit_price, 2)
        subtotal += line_total

        # "Why this price?" explanation per line
        explain = f"Standard catalogue rate of ₹{unit_price:.2f}/{product['unit']} for {product['name']}."

        validated.append({
            "sku": sku,
            "name": product["name"],
            "quantity": qty,
            "unit": product["unit"],
            "unit_price": unit_price,
            "line_total": line_total,
            "explain_text": explain,
        })

    # Ensure tax_rate is safe
    safe_tax_rate = max(0.0, min(float(tax_rate), 100.0))
    tax = round(subtotal * safe_tax_rate / 100, 2)

    can_approve = len(validated) > 0 and len(warnings) == 0

    return {
        "items": validated,
        "subtotal": round(subtotal, 2),
        "tax_rate": safe_tax_rate,
        "tax": tax,
        "total": round(subtotal + tax, 2),
        "warnings": warnings,
        "can_approve": can_approve,
    }
