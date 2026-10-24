"""Deterministic Product Matching Service.

Per CONTEXT.md Section 5 & 8:
- Matching: exact SKU or name first, then alias matching, then deterministic keyword rules.
- Weak or multiple matches go to the owner. Never invent a SKU.
- Flags raised:
  - UNKNOWN_PRODUCT (Critical/blocking): No matching product in catalogue.
  - AMBIGUOUS_PRODUCT (Critical/blocking): Multiple products match; owner must select.
  - STALE_PRICE (Warning): Product price has not been updated within stale_days limit (default 30 days).
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional


def match_product(
    description: str,
    catalog: List[Dict[str, Any]],
    specifications: Optional[Dict[str, Any]] = None,
    stale_days: int = 30,
) -> Dict[str, Any]:
    """Match an extracted customer description to a catalogue product.

    Args:
        description: Extracted item description text.
        catalog: List of product dicts or model instances.
        specifications: Optional spec dict (e.g. {"size": "12x10x8", "ply": "3-ply"}).
        stale_days: Number of days before a price is flagged as stale.

    Returns:
        Dict containing:
            - product: Matched product dict or None
            - match_type: "exact" | "alias" | "keyword" | "ambiguous" | "none"
            - candidates: List of candidate products (for ambiguous matches)
            - flags: Standardized validation flag list
    """
    clean_desc = description.strip().lower()
    specifications = specifications or {}

    # 1. Exact Name Match
    for prod in catalog:
        prod_name = str(prod.get("name", "")).strip().lower()
        if clean_desc == prod_name:
            flags = _check_stale_price(prod, stale_days)
            return {"product": prod, "match_type": "exact", "candidates": [], "flags": flags}

    # 2. Alias Match
    alias_matches = []
    for prod in catalog:
        aliases = prod.get("aliases") or []
        for alias in aliases:
            clean_alias = str(alias).strip().lower()
            if clean_alias == clean_desc or clean_alias in clean_desc or clean_desc in clean_alias:
                alias_matches.append(prod)
                break

    if len(alias_matches) == 1:
        prod = alias_matches[0]
        flags = _check_stale_price(prod, stale_days)
        return {"product": prod, "match_type": "alias", "candidates": [], "flags": flags}
    elif len(alias_matches) > 1:
        return {
            "product": None,
            "match_type": "ambiguous",
            "candidates": alias_matches,
            "flags": [
                {
                    "code": "AMBIGUOUS_PRODUCT",
                    "severity": "blocking",
                    "message": f"Multiple catalogue products match '{description}'. Please select the exact item.",
                    "suggested_action": "Pick the correct product from the candidate list.",
                    "blocks_approval": True,
                }
            ],
        }

    # 3. Substring / Specification Matching
    spec_tokens = set(clean_desc.replace("-", " ").replace("x", " ").split())
    for v in specifications.values():
        if isinstance(v, str):
            spec_tokens.update(v.lower().replace("-", " ").replace("x", " ").split())

    keyword_matches = []
    for prod in catalog:
        prod_text = (
            str(prod.get("name", "")) + " " + " ".join(str(a) for a in prod.get("aliases", []))
        ).lower().replace("-", " ").replace("x", " ")
        prod_tokens = set(prod_text.split())

        # Measure keyword overlap
        overlap = spec_tokens.intersection(prod_tokens)
        if len(overlap) >= 2:
            keyword_matches.append((len(overlap), prod))

    if keyword_matches:
        # Sort descending by overlap count
        keyword_matches.sort(key=lambda x: x[0], reverse=True)
        top_score = keyword_matches[0][0]
        top_candidates = [p for score, p in keyword_matches if score == top_score]

        if len(top_candidates) == 1:
            prod = top_candidates[0]
            flags = _check_stale_price(prod, stale_days)
            return {"product": prod, "match_type": "keyword", "candidates": [], "flags": flags}
        else:
            return {
                "product": None,
                "match_type": "ambiguous",
                "candidates": top_candidates,
                "flags": [
                    {
                        "code": "AMBIGUOUS_PRODUCT",
                        "severity": "blocking",
                        "message": f"Multiple potential matches found for '{description}'. Please clarify.",
                        "suggested_action": "Choose from candidates or specify product name manually.",
                        "blocks_approval": True,
                    }
                ],
            }

    # 4. No Match Found
    return {
        "product": None,
        "match_type": "none",
        "candidates": [],
        "flags": [
            {
                "code": "UNKNOWN_PRODUCT",
                "severity": "blocking",
                "message": f"Product '{description}' could not be matched to any item in the catalogue.",
                "suggested_action": "Link to an existing product or add to price list.",
                "blocks_approval": True,
            }
        ],
    }


def _check_stale_price(product: Dict[str, Any], stale_days: int) -> List[Dict[str, Any]]:
    """Check if a product's price has not been updated within stale_days limit."""
    updated_at = product.get("price_updated_at")
    if not updated_at:
        return []

    if isinstance(updated_at, str):
        try:
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            return []

    now = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    if (now - updated_at) > timedelta(days=stale_days):
        days_ago = (now - updated_at).days
        return [
            {
                "code": "STALE_PRICE",
                "severity": "warning",
                "message": f"Product price was last updated {days_ago} days ago (exceeds {stale_days}-day review threshold).",
                "suggested_action": "Confirm current supplier cost and sell price before final approval.",
                "blocks_approval": False,
            }
        ]
    return []
