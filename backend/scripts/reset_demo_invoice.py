import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import SessionLocal
from models.invoice import Invoice


def reset_demo_invoice(invoice_id: int) -> None:
    db = SessionLocal()

    try:
        invoice = db.get(Invoice, invoice_id)

        if not invoice:
            raise ValueError("Invoice not found.")

        if not invoice.source_filename.startswith("DEMO_"):
            raise ValueError(
                "Refusing to reset a non-demo invoice."
            )

        hold_findings = [
            finding
            for finding in invoice.risk_findings
            if finding.action == "HOLD"
        ]
        hold_codes = {finding.rule_code for finding in hold_findings}

        if (
            invoice.risk_status != "HOLD"
            or hold_codes != {"BANK_DETAILS_CHANGED"}
            or len(invoice.risk_findings) != 1
        ):
            raise ValueError(
                "Only a synthetic invoice with a sole bank-change HOLD "
                "can be reset."
            )

        invoice.approval_status = "PENDING"
        invoice.approved_by_id = None
        invoice.approved_at = None
        invoice.rejected_by_id = None
        invoice.rejected_at = None
        invoice.rejection_reason = None
        invoice.review_status = "NOT_REQUIRED"
        invoice.reviewed_by_id = None
        invoice.reviewed_at = None
        invoice.review_note = None
        invoice.verification_status = "PENDING"
        invoice.verified_by_id = None
        invoice.verified_at = None
        invoice.verification_method = None
        invoice.verification_reference = None
        invoice.verification_note = None

        db.commit()
        print(
            f"Reset synthetic invoice {invoice_id}; risk findings and "
            "audit history were preserved."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reset a synthetic bank-change invoice for a Kane retest."
    )
    parser.add_argument("invoice_id", type=int)
    args = parser.parse_args()

    try:
        reset_demo_invoice(args.invoice_id)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
