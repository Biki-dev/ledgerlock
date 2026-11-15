from decimal import Decimal

from models.invoice import Invoice


TOLERANCE = Decimal("1.00")


def detect_arithmetic_errors(invoice: Invoice):

    findings = []

    # 1. Verify every line item.

    for item in invoice.items:

        expected = (
            Decimal(str(item.quantity))
            * Decimal(str(item.unit_price))
        )

        actual = Decimal(str(item.line_total))

        if abs(expected - actual) > Decimal("0.05"):

            findings.append({

                "rule_code": "LINE_TOTAL_MISMATCH",

                "severity": "MEDIUM",

                "action": "REVIEW",

                "message": (
                    f"Line total does not match quantity × unit price "
                    f"for {item.description}."
                ),

                "evidence": {

                    "description": item.description,

                    "quantity": str(item.quantity),

                    "unit_price": str(item.unit_price),

                    "expected_total": str(expected),

                    "invoice_line_total": str(actual)
                }
            })

    # 2. Compare item totals with subtotal.

    if invoice.items and invoice.subtotal is not None:

        calculated_subtotal = sum(
            (
                Decimal(str(item.line_total))
                for item in invoice.items
            ),
            Decimal("0")
        )

        subtotal = Decimal(str(invoice.subtotal))

        if abs(calculated_subtotal - subtotal) > TOLERANCE:

            findings.append({

                "rule_code": "SUBTOTAL_MISMATCH",

                "severity": "MEDIUM",

                "action": "REVIEW",

                "message": "Line-item sum differs from the invoice subtotal.",

                "evidence": {

                    "calculated_subtotal": str(calculated_subtotal),

                    "invoice_subtotal": str(subtotal)
                }
            })

    # 3. Check subtotal + tax.

    if (
        invoice.subtotal is not None
        and invoice.tax is not None
        and invoice.total is not None
    ):

        expected_total = (
            Decimal(str(invoice.subtotal))
            + Decimal(str(invoice.tax))
        )

        actual_total = Decimal(str(invoice.total))

        if abs(expected_total - actual_total) > TOLERANCE:

            findings.append({

                "rule_code": "GRAND_TOTAL_MISMATCH",

                "severity": "MEDIUM",

                "action": "REVIEW",

                "message": "Subtotal plus tax does not match the invoice total.",

                "evidence": {

                    "expected_total": str(expected_total),

                    "invoice_total": str(actual_total)
                }
            })

    return findings