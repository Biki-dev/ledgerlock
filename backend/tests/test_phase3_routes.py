from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from core.dependencies import get_current_user, require_roles
from core.security import hash_password
from database import Base
from migrate_phase3 import migrate_phase3
from models.invoice import Invoice
from models.user import User
from routes.approvals import (
    approve_invoice,
    get_invoice_audit,
    reject_invoice,
    review_invoice,
    verify_bank_change,
    router as approval_router,
)
from routes.auth import get_me, login
from schemas.approval import (
    BankVerificationRequest,
    RejectRequest,
    ReviewRequest,
)
from schemas.auth import LoginRequest
from services.audit_service import record_audit


class FakeDatabase:
    def __init__(self, invoice):
        self.invoice = invoice
        self.events = []

    def get(self, model, invoice_id):
        return self.invoice if invoice_id == self.invoice.id else None

    def add(self, event):
        self.events.append(event)

    def commit(self):
        pass

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: self.events)


def test_repeat_review_is_rejected():
    invoice = SimpleNamespace(
        id=1,
        approval_status="PENDING",
        risk_status="REVIEW",
        risk_findings=[],
        review_status="PENDING",
        reviewed_by_id=None,
        reviewed_at=None,
        review_note=None,
        rejected_by_id=None,
        rejected_at=None,
        rejection_reason=None,
    )
    db = FakeDatabase(invoice)
    reviewer = SimpleNamespace(id=7)
    request = ReviewRequest(
        decision="CLEAR_FOR_APPROVAL",
        note="Reviewed supporting invoice details.",
    )

    review_invoice(1, request, db, reviewer)
    assert db.events[0].action == "INVOICE_REVIEW_CLEARED"

    with pytest.raises(HTTPException) as error:
        review_invoice(1, request, db, reviewer)

    assert error.value.status_code == 409


def test_review_cannot_clear_invoice_with_a_hold_finding():
    invoice = SimpleNamespace(
        id=11,
        approval_status="PENDING",
        risk_status="REVIEW",
        risk_findings=[SimpleNamespace(action="HOLD")],
        review_status="PENDING",
    )

    with pytest.raises(HTTPException) as error:
        review_invoice(
            11,
            ReviewRequest(
                decision="CLEAR_FOR_APPROVAL",
                note="Reviewed supporting invoice details.",
            ),
            FakeDatabase(invoice),
            SimpleNamespace(id=7),
        )
    assert error.value.status_code == 409


def test_bank_verification_is_audited_and_cannot_repeat():
    invoice = SimpleNamespace(
        id=2,
        approval_status="PENDING",
        risk_status="HOLD",
        risk_findings=[
            SimpleNamespace(
                action="HOLD",
                rule_code="BANK_DETAILS_CHANGED",
            )
        ],
        verification_status="PENDING",
        verified_by_id=None,
        verified_at=None,
        verification_method=None,
        verification_reference=None,
        verification_note=None,
    )
    db = FakeDatabase(invoice)
    reviewer = SimpleNamespace(id=8)
    request = BankVerificationRequest(
        method="PHONE_TO_KNOWN_CONTACT",
        reference="CALL-123",
        note="Confirmed with the known vendor contact.",
    )

    verify_bank_change(2, request, db, reviewer)

    assert db.events[0].action == "BANK_CHANGE_VERIFIED"
    assert db.events[0].outcome == "SUCCESS"
    with pytest.raises(HTTPException) as error:
        verify_bank_change(2, request, db, reviewer)
    assert error.value.status_code == 409


def test_bank_verification_cannot_bypass_an_additional_finding():
    invoice = SimpleNamespace(
        id=3,
        approval_status="PENDING",
        risk_status="HOLD",
        risk_findings=[
            SimpleNamespace(action="HOLD", rule_code="BANK_DETAILS_CHANGED"),
            SimpleNamespace(action="REVIEW", rule_code="PRICE_INFLATION"),
        ],
        verification_status="PENDING",
    )

    with pytest.raises(HTTPException) as error:
        verify_bank_change(
            3,
            BankVerificationRequest(
                method="PHONE_TO_KNOWN_CONTACT",
                reference="CALL-123",
                note="Confirmed with the known vendor contact.",
            ),
            FakeDatabase(invoice),
            SimpleNamespace(id=8),
        )
    assert error.value.status_code == 409


