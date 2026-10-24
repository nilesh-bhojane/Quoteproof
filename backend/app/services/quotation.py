# Demo price list. Replace with uploaded/approved catalogue before real use.
PRICE_LIST = {
    "BOX-L": {"name": "Large box", "unit_price": 24.0, "unit": "pcs"},
}


def validate_quote(items: list[dict], tax_rate: float = 0.0) -> dict:
    validated, warnings = [], []
    subtotal = 0.0
    for item in items:
        sku = item.get("sku")
        quantity = item.get("quantity")
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
        product = PRICE_LIST[sku]
        line_total = round(qty * product["unit_price"], 2)
        subtotal += line_total
        validated.append({"sku": sku, "name": product["name"], "quantity": qty, "unit": product["unit"], "unit_price": product["unit_price"], "line_total": line_total})
    tax = round(subtotal * tax_rate / 100, 2)
    return {"items": validated, "subtotal": round(subtotal, 2), "tax_rate": tax_rate, "tax": tax, "total": round(subtotal + tax, 2), "warnings": warnings}
