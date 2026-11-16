from datetime import timezone

from models.invoice import Invoice


class ApprovalBlocked(Exception):
    pass


def check_approval_eligibility(
    invoice: Invoice,
    approver_id: int
):

    # 1. Invoice must be pending.

    if invoice.approval_status != "PENDING":

        raise ApprovalBlocked(
            "Invoice has already been approved or rejected."
        )

    # 2. Risk analysis must have completed.

    if invoice.risk_status == "PENDING":

        raise ApprovalBlocked(
            "Invoice has not completed risk analysis."
        )

    # 3. CLEAR invoice.

    if invoice.risk_status == "CLEAR":

        if invoice.risk_findings:

            raise ApprovalBlocked(
                "Risk findings are present; invoice analysis must be rerun."
            )

        return True

    # 4. REVIEW invoice.

    if invoice.risk_status == "REVIEW":

        if any(
            finding.action == "HOLD"
            for finding in invoice.risk_findings
        ):

            raise ApprovalBlocked(
                "A blocking risk finding must be resolved before approval."
            )

        if invoice.review_status != "CLEARED":

            raise ApprovalBlocked(
                "Invoice requires reviewer clearance."
            )

        reviewed_at = invoice.reviewed_at

        if reviewed_at is None:

            raise ApprovalBlocked(
                "Reviewer clearance timestamp is missing."
            )

        if reviewed_at.tzinfo is None:
            reviewed_at = reviewed_at.replace(tzinfo=timezone.utc)

        for finding in invoice.risk_findings:

            created_at = finding.created_at

            if created_at is None:
                raise ApprovalBlocked(
                    "A risk finding has no creation timestamp."
                )

            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            if created_at > reviewed_at:
                raise ApprovalBlocked(
                    "Risk findings changed after reviewer clearance."
                )

        if invoice.reviewed_by_id == approver_id:

            raise ApprovalBlocked(
                "Reviewer cannot approve their own review."
            )

        return True

    # 5. HOLD invoice.

    if invoice.risk_status == "HOLD":

        hold_findings = [
            finding
            for finding in invoice.risk_findings
            if finding.action == "HOLD"
        ]

        hold_codes = {
            finding.rule_code
            for finding in hold_findings
        }

        # Only a pure bank-change HOLD can use this exception.
        # Duplicate HOLDs cannot be released through this workflow.

        if (
            hold_codes != {"BANK_DETAILS_CHANGED"}
            or len(invoice.risk_findings) != 1
        ):

            raise ApprovalBlocked(
                "This HOLD cannot be released through the bank verification workflow."
            )

        if invoice.verification_status != "VERIFIED":

            raise ApprovalBlocked(
                "Independent bank verification is required."
            )

        if invoice.verified_by_id == approver_id:

            raise ApprovalBlocked(
                "The person who verified bank details cannot approve the invoice."
            )

        return True

    raise ApprovalBlocked(
        "Unknown or invalid invoice risk status."
    )