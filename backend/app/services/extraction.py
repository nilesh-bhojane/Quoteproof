"""Deterministic placeholder parser for inquiry extraction.

Returns a JSON-compatible dict with:
- items: list of extracted line items
- missing_fields: any heuristically-detected gaps (e.g. dimensions for a "smaller" item)
- warnings: static notice that this is a stub
- mode: identifier for downstream code
"""

import re
from typing import List, Dict


def _looks_like_spec(text: str) -> bool:
    """Return True if *text* looks like a specification rather than a new item.

    Heuristics:
    - Starts with a digit directly followed by a hyphen (e.g. "3‑ply", "2-ply")
    - Very short (≤ 10 chars) and has no leading quantity‑description structure
    """
    stripped = text.strip()
    # e.g. "3-ply", "3‑ply"
    if re.match(r"^\d[\d\s]*[‑\-]\w", stripped):
        return True
    if len(stripped) <= 10:
        return True
    return False


def extract_inquiry(text: str) -> Dict:
    """Parse *text* for simple ``<quantity> <description>`` patterns.

    Algorithm:
    1. Split on commas and the word 'and'.
    2. For each segment, look for a leading quantity.
    3. If a segment has no quantity but looks like a spec (e.g. "3-ply"),
       attach it to the previous item's specifications instead of creating
       a new item.
    """
    items: List[Dict] = []

    # Split on commas and the word "and" (case-insensitive)
    parts = re.split(r",|\band\b", text, flags=re.I)

    for part in parts:
        part = part.strip().rstrip(".")
        if not part:
            continue

        # Find the first number (quantity) in this segment
        m = re.search(r"(\d[\d,]*)", part)

        if not m:
            # No quantity found — treat as spec for previous item if possible
            if items and _looks_like_spec(part):
                spec_text = part.strip()
                items[-1]["specifications"]["note"] = (
                    (items[-1]["specifications"].get("note", "") + " " + spec_text).strip()
                )
            continue

        quantity_str = m.group(1)
        # Description is everything after the quantity
        description = part[m.end():].strip()
        # Strip leading "need " if present (sentence start)
        description = re.sub(r"^need\s+", "", description, flags=re.I)

        if not description:
            continue

        # Check if this number is a spec pattern like "3‑ply" (digit followed directly by hyphen)
        remainder = part[m.end():]
        if re.match(r"^[‑\-]\w", remainder) and items:
            spec_text = part.strip()
            items[-1]["specifications"]["note"] = (
                (items[-1]["specifications"].get("note", "") + " " + spec_text).strip()
            )
            continue

        items.append({
            "description": description,
            "quantity": int(quantity_str.replace(",", "")),
            "unit": "pcs",
            "specifications": {},
            "sku": None,
        })

    # Heuristic for missing fields – detect the word "smaller"
    missing: List[str] = []
    if re.search(r"\bsmaller\b", text, re.I):  # single backslash = correct word boundary
        missing.append("dimensions/SKU for smaller item")

    return {
        "items": items,
        "missing_fields": missing,
        "warnings": ["Starter parser only: verify every extracted field."],
        "mode": "deterministic_stub_not_llm",
    }
