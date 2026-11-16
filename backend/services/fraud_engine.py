from sqlalchemy.orm import Session

from models.invoice import Invoice
from models.vendor import Vendor
from models.risk_finding import RiskFinding

from services.duplicate_detector import detect_duplicates
from services.bank_detector import detect_bank_changes
from services.price_detector import detect_price_anomalies
from services.arithmetic_detector import detect_arithmetic_errors


SEVERITY_WEIGHTS = {
    "CRITICAL": 100,
    "HIGH": 75,
    "MEDIUM": 35,
    "LOW": 10
}


def run_fraud_analysis(
    db: Session,
    invoice: Invoice
):

    findings = []

    # 1. Get the vendor reference.

    vendor = (
        db.get(Vendor, invoice.vendor_id)
        if invoice.vendor_id
        else None
    )

    # 2. Run duplicate detection.

    findings.extend(
        detect_duplicates(db, invoice)
    )

    # 3. Run bank-change detection.

    findings.extend(
        detect_bank_changes(invoice, vendor)
    )

    # 4. Run price anomaly detection.

    findings.extend(
        detect_price_anomalies(db, invoice)
    )

    # 5. Run arithmetic validation.

    findings.extend(
        detect_arithmetic_errors(invoice)
    )

    # 6. Check incomplete extraction.

    if invoice.extraction_status != "EXTRACTED":

        findings.append({

            "rule_code": "EXTRACTION_INCOMPLETE",

            "severity": "MEDIUM",

            "action": "REVIEW",

            "message": "Invoice extraction requires manual verification.",

            "evidence": {
                "extraction_status": invoice.extraction_status,
                "confidence": invoice.extraction_confidence
            }
        })

    # 7. Check missing critical data.

    missing_fields = []

    if not invoice.vendor_name:
        missing_fields.append("vendor_name")

    if not invoice.invoice_number:
        missing_fields.append("invoice_number")

    if invoice.total is None:
        missing_fields.append("total")

    if missing_fields:

        findings.append({

            "rule_code": "MISSING_INVOICE_FIELDS",

            "severity": "MEDIUM",

            "action": "REVIEW",

            "message": "Important invoice fields are missing.",

            "evidence": {
                "missing_fields": missing_fields
            }
        })

    # 8. Calculate heuristic risk score.

    risk_score = min(
        100,
        sum(
            SEVERITY_WEIGHTS.get(
                finding["severity"],
                0
            )
            for finding in findings
        )
    )

    # 9. Determine final status.

    if any(
        finding["action"] == "HOLD"
        for finding in findings
    ):

        risk_status = "HOLD"

    elif findings:

        risk_status = "REVIEW"

    else:

        risk_status = "CLEAR"
        
        # Do not re-analyze finalized invoices.

    if invoice.approval_status in ("APPROVED", "REJECTED"):

        raise ValueError(
            "Finalized invoices cannot be re-analyzed."
        )

    # Reset previous human review when risk analysis is rerun.

    invoice.reviewed_by_id = None
    invoice.reviewed_at = None
    invoice.review_note = None

    invoice.verified_by_id = None
    invoice.verified_at = None
    invoice.verification_method = None
    invoice.verification_reference = None
    invoice.verification_note = None

    # REVIEW workflow initialization.

    invoice.review_status = (
        "PENDING"
        if risk_status == "REVIEW"
        else "NOT_REQUIRED"
    )

    # Determine whether the only blocking condition
    # is a changed vendor bank detail.

    hold_codes = {
        finding["rule_code"]
        for finding in findings
        if finding["action"] == "HOLD"
    }

    if (
        risk_status == "HOLD"
        and hold_codes == {"BANK_DETAILS_CHANGED"}
    ):

        invoice.verification_status = "PENDING"

    else:

        invoice.verification_status = "NOT_REQUIRED"

    invoice.risk_status = risk_status

    invoice.risk_score = risk_score

    db.flush()

    # 10. Remove previous findings when re-running analysis.

    db.query(RiskFinding).filter(
        RiskFinding.invoice_id == invoice.id
    ).delete(synchronize_session=False)

    db.flush()

    # 11. Save new findings.

    for finding in findings:

        record = RiskFinding(

            invoice_id=invoice.id,

            rule_code=finding["rule_code"],

            severity=finding["severity"],

            action=finding["action"],

            message=finding["message"],

            evidence=finding["evidence"]
        )

        db.add(record)

    # 12. Update invoice.

    invoice.risk_status = risk_status

    invoice.risk_score = risk_score

    db.flush()

    return {
        "invoice_id": invoice.id,
        "risk_status": risk_status,
        "risk_score": risk_score,
        "findings": findings
    }