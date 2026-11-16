from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session
from sqlalchemy import select

from database import get_db

from models.invoice import Invoice

from models.user import User

from models.audit_event import AuditEvent

from schemas.approval import (
    ReviewRequest,
    BankVerificationRequest,
    RejectRequest,
    AuditEventOut
)

from core.dependencies import require_roles

from services.approval_service import (
    check_approval_eligibility,
    ApprovalBlocked
)

from services.audit_service import record_audit


router = APIRouter(
    prefix="/api/invoices",
    tags=["Invoice Approval"]
)


def get_invoice_or_404(invoice_id, db):

    invoice = db.get(Invoice, invoice_id)

    if not invoice:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    return invoice


def ensure_pending(invoice):

    if invoice.approval_status != "PENDING":

        raise HTTPException(
            status_code=409,
            detail="Invoice is already finalized."
        )


# ------------------------------------------------
# 1. REVIEW INVOICE
# ------------------------------------------------

@router.post("/{invoice_id}/review")
def review_invoice(

    invoice_id: int,

    payload: ReviewRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "ADMIN"
        )
    )

):

    invoice = get_invoice_or_404(
        invoice_id,
        db
    )

    ensure_pending(invoice)

    if invoice.risk_status != "REVIEW":

        raise HTTPException(
            status_code=409,
            detail="Only REVIEW invoices can use this endpoint."
        )

    if invoice.review_status != "PENDING":

        raise HTTPException(
            status_code=409,
            detail="Invoice review has already been completed."
        )

    if any(
        finding.action == "HOLD"
        for finding in invoice.risk_findings
    ):

        raise HTTPException(
            status_code=409,
            detail="A blocking risk finding must be resolved before review clearance."
        )

    if payload.decision == "CLEAR_FOR_APPROVAL":

        invoice.review_status = "CLEARED"

        invoice.reviewed_by_id = current_user.id

        invoice.reviewed_at = datetime.now(timezone.utc)

        invoice.review_note = payload.note

        action = "INVOICE_REVIEW_CLEARED"

    else:

        invoice.review_status = "REJECTED"

        invoice.approval_status = "REJECTED"

        invoice.rejected_by_id = current_user.id

        invoice.rejected_at = datetime.now(timezone.utc)

        invoice.rejection_reason = payload.note

        action = "INVOICE_REVIEW_REJECTED"

    record_audit(
        db,
        invoice.id,
        current_user.id,
        action,
        "SUCCESS",
        {
            "decision": payload.decision,
            "note": payload.note
        }
    )

    db.commit()

    return {
        "message": "Review recorded successfully",
        "invoice_id": invoice.id,
        "risk_status": invoice.risk_status,
        "review_status": invoice.review_status,
        "approval_status": invoice.approval_status
    }


# ------------------------------------------------
# 2. VERIFY BANK CHANGE
# ------------------------------------------------

@router.post("/{invoice_id}/verify-bank-change")
def verify_bank_change(

    invoice_id: int,

    payload: BankVerificationRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "ADMIN"
        )
    )

):

    invoice = get_invoice_or_404(
        invoice_id,
        db
    )

    ensure_pending(invoice)

    if invoice.risk_status != "HOLD":

        raise HTTPException(
            status_code=409,
            detail="This invoice is not on HOLD."
        )

    # Find all blocking findings.

    hold_findings = [
        finding
        for finding in invoice.risk_findings
        if finding.action == "HOLD"
    ]

    hold_codes = {
        finding.rule_code
        for finding in hold_findings
    }

    # A duplicate must never be released by
    # simply claiming bank verification.

    if (
        hold_codes != {"BANK_DETAILS_CHANGED"}
        or len(invoice.risk_findings) != 1
    ):

        raise HTTPException(
            status_code=409,
            detail="This HOLD requires a different investigation."
        )

    if invoice.verification_status == "VERIFIED":

        raise HTTPException(
            status_code=409,
            detail="Bank change has already been verified."
        )

    invoice.verification_status = "VERIFIED"

    invoice.verified_by_id = current_user.id

    invoice.verified_at = datetime.now(timezone.utc)

    invoice.verification_method = payload.method

    invoice.verification_reference = payload.reference

    invoice.verification_note = payload.note

    record_audit(
        db,
        invoice.id,
        current_user.id,
        "BANK_CHANGE_VERIFIED",
        "SUCCESS",
        {
            "method": payload.method,
            "reference": payload.reference,
            "note": payload.note,
            "verification_attested_by": current_user.id
        }
    )

    db.commit()

    return {
        "message": "Bank verification recorded.",
        "invoice_id": invoice.id,
        "risk_status": invoice.risk_status,
        "verification_status": invoice.verification_status,
        "verified_by_id": invoice.verified_by_id,
        "next_step": "Independent finance approver must authorize the invoice."
    }


