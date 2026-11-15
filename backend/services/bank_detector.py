import re

from models.vendor import Vendor
from models.invoice import Invoice


def normalize_account(value):

    if not value:
        return ""

    return re.sub(r"\D", "", value)


def normalize_ifsc(value):

    if not value:
        return ""

    return re.sub(
        r"\s+",
        "",
        value
    ).upper()


def mask_account(value):

    digits = normalize_account(value)

    if not digits:
        return None

    return f"****{digits[-4:]}"


def detect_bank_changes(
    invoice: Invoice,
    vendor: Vendor | None
):

    findings = []

    # No matched vendor

    if not vendor:

        findings.append({
            "rule_code": "VENDOR_NOT_LINKED",
            "severity": "MEDIUM",
            "action": "REVIEW",
            "message": "Invoice is not linked to a known vendor.",
            "evidence": {}
        })

        return findings

    # Vendor not verified

    if not vendor.is_verified:

        findings.append({
            "rule_code": "UNVERIFIED_VENDOR",
            "severity": "MEDIUM",
            "action": "REVIEW",
            "message": "Vendor identity or payment details have not been verified.",
            "evidence": {
                "vendor_id": vendor.id
            }
        })

        return findings

    # Verified vendor without stored bank profile

    if not vendor.bank_account:

        findings.append({
            "rule_code": "BANK_PROFILE_MISSING",
            "severity": "MEDIUM",
            "action": "REVIEW",
            "message": "Verified vendor has no trusted bank account on record.",
            "evidence": {}
        })

        return findings

    expected_account = normalize_account(
        vendor.bank_account
    )

    actual_account = normalize_account(
        invoice.bank_account
    )

    expected_ifsc = normalize_ifsc(vendor.ifsc)

    actual_ifsc = normalize_ifsc(invoice.ifsc)

    changes = []

    if not actual_account:

        findings.append({
            "rule_code": "BANK_ACCOUNT_MISSING",
            "severity": "MEDIUM",
            "action": "REVIEW",
            "message": "Invoice bank account could not be extracted.",
            "evidence": {}
        })

    elif actual_account != expected_account:

        changes.append("bank_account")

    if expected_ifsc:

        if not actual_ifsc:

            findings.append({
                "rule_code": "IFSC_MISSING",
                "severity": "MEDIUM",
                "action": "REVIEW",
                "message": "Invoice IFSC could not be extracted.",
                "evidence": {}
            })

        elif actual_ifsc != expected_ifsc:

            changes.append("ifsc")

    if changes:

        findings.append({
            "rule_code": "BANK_DETAILS_CHANGED",
            "severity": "CRITICAL",
            "action": "HOLD",
            "message": "Invoice payment details differ from the verified vendor profile.",
            "evidence": {
                "changed_fields": changes,
                "expected_account": mask_account(expected_account),
                "invoice_account": mask_account(actual_account),
                "expected_ifsc": expected_ifsc,
                "invoice_ifsc": actual_ifsc
            }
        })

    return findings