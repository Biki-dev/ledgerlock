import runpy
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from models.vendor import Vendor
from services.invoice_parser import parse_invoice_text
from services.vendor_service import resolve_vendor


def test_generated_bank_change_invoice_matches_synthetic_vendor(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runpy.run_path(
        str(Path(__file__).parents[1] / "tests/create_test_invoices.py")
    )

    generated_pdf = tmp_path / "tests/generated/bank_changed.pdf"
    assert generated_pdf.is_file()

    import fitz

    with fitz.open(generated_pdf) as document:
        text = "\n".join(page.get_text("text") for page in document)

    parsed = parse_invoice_text(text)
    assert parsed["gstin"] == "27AAAAA0000A1Z5"

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
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

        matched = resolve_vendor(
            db,
            parsed["vendor_name"],
            parsed["gstin"],
        )

        assert matched.id == vendor.id
        assert matched.bank_account == "900000000001"

    engine.dispose()