# ------------------------------------------------
# 3. APPROVE INVOICE
# ------------------------------------------------

@router.post("/{invoice_id}/approve")
def approve_invoice(

    invoice_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "FINANCE_APPROVER",
            "ADMIN"
        )
    )

):

    invoice = get_invoice_or_404(
        invoice_id,
        db
    )

    # Check the approval policy.

    try:

        check_approval_eligibility(
            invoice,
            current_user.id
        )

    except ApprovalBlocked as exc:

        record_audit(
            db,
            invoice.id,
            current_user.id,
            "INVOICE_APPROVAL",
            "BLOCKED",
            {
                "reason": str(exc),
                "risk_status": invoice.risk_status
            }
        )

        db.commit()

        raise HTTPException(
            status_code=409,
            detail=str(exc)
        )

    invoice.approval_status = "APPROVED"

    invoice.approved_by_id = current_user.id

    invoice.approved_at = datetime.now(timezone.utc)

    record_audit(
        db,
        invoice.id,
        current_user.id,
        "INVOICE_APPROVAL",
        "SUCCESS",
        {
            "risk_status": invoice.risk_status,
            "risk_score": invoice.risk_score,
            "approval_status": "APPROVED"
        }
    )

    db.commit()

    return {
        "message": "Invoice approved successfully",
        "invoice_id": invoice.id,
        "approval_status": invoice.approval_status,
        "risk_status": invoice.risk_status,
        "approved_by_id": current_user.id
    }


# ------------------------------------------------
# 4. REJECT INVOICE
# ------------------------------------------------

@router.post("/{invoice_id}/reject")
def reject_invoice(

    invoice_id: int,

    payload: RejectRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "FINANCE_APPROVER",
            "ADMIN"
        )
    )

):

    invoice = get_invoice_or_404(
        invoice_id,
        db
    )

    ensure_pending(invoice)

    invoice.approval_status = "REJECTED"

    invoice.rejected_by_id = current_user.id

    invoice.rejected_at = datetime.now(timezone.utc)

    invoice.rejection_reason = payload.reason

    record_audit(
        db,
        invoice.id,
        current_user.id,
        "INVOICE_REJECTION",
        "SUCCESS",
        {
            "reason": payload.reason,
            "risk_status": invoice.risk_status
        }
    )

    db.commit()

    return {
        "message": "Invoice rejected",
        "invoice_id": invoice.id,
        "approval_status": invoice.approval_status
    }


# ------------------------------------------------
# 5. GET AUDIT HISTORY
# ------------------------------------------------

@router.get(
    "/{invoice_id}/audit",
    response_model=list[AuditEventOut]
)
def get_invoice_audit(

    invoice_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "FINANCE_APPROVER",
            "ADMIN"
        )
    )

):

    invoice = get_invoice_or_404(
        invoice_id,
        db
    )

    events = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.invoice_id == invoice.id)
        .order_by(AuditEvent.created_at.asc())
    ).all()

    return events