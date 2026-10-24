"""Analytics and Evidence Ledger Service — Contributor C

Tracks key audit trail events (draft created, fields edited, warning resolved,
approved, rejected) and provides ROI calculation functions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# In-memory storage for hackathon audit events
_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "evt-init-1",
        "quote_id": "demo-001",
        "event_type": "inquiry_received",
        "timestamp": "2026-10-24T21:00:00Z",
        "details": {"source": "paste_input", "description": "Raw inquiry text captured"},
    },
    {
        "id": "evt-init-2",
        "quote_id": "demo-001",
        "event_type": "draft_created",
        "timestamp": "2026-10-24T21:01:15Z",
        "details": {"items_count": 2, "status": "draft"},
    },
    {
        "id": "evt-init-3",
        "quote_id": "demo-001",
        "event_type": "warning_flagged",
        "timestamp": "2026-10-24T21:01:20Z",
        "details": {"warning": "Smaller box specification unresolved"},
    },
]


def record_event(quote_id: str, event_type: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Record an audit trail event with an ISO timestamp."""
    event = {
        "id": f"evt-{len(_EVENTS) + 1}",
        "quote_id": quote_id,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }
    _EVENTS.append(event)
    return event


def get_events(quote_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all recorded events, optionally filtered by quote_id."""
    if quote_id:
        return [e for e in _EVENTS if e.get("quote_id") == quote_id]
    return list(_EVENTS)


def clear_events() -> None:
    """Helper for testing / reset."""
    _EVENTS.clear()


def calculate_roi(
    manual_seconds: Optional[float],
    assisted_seconds: Optional[float],
    hourly_labour_cost: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate time difference, percentage reduction, and estimated labor value.

    Labour value is ONLY estimated when an explicit, positive hourly_labour_cost
    is provided.
    """
    if manual_seconds is None or assisted_seconds is None:
        return {
            "time_saved_seconds": None,
            "percentage_reduction": None,
            "estimated_labour_value_saved": None,
            "is_illustrative": True,
            "message": "Enter manual and assisted durations to calculate savings.",
        }

    manual = max(0.0, float(manual_seconds))
    assisted = max(0.0, float(assisted_seconds))
    time_saved = max(0.0, manual - assisted)

    percentage_reduction = round((time_saved / manual * 100.0), 2) if manual > 0 else 0.0

    labour_saved = None
    if hourly_labour_cost is not None and hourly_labour_cost > 0:
        # (seconds saved / 3600) * hourly rate
        labour_saved = round((time_saved / 3600.0) * float(hourly_labour_cost), 2)

    return {
        "manual_seconds": manual,
        "assisted_seconds": assisted,
        "time_saved_seconds": round(time_saved, 2),
        "percentage_reduction": percentage_reduction,
        "hourly_labour_cost": hourly_labour_cost,
        "estimated_labour_value_saved": labour_saved,
        "is_illustrative": True,
        "note": "Values are illustrative estimates. Replace with measured trial data.",
    }


def summary() -> Dict[str, Any]:
    """Summary of audit sessions and illustrative baseline metrics."""
    return {
        "manual_seconds": 600,
        "assisted_seconds": 240,
        "quotes_tested": len({e["quote_id"] for e in _EVENTS if "quote_id" in e}),
        "total_events_logged": len(_EVENTS),
        "hourly_labour_cost": None,
        "estimated_labour_value_saved": None,
        "note": "Illustrative baseline. Explicit hourly cost required for labour calculation.",
    }