def test_approval_rejection_and_blocked_approval_are_audited():
    clear_invoice = SimpleNamespace(
        id=4,
        approval_status="PENDING",
        risk_status="CLEAR",
        risk_score=0,
        risk_findings=[],
        approved_by_id=None,
        approved_at=None,
    )
    approval_db = FakeDatabase(clear_invoice)
    approver = SimpleNamespace(id=9)

    approve_invoice(4, approval_db, approver)
    assert approval_db.events[-1].action == "INVOICE_APPROVAL"
    assert approval_db.events[-1].outcome == "SUCCESS"

    with pytest.raises(HTTPException) as error:
        approve_invoice(4, approval_db, approver)
    assert error.value.status_code == 409
    assert approval_db.events[-1].outcome == "BLOCKED"

    rejected_invoice = SimpleNamespace(
        id=5,
        approval_status="PENDING",
        risk_status="CLEAR",
        rejected_by_id=None,
        rejected_at=None,
        rejection_reason=None,
    )
    rejection_db = FakeDatabase(rejected_invoice)
    reject_invoice(
        5,
        RejectRequest(reason="Supporting documentation was incomplete."),
        rejection_db,
        SimpleNamespace(id=7),
    )
    assert rejection_db.events[-1].action == "INVOICE_REJECTION"
    assert rejection_db.events[-1].outcome == "SUCCESS"


def test_audit_endpoint_returns_saved_history_in_order():
    invoice = SimpleNamespace(id=6)
    events = [
        SimpleNamespace(action="INVOICE_REVIEW_CLEARED"),
        SimpleNamespace(action="INVOICE_APPROVAL"),
    ]
    db = FakeDatabase(invoice)
    db.events = events

    result = get_invoice_audit(6, db, SimpleNamespace(id=1))

    assert result == events
    assert [event.action for event in result] == [
        "INVOICE_REVIEW_CLEARED",
        "INVOICE_APPROVAL",
    ]


def test_audit_event_persists_and_is_returned_by_endpoint():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        user = User(
            full_name="Audit Reviewer",
            email="audit@example.test",
            password_hash="not-used",
            role="FINANCE_REVIEWER",
        )
        invoice = Invoice(
            source_filename="audit.pdf",
            storage_path="",
            sha256="a" * 64,
            vendor_name="Audit Vendor",
            risk_status="CLEAR",
        )
        db.add_all([user, invoice])
        db.flush()
        record_audit(
            db,
            invoice.id,
            user.id,
            "INVOICE_REVIEW_CLEARED",
            "SUCCESS",
            {"decision": "CLEAR_FOR_APPROVAL"},
        )
        db.commit()

        events = get_invoice_audit(invoice.id, db, user)

        assert len(events) == 1
        assert events[0].action == "INVOICE_REVIEW_CLEARED"
        assert events[0].details == {"decision": "CLEAR_FOR_APPROVAL"}

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_phase3_migration_preserves_existing_invoice(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'phase2.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE invoices (id INTEGER PRIMARY KEY, invoice_number TEXT)"
        )
        connection.exec_driver_sql(
            "INSERT INTO invoices (id, invoice_number) VALUES (71, 'OLD-071')"
        )

    migrate_phase3(engine)

    with engine.connect() as connection:
        existing = connection.exec_driver_sql(
            "SELECT id, invoice_number FROM invoices WHERE id = 71"
        ).one()
        columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(invoices)"
            ).fetchall()
        }

    assert existing == (71, "OLD-071")
    assert {"approval_status", "review_status", "verification_status"}.issubset(
        columns
    )
    engine.dispose()


def test_login_me_password_hash_and_role_restrictions():
    password = "StrongDemoPass123!"
    user = SimpleNamespace(
        id=12,
        full_name="Finance Reviewer",
        email="reviewer@example.test",
        password_hash=hash_password(password),
        role="FINANCE_REVIEWER",
        is_active=True,
    )

    class AuthDatabase:
        def scalar(self, statement):
            return user

        def get(self, model, user_id):
            return user if user_id == user.id else None

    db = AuthDatabase()
    response = login(
        LoginRequest(email=user.email, password=password),
        db,
    )
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=response["access_token"],
    )
    authenticated_user = get_current_user(credentials, db)

    assert response["token_type"] == "bearer"
    assert response["user"].id == user.id
    assert get_me(authenticated_user)["email"] == user.email
    assert user.password_hash != password

    with pytest.raises(HTTPException) as error:
        require_roles("FINANCE_APPROVER")(user)
    assert error.value.status_code == 403


def test_audit_routes_are_read_only():
    audit_routes = [
        route
        for route in approval_router.routes
        if "audit" in route.path
    ]

    assert audit_routes
    assert all(route.methods == {"GET"} for route in audit_routes)