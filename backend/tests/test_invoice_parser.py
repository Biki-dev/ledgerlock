from decimal import Decimal

from services.invoice_parser import parse_invoice_text


SAMPLE_INVOICE = """
ABC Industrial Supplies

Vendor Name: ABC Industrial Supplies

Invoice No: INV-2026-001

Invoice Date: 12/11/2026

GSTIN: 27AAAAA0000A1Z5

Bank Account: 900000000001

IFSC: DEMO0000001

Description       Qty       Unit Price       Amount

Steel Rod         100       100.00           10000.00

Subtotal: 10000.00

Tax: 1800.00

Grand Total: 11800.00
"""


def test_vendor_extraction():

    result = parse_invoice_text(SAMPLE_INVOICE)

    assert result["vendor_name"] == "ABC Industrial Supplies"


def test_invoice_number():

    result = parse_invoice_text(SAMPLE_INVOICE)

    assert result["invoice_number"] == "INV-2026-001"


def test_invoice_number_and_date_on_following_lines():

    text = """
    ABC Industrial Supplies
    Invoice
    INV-2026-001
    Date
    12/11/2026
    """

    result = parse_invoice_text(text)

    assert result["invoice_number"] == "INV-2026-001"
    assert result["invoice_date"].isoformat() == "2026-11-12"


def test_bank_extraction():

    result = parse_invoice_text(SAMPLE_INVOICE)

    assert result["bank_account"] == "900000000001"

    assert result["ifsc"] == "DEMO0000001"


def test_amount_extraction():

    result = parse_invoice_text(SAMPLE_INVOICE)

    assert result["subtotal"] == Decimal("10000.00")

    assert result["tax"] == Decimal("1800.00")

    assert result["total"] == Decimal("11800.00")


def test_item_extraction():

    result = parse_invoice_text(SAMPLE_INVOICE)

    assert len(result["items"]) == 1

    assert result["items"][0]["description"] == "Steel Rod"