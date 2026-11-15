import re

from decimal import Decimal
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.invoice import Invoice


def normalize(value):

    if not value:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


def same_vendor(current, previous):

    if (
        current.vendor_id
        and previous.vendor_id
        and current.vendor_id == previous.vendor_id
    ):
        return True

    if current.gstin and previous.gstin:

        if normalize(current.gstin) == normalize(previous.gstin):
            return True

    if current.vendor_name and previous.vendor_name:

        return (
            normalize(current.vendor_name)
            == normalize(previous.vendor_name)
        )

    return False


def amount_is_similar(a, b):

    if a is None or b is None:
        return False

    a = Decimal(str(a))
    b = Decimal(str(b))

    tolerance = max(
        Decimal("1.00"),
        max(abs(a), abs(b)) * Decimal("0.01")
    )

    return abs(a - b) <= tolerance


def dates_are_close(a, b):

    if not a or not b:
        return True

    return abs((a - b).days) <= 60


def detect_duplicates(
    db: Session,
    invoice: Invoice
):

    findings = []

    # 1. Exact PDF duplicate using SHA256

    exact_file = db.scalar(
        select(Invoice).where(
            Invoice.sha256 == invoice.sha256,
            Invoice.id != invoice.id
        ).limit(1)
    )

    if exact_file:

        findings.append({
            "rule_code": "EXACT_FILE_DUPLICATE",
            "severity": "CRITICAL",
            "action": "HOLD",
            "message": "An identical PDF has already been uploaded.",
            "evidence": {
                "matched_invoice_id": exact_file.id,
                "sha256": invoice.sha256
            }
        })

        return findings

    # 2. Compare with previous extracted invoices

    previous_invoices = db.scalars(
        select(Invoice).where(
            Invoice.id != invoice.id,
            Invoice.extraction_status == "EXTRACTED"
        )
    ).all()

    for previous in previous_invoices:

        if not same_vendor(invoice, previous):
            continue

        current_number = normalize(invoice.invoice_number)
        previous_number = normalize(previous.invoice_number)

        if not current_number or not previous_number:
            continue

        # Exact invoice number

        if current_number == previous_number:

            findings.append({
                "rule_code": "DUPLICATE_INVOICE_NUMBER",
                "severity": "HIGH",
                "action": "HOLD",
                "message": "This vendor invoice number already exists.",
                "evidence": {
                    "matched_invoice_id": previous.id,
                    "invoice_number": invoice.invoice_number,
                    "previous_total": str(previous.total),
                    "current_total": str(invoice.total)
                }
            })

            break

        # Near duplicate invoice number

        similarity = fuzz.ratio(
            current_number,
            previous_number
        )

        if (
            similarity >= 92
            and amount_is_similar(
                invoice.total,
                previous.total
            )
            and dates_are_close(
                invoice.invoice_date,
                previous.invoice_date
            )
        ):

            findings.append({
                "rule_code": "POSSIBLE_DUPLICATE",
                "severity": "MEDIUM",
                "action": "REVIEW",
                "message": "Invoice number resembles a previous invoice.",
                "evidence": {
                    "matched_invoice_id": previous.id,
                    "current_number": invoice.invoice_number,
                    "previous_number": previous.invoice_number,
                    "number_similarity": similarity,
                    "current_total": str(invoice.total),
                    "previous_total": str(previous.total)
                }
            })

            break

    return findings