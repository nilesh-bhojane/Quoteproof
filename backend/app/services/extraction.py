"""Deterministic placeholder parser for inquiry extraction.

Returns a JSON‑compatible dict with:
- items: list of extracted line items
- missing_fields: any heuristically‑detected gaps (e.g. dimensions for a "smaller" item)
- warnings: static notice that this is a stub
- mode: identifier for downstream code
"""

import re
from typing import List, Dict


def extract_inquiry(text: str) -> Dict:
    """Parse *text* for a simple ``<quantity> <description>`` pattern.

    The implementation is deliberately deterministic – no external LLM calls –
    because Contributor A's task focuses on the UI/service contract, not on AI
    quality.  It is easy to replace later with an LLM adapter.
    """
    items: List[Dict] = []
    # Capture sequences like "500 boxes" or "200 smaller ones"
    patterns = re.findall(
        r"(?:need\s+)?([\d,]+)\s+([a-zA-Z0-9 &\-]+?)(?=,|\\.|\\band\\b|$)",
        text,
        flags=re.I,
    )
    for quantity, description in patterns:
        cleaned = description.strip()
        if not cleaned:
            continue
        items.append(
            {
                "description": cleaned,
                "quantity": int(quantity.replace(",", "")),
                "unit": "pcs",
                "specifications": {},
                "sku": None,
            }
        )

    # Simple heuristic for missing fields – look for the word "smaller"
    missing: List[str] = []
    if re.search(r"\\bsmaller\\b", text, re.I):
        missing.append("dimensions/SKU for smaller item")

    return {
        "items": items,
        "missing_fields": missing,
        "warnings": ["Starter parser only: verify every extracted field."],
        "mode": "deterministic_stub_not_llm",
    }
