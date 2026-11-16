from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from services.approval_service import (
    check_approval_eligibility,
    ApprovalBlocked
)


def make_invoice(
    risk_status,
    review_status="NOT_REQUIRED",
    reviewed_by_id=None,
    verification_status="NOT_REQUIRED",
    verified_by_id=None,
    hold_codes=None
):

    findings = [
        SimpleNamespace(
            rule_code=code,
            action="HOLD"
        )
        for code in (hold_codes or [])
    ]

    return SimpleNamespace(
        approval_status="PENDING",
        risk_status=risk_status,
        review_status=review_status,
        reviewed_by_id=reviewed_by_id,
        reviewed_at=(
            datetime.now(timezone.utc) - timedelta(minutes=1)
            if review_status == "CLEARED"
            else None
        ),
        verification_status=verification_status,
        verified_by_id=verified_by_id,
        risk_findings=findings
    )


def test_clear_invoice_can_be_approved():

    invoice = make_invoice("CLEAR")

    assert check_approval_eligibility(
        invoice, approver_id=2
    )


def test_review_requires_clearance():

    invoice = make_invoice("REVIEW")

    with pytest.raises(ApprovalBlocked):
        check_approval_eligibility(invoice, 2)


def test_reviewer_cannot_approve_own_review():

    invoice = make_invoice(
        "REVIEW",
        review_status="CLEARED",
        reviewed_by_id=2
    )

    with pytest.raises(ApprovalBlocked):
        check_approval_eligibility(invoice, 2)


def test_different_approver_can_approve_review():

    invoice = make_invoice(
        "REVIEW",
        review_status="CLEARED",
        reviewed_by_id=1
    )

    assert check_approval_eligibility(invoice, 2)


def test_review_with_a_hold_finding_cannot_be_approved():

    invoice = make_invoice(
        "REVIEW",
        review_status="CLEARED",
        reviewed_by_id=1,
        hold_codes=["BANK_DETAILS_CHANGED"]
    )

    with pytest.raises(ApprovalBlocked):
        check_approval_eligibility(invoice, 2)


def test_finding_added_after_review_clearance_blocks_approval():

    invoice = make_invoice(
        "REVIEW",
        review_status="CLEARED",
        reviewed_by_id=1
    )
    invoice.risk_findings.append(
        SimpleNamespace(
            action="REVIEW",
            rule_code="NEW_REVIEW_FINDING",
            created_at=datetime.now(timezone.utc)
        )
    )

    with pytest.raises(ApprovalBlocked):
        check_approval_eligibility(invoice, 2)


def test_bank_hold_requires_verification():

    invoice = make_invoice(
        "HOLD",
        hold_codes=["BANK_DETAILS_CHANGED"]
    )

    with pytest.raises(ApprovalBlocked):
        check_approval_eligibility(invoice, 2)


def test_bank_hold_requires_different_approver():

    invoice = make_invoice(
        "HOLD",
        verification_status="VERIFIED",
        verified_by_id=2,
        hold_codes=["BANK_DETAILS_CHANGED"]
    )

    with pytest.raises(ApprovalBlocked):
        check_approval_eligibility(invoice, 2)


def test_bank_hold_allows_independent_approver():

    invoice = make_invoice(
        "HOLD",
        verification_status="VERIFIED",
        verified_by_id=1,
        hold_codes=["BANK_DETAILS_CHANGED"]
    )

    assert check_approval_eligibility(invoice, 2)


def test_duplicate_hold_cannot_be_released():

    invoice = make_invoice(
        "HOLD",
        verification_status="VERIFIED",
        verified_by_id=1,
        hold_codes=["EXACT_FILE_DUPLICATE"]
    )

    with pytest.raises(ApprovalBlocked):
        check_approval_eligibility(invoice, 2)


def test_rejected_invoice_cannot_be_approved():

    invoice = make_invoice("CLEAR")
    invoice.approval_status = "REJECTED"

    with pytest.raises(ApprovalBlocked):
        check_approval_eligibility(invoice, 2)