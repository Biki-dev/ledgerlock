from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.dependencies import require_roles
from database import get_db
from models.audit_event import AuditEvent
from models.invoice import Invoice
from models.user import User
from schemas.audit import GlobalAuditEventOut


router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"]
)


@router.get("", response_model=list[GlobalAuditEventOut])
def get_global_audit(
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "FINANCE_APPROVER",
            "ADMIN"
        )
    )
):
    rows = db.execute(
        select(AuditEvent, Invoice.invoice_number, User.full_name)
        .outerjoin(Invoice, Invoice.id == AuditEvent.invoice_id)
        .outerjoin(User, User.id == AuditEvent.actor_id)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .limit(limit)
    ).all()

    return [
        {
            "id": event.id,
            "invoice_id": event.invoice_id,
            "invoice_number": invoice_number,
            "actor_id": event.actor_id,
            "actor_name": actor_name or "System",
            "action": event.action,
            "outcome": event.outcome,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event, invoice_number, actor_name in rows
    ]