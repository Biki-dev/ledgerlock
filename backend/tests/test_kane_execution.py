import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base
from models.assurance_run import AssuranceRun
from models.audit_event import AuditEvent
from models.invoice import Invoice
from models.risk_finding import RiskFinding
from services import kane_execution
from services import kane_runner
from scripts import reset_demo_invoice


def test_find_evidence_pack_returns_none_when_no_pack_exists(tmp_path):
    session_dir = tmp_path / "session"
    (session_dir / "evidence").mkdir(parents=True)

    assert kane_execution.find_evidence_pack(str(session_dir)) is None


def test_find_evidence_pack_returns_actual_pack(tmp_path):
    session_dir = tmp_path / "session"
    evidence_file = session_dir / "evidence" / "sealed.evidence"
    evidence_file.parent.mkdir(parents=True)
    evidence_file.write_text("evidence", encoding="utf-8")

    assert kane_execution.find_evidence_pack(str(session_dir)) == str(evidence_file)


def test_kane_output_redacts_configured_approver_password():
    output = '"value":"private-test-password"'

    redacted = kane_execution.redact_kane_output(
        output,
        "private-test-password",
    )

    assert "private-test-password" not in redacted
    assert "[REDACTED]" in redacted


def test_passing_retest_marks_original_agent_completed(monkeypatch):
    previous_run = SimpleNamespace(agent_status="FAILED")
    run = SimpleNamespace(
        id=22,
        retest_of_run_id=17,
        scenario_code="bank_change_approval_guard",
        objective="Verify an unverified bank change is blocked.",
        status="QUEUED",
        session_dir=None,
    )

    class FakeSession:
        def __init__(self):
            self.commits = 0

        def get(self, model, run_id):
            if model is not AssuranceRun:
                raise AssertionError("Unexpected model lookup")
            return run if run_id == run.id else previous_run

        def commit(self):
            self.commits += 1

        def rollback(self):
            raise AssertionError("Unexpected rollback")

        def close(self):
            pass

    session = FakeSession()
    monkeypatch.setattr(kane_execution, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        kane_execution,
        "get_kane_variables_file",
        lambda: (None, "/tmp/kane-variables.json"),
    )
    monkeypatch.setattr(
        kane_execution,
        "get_approver_password",
        lambda: "private-test-password",
    )
    monkeypatch.setattr(kane_execution.shutil, "which", lambda _: "/usr/bin/kane-cli")
    monkeypatch.setattr(
        kane_execution.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "type": "run_end",
                "status": "passed",
                "summary": "The approval was blocked.",
                "reason": "Objective completed.",
                "duration": 2.0,
            }),
            stderr="",
        ),
    )

    kane_execution.execute_kane_run(run.id)

    assert run.status == "PASSED"
    assert previous_run.agent_status == "COMPLETED"
    assert session.commits == 2


def test_timed_out_process_with_partial_pass_is_still_error(monkeypatch):
    run = SimpleNamespace(
        id=23,
        retest_of_run_id=None,
        scenario_code="bank_change_approval_guard",
        objective="Verify an unverified bank change is blocked.",
        status="QUEUED",
        session_dir=None,
    )

    class FakeSession:
        def get(self, model, run_id):
            assert model is AssuranceRun
            return run if run_id == run.id else None

        def commit(self):
            pass

        def rollback(self):
            raise AssertionError("Unexpected rollback")

        def close(self):
            pass

    monkeypatch.setattr(kane_execution, "SessionLocal", FakeSession)
    monkeypatch.setattr(kane_execution.shutil, "which", lambda _: "/usr/bin/kane-cli")
    monkeypatch.setattr(
        kane_execution,
        "get_kane_variables_file",
        lambda: (None, "/tmp/kane-variables.json"),
    )
    monkeypatch.setattr(
        kane_execution,
        "get_approver_password",
        lambda: "private-test-password",
    )

    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 300
        raise subprocess.TimeoutExpired(
            args[0],
            kwargs["timeout"],
            output=(
                b'{"step":1,"status":"done","remark":"guard blocked"}'
                b'\n{"type":"run_end","status":"passed","reason":"Complete."}'
            ),
            stderr=b"private-test-password",
        )

    monkeypatch.setattr(kane_execution.subprocess, "run", timeout)

    kane_execution.execute_kane_run(run.id)

    assert run.status == "ERROR"
    assert run.kane_status == "passed"
    assert run.step_events[0]["remark"] == "guard blocked"
    assert "not considered verified" in run.reason
    assert "private-test-password" not in run.stderr_output
    assert "[REDACTED]" in run.stderr_output


