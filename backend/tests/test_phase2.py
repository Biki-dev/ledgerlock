import asyncio
from io import BytesIO
from pathlib import Path
from decimal import Decimal

import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base
from migrate_phase2 import migrate_phase2
from models.invoice import Invoice, InvoiceItem
from models.risk_finding import RiskFinding
from models.vendor import Vendor
from routes.invoices import analyze_invoice_endpoint, get_invoice_risk
from routes import invoices as invoice_routes
from schemas.invoice import InvoiceOut, InvoiceRiskOut
from services.arithmetic_detector import detect_arithmetic_errors
from services.bank_detector import detect_bank_changes
from services.fraud_engine import run_fraud_analysis
from services.price_detector import detect_price_anomalies
from services.vendor_service import resolve_vendor


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


def add_invoice(
    db,
    *,
    vendor_id,
    invoice_number,
    unit_price,
    sha256,
    bank_account="900000000001",
    ifsc="DEMO0000001",
    line_total=None,
):
    quantity = Decimal("10")
    if line_total is None:
        line_total = quantity * Decimal(str(unit_price))
    invoice = Invoice(
        vendor_id=vendor_id,
        vendor_name="ABC Industrial Supplies",
        invoice_number=invoice_number,
        bank_account=bank_account,
        ifsc=ifsc,
        subtotal=line_total,
        tax=line_total * Decimal("0.18"),
        total=line_total * Decimal("1.18"),
        source_filename=f"{invoice_number}.pdf",
        storage_path="",
        sha256=sha256,
        extraction_status="EXTRACTED",
    )
    invoice.items.append(
        InvoiceItem(
            description="Steel Rod",
            quantity=quantity,
            unit_price=Decimal(str(unit_price)),
            line_total=line_total,
        )
    )
    db.add(invoice)
    db.flush()
    return invoice


def add_verified_vendor(db):
    vendor = Vendor(
        name="ABC Industrial Supplies",
        normalized_name="abc industrial supplies",
        gstin="27AAAAA0000A1Z5",
        bank_account="900000000001",
        ifsc="DEMO0000001",
        is_verified=True,
    )
    db.add(vendor)
    db.flush()
    return vendor


def test_exactly_thirty_percent_price_increase_triggers_review(db_session):
    vendor = add_verified_vendor(db_session)

    for index in range(3):
        add_invoice(
            db_session,
            vendor_id=vendor.id,
            invoice_number=f"HIST-{index}",
            unit_price=Decimal("100.00"),
            sha256=f"history-{index}",
        )

    current = add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="CURRENT-001",
        unit_price=Decimal("130.00"),
        sha256="current",
    )

    findings = detect_price_anomalies(db_session, current)

    assert [finding["rule_code"] for finding in findings] == [
        "PRICE_INFLATION"
    ]
    assert findings[0]["action"] == "REVIEW"


def test_price_increase_waits_for_three_historical_observations(db_session):
    vendor = add_verified_vendor(db_session)
    for index in range(2):
        add_invoice(
            db_session,
            vendor_id=vendor.id,
            invoice_number=f"HIST-{index}",
            unit_price=Decimal("100.00"),
            sha256=f"history-{index}",
        )
    current = add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="CURRENT-001",
        unit_price=Decimal("140.00"),
        sha256="current",
    )

    assert detect_price_anomalies(db_session, current) == []


@pytest.mark.parametrize(
    ("bank_account", "ifsc", "changed_field"),
    [
        ("900000000999", "DEMO0000001", "bank_account"),
        ("900000000001", "DEMO0000002", "ifsc"),
    ],
)
def test_changed_verified_bank_details_trigger_hold(
    db_session,
    bank_account,
    ifsc,
    changed_field,
):
    vendor = add_verified_vendor(db_session)
    invoice = Invoice(
        vendor_id=vendor.id,
        bank_account=bank_account,
        ifsc=ifsc,
    )

    findings = detect_bank_changes(invoice, vendor)

    assert len(findings) == 1
    assert findings[0]["rule_code"] == "BANK_DETAILS_CHANGED"
    assert findings[0]["action"] == "HOLD"
    assert changed_field in findings[0]["evidence"]["changed_fields"]
    assert vendor.bank_account == "900000000001"
    assert vendor.ifsc == "DEMO0000001"


