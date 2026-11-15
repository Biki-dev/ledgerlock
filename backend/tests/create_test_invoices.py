from pathlib import Path
import fitz


OUTPUT = Path("tests/generated")
OUTPUT.mkdir(parents=True, exist_ok=True)


def create_invoice(
    filename,
    invoice_number,
    bank_account,
    unit_price
):

    quantity = 10

    subtotal = quantity * unit_price

    tax = subtotal * 0.18

    total = subtotal + tax

    lines = [
        "ABC Industrial Supplies",
        "Invoice No: " + invoice_number,
        "Invoice Date: 15/11/2026",
        "GSTIN: 27AAAAA0000A1Z5",
        "Bank Account: " + bank_account,
        "IFSC: DEMO0000001",
        "",
        "Description       Qty       Unit Price       Amount",
        (
            f"Steel Rod       {quantity}       "
            f"{unit_price:.2f}       {subtotal:.2f}"
        ),
        "",
        f"Subtotal: {subtotal:.2f}",
        f"Tax: {tax:.2f}",
        f"Grand Total: {total:.2f}"
    ]

    document = fitz.open()

    page = document.new_page()

    y = 60

    for line in lines:

        page.insert_text(
            (60, y),
            line,
            fontsize=10
        )

        y += 24

    document.save(OUTPUT / filename)

    document.close()

    print("Created:", filename)


# 1. Normal invoice.

create_invoice(
    "normal.pdf",
    "TEST-001",
    "900000000001",
    100.00
)


# 2. Altered bank account.

create_invoice(
    "bank_changed.pdf",
    "TEST-002",
    "900000000999",
    100.00
)


# 3. Inflated product price.

create_invoice(
    "price_inflated.pdf",
    "TEST-003",
    "900000000001",
    140.00
)


# 4. Separate invoice for duplicate test.

create_invoice(
    "duplicate_test.pdf",
    "TEST-004",
    "900000000001",
    100.00
)