def test_scenario_objectives_keep_password_as_variable():
    from services.kane_runner import SCENARIOS

    for scenario in SCENARIOS.values():
        objective = scenario["objective"](12)
        assert "{{approver_password}}" in objective
        assert "password {{approver_password}}" in objective


def test_kane_variables_file_marks_password_secret(monkeypatch):
    monkeypatch.setattr(
        kane_runner,
        "APPROVER_PASSWORD",
        "a-unique-local-approver-password",
    )
    temporary_directory, variables_path = (
        kane_runner.get_kane_variables_file()
    )

    try:
        variables = json.loads(
            Path(variables_path).read_text(encoding="utf-8")
        )
        assert variables["approver_email"]["secret"] is False
        assert variables["approver_password"]["secret"] is True
        assert os.stat(variables_path).st_mode & 0o777 == 0o600
    finally:
        temporary_directory.cleanup()


def test_reset_demo_invoice_preserves_hold_findings_and_audit(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        invoice = Invoice(
            approval_status="APPROVED",
            risk_status="HOLD",
            review_status="NOT_REQUIRED",
            verification_status="VERIFIED",
            verified_by_id=3,
            source_filename="DEMO_bank_changed.pdf",
            storage_path="",
            sha256="demo-sha",
        )
        invoice.risk_findings.append(
            RiskFinding(
                rule_code="BANK_DETAILS_CHANGED",
                severity="CRITICAL",
                action="HOLD",
                message="Bank details changed.",
                evidence={},
            )
        )
        db.add(invoice)
        db.flush()
        db.add(
            AuditEvent(
                invoice_id=invoice.id,
                actor_id=None,
                action="INVOICE_APPROVAL",
                outcome="BLOCKED",
                details={"test": True},
            )
        )
        db.commit()
        invoice_id = invoice.id

    monkeypatch.setattr(
        reset_demo_invoice,
        "SessionLocal",
        lambda: Session(engine),
    )

    reset_demo_invoice.reset_demo_invoice(invoice_id)

    with Session(engine) as db:
        invoice = db.get(Invoice, invoice_id)
        assert invoice.approval_status == "PENDING"
        assert invoice.approved_by_id is None
        assert invoice.verification_status == "PENDING"
        assert invoice.verified_by_id is None
        assert invoice.risk_status == "HOLD"
        assert [finding.rule_code for finding in invoice.risk_findings] == [
            "BANK_DETAILS_CHANGED"
        ]
        assert db.query(AuditEvent).filter_by(
            invoice_id=invoice_id
        ).count() == 1

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_reset_refuses_non_demo_invoice(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        invoice = Invoice(
            approval_status="APPROVED",
            risk_status="HOLD",
            source_filename="business_invoice.pdf",
            storage_path="",
            sha256="business-sha",
        )
        invoice.risk_findings.append(
            RiskFinding(
                rule_code="BANK_DETAILS_CHANGED",
                severity="CRITICAL",
                action="HOLD",
                message="Bank details changed.",
                evidence={},
            )
        )
        db.add(invoice)
        db.commit()
        invoice_id = invoice.id

    monkeypatch.setattr(
        reset_demo_invoice,
        "SessionLocal",
        lambda: Session(engine),
    )

    with pytest.raises(ValueError, match="non-demo"):
        reset_demo_invoice.reset_demo_invoice(invoice_id)

    with Session(engine) as db:
        assert db.get(Invoice, invoice_id).approval_status == "APPROVED"

    Base.metadata.drop_all(engine)
    engine.dispose()