def test_resolving_vendor_never_overwrites_trusted_bank_details(db_session):
    vendor = add_verified_vendor(db_session)

    resolved = resolve_vendor(
        db_session,
        "A Different Name From The Invoice",
        vendor.gstin,
    )

    assert resolved.id == vendor.id
    assert resolved.bank_account == "900000000001"
    assert resolved.ifsc == "DEMO0000001"


def test_same_vendor_invoice_number_is_held(db_session):
    vendor = add_verified_vendor(db_session)
    add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="INV-2026-001",
        unit_price=Decimal("100.00"),
        sha256="first-file",
    )
    current = add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="INV-2026-001",
        unit_price=Decimal("100.00"),
        sha256="second-file",
    )

    result = run_fraud_analysis(db_session, current)

    assert result["risk_status"] == "HOLD"
    assert any(
        finding["rule_code"] == "DUPLICATE_INVOICE_NUMBER"
        for finding in result["findings"]
    )


def test_near_duplicate_invoice_is_flagged_for_review(db_session):
    vendor = add_verified_vendor(db_session)
    add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="INV-2026-000001",
        unit_price=Decimal("100.00"),
        sha256="first-file",
    )
    current = add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="INV-2026-000002",
        unit_price=Decimal("100.00"),
        sha256="second-file",
    )

    result = run_fraud_analysis(db_session, current)

    assert result["risk_status"] == "REVIEW"
    assert any(
        finding["rule_code"] == "POSSIBLE_DUPLICATE"
        and finding["action"] == "REVIEW"
        for finding in result["findings"]
    )


def test_four_detectors_aggregate_and_reanalysis_replaces_findings(db_session):
    vendor = add_verified_vendor(db_session)
    for index in range(3):
        add_invoice(
            db_session,
            vendor_id=vendor.id,
            invoice_number=f"HIST-{index}",
            unit_price=Decimal("100.00"),
            sha256=f"history-{index}",
        )
    add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="PREVIOUS-001",
        unit_price=Decimal("100.00"),
        sha256="duplicate-file",
    )
    current = add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="CURRENT-001",
        unit_price=Decimal("140.00"),
        sha256="duplicate-file",
        bank_account="900000000999",
        ifsc="DEMO0000002",
        line_total=Decimal("1350.00"),
    )

    result = run_fraud_analysis(db_session, current)
    rule_codes = {finding["rule_code"] for finding in result["findings"]}

    assert {
        "EXACT_FILE_DUPLICATE",
        "BANK_DETAILS_CHANGED",
        "PRICE_INFLATION",
        "LINE_TOTAL_MISMATCH",
    }.issubset(rule_codes)
    assert result["risk_status"] == "HOLD"
    assert result["risk_score"] == 100
    assert db_session.query(RiskFinding).filter_by(
        invoice_id=current.id
    ).count() == len(result["findings"])

    current.sha256 = "unique-file"
    current.bank_account = vendor.bank_account
    current.ifsc = vendor.ifsc
    current.items[0].unit_price = Decimal("100.00")
    current.items[0].line_total = Decimal("1000.00")
    current.subtotal = Decimal("1000.00")
    current.tax = Decimal("180.00")
    current.total = Decimal("1180.00")
    result = run_fraud_analysis(db_session, current)

    assert result["risk_status"] == "CLEAR"
    assert result["risk_score"] == 0
    assert result["findings"] == []
    assert db_session.query(RiskFinding).filter_by(
        invoice_id=current.id
    ).count() == 0


