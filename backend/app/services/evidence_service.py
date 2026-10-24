"""Evidence Service for logging append-only audit events.

Per CONTEXT.md Section 8 & 9 (Handshake #2):
- Every event has: id, correlation_id, quote_id, actor (ai / human / system), action, before, after, at.
- Used by both Person A (intake / draft events) and Person B (review / approval / rejection events).
- Appends to audit_log table. Never rewrites or deletes existing events.
"""

import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_event(
    action: str,
    actor: str,
    quote_id: Optional[Any] = None,
    correlation_id: Optional[str] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> Optional[AuditLog]:
    """Append a traceable event to the Evidence Ledger (audit_log).

    Args:
        action: Event action name (e.g. "draft_extracted", "stock_decision", "quote_approved").
        actor: One of 'ai', 'human', or 'system'.
        quote_id: UUID or string ID of associated quotation.
        correlation_id: Optional correlation string for tracing requests.
        before: State before action.
        after: State after action.
        db: Active SQLAlchemy database session (if writing to DB).

    Returns:
        The instantiated or persisted AuditLog record.
    """
    event = AuditLog(
        id=uuid.uuid4(),
        correlation_id=correlation_id or f"corr-{uuid.uuid4().hex[:8]}",
        quote_id=uuid.UUID(str(quote_id)) if quote_id else None,
        actor=actor,
        action=action,
        before=before or {},
        after=after or {},
    )

    if db is not None:
        try:
            db.add(event)
            db.commit()
            db.refresh(event)
        except Exception:
            db.rollback()

    return event