def test_arithmetic_detector_checks_line_subtotal_and_grand_total(db_session):
    invoice = Invoice(
        subtotal=Decimal("1000.00"),
        tax=Decimal("100.00"),
        total=Decimal("1200.00"),
    )
    invoice.items.append(
        InvoiceItem(
            description="Steel Rod",
            quantity=Decimal("10"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("900.00"),
        )
    )

    findings = detect_arithmetic_errors(invoice)

    assert {finding["rule_code"] for finding in findings} == {
        "LINE_TOTAL_MISMATCH",
        "SUBTOTAL_MISMATCH",
        "GRAND_TOTAL_MISMATCH",
    }


def test_manual_analysis_and_risk_report_endpoints(db_session):
    vendor = add_verified_vendor(db_session)
    invoice = add_invoice(
        db_session,
        vendor_id=vendor.id,
        invoice_number="API-001",
        unit_price=Decimal("100.00"),
        sha256="api-file",
    )
    db_session.flush()

    analyzed = analyze_invoice_endpoint(invoice.id, db_session)
    report = get_invoice_risk(invoice.id, db_session)
    invoice_response = InvoiceOut.model_validate(analyzed)
    risk_response = InvoiceRiskOut.model_validate(report)

    assert invoice_response.risk_status == "CLEAR"
    assert risk_response.invoice_id == invoice.id
    assert risk_response.risk_status == "CLEAR"
    assert risk_response.risk_score == 0
    assert risk_response.findings == []


def test_upload_runs_risk_analysis_automatically(
    db_session,
    monkeypatch,
    tmp_path,
):
    sample_path = Path(__file__).parents[1] / "sample_invoice.pdf"
    upload = UploadFile(
        filename="sample_invoice.pdf",
        file=BytesIO(sample_path.read_bytes()),
    )
    monkeypatch.setattr(invoice_routes, "STORAGE_DIR", tmp_path)

    invoice = asyncio.run(
        invoice_routes.upload_invoice(upload, db_session)
    )
    response = InvoiceOut.model_validate(invoice)

    assert response.risk_status != "PENDING"
    assert response.risk_score > 0
    assert any(
        finding.rule_code == "UNVERIFIED_VENDOR"
        for finding in response.risk_findings
    )


def test_migration_adds_risk_columns_without_losing_old_invoices(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE invoices (
                id INTEGER PRIMARY KEY,
                vendor_id INTEGER,
                vendor_name VARCHAR(255),
                invoice_number VARCHAR(100),
                invoice_date DATE,
                gstin VARCHAR(20),
                bank_account VARCHAR(40),
                ifsc VARCHAR(20),
                subtotal NUMERIC(14, 2),
                tax NUMERIC(14, 2),
                total NUMERIC(14, 2),
                source_filename VARCHAR(255) NOT NULL,
                storage_path VARCHAR(500) NOT NULL,
                sha256 VARCHAR(64) NOT NULL,
                extraction_method VARCHAR(30) NOT NULL,
                extraction_status VARCHAR(30) NOT NULL,
                extraction_confidence FLOAT NOT NULL,
                field_confidence JSON NOT NULL,
                extraction_warning TEXT,
                raw_text TEXT,
                uploaded_at DATETIME NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO invoices (
                id, invoice_number, source_filename, storage_path, sha256,
                extraction_method, extraction_status, extraction_confidence,
                field_confidence, uploaded_at
            ) VALUES (
                41, 'LEGACY-041', 'legacy.pdf', '', 'legacy-sha',
                'TEXT', 'EXTRACTED', 0.9, '{}', '2026-01-01 00:00:00'
            )
            """
        )

    migrate_phase2(engine)

    with Session(engine) as session:
        old_invoice = session.get(Invoice, 41)

    assert old_invoice is not None
    assert old_invoice.invoice_number == "LEGACY-041"
    assert old_invoice.risk_status == "PENDING"
    assert old_invoice.risk_score == 0
    engine.dispose()