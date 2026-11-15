import re

from datetime import datetime, date
from decimal import Decimal, InvalidOperation


GSTIN_PATTERN = re.compile(
    r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b",
    re.IGNORECASE
)

IFSC_PATTERN = re.compile(
    r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    re.IGNORECASE
)


def normalize_text(text: str) -> str:

    text = text.replace("\t", "    ")

    return text.strip()


def parse_decimal(value: str | None):

    if not value:
        return None

    cleaned = re.sub(
        r"[₹,\s]|INR",
        "",
        value,
        flags=re.IGNORECASE
    )

    try:
        return Decimal(cleaned)

    except InvalidOperation:
        return None


def find_labeled_value(text, labels):

    pattern = (
        r"(?im)^\s*(?:"
        + labels
        + r")\s*[:#-]\s*(.*?)\s*$"
    )

    match = re.search(pattern, text)

    return match.group(1).strip() if match else None


def find_money(text, labels):

    pattern = (
        r"(?im)^\s*(?:"
        + labels
        + r")\s*[:#-]?\s*(?:₹|INR)?\s*"
        r"([0-9][0-9,]*(?:\.\d{1,2})?)"
        r"\s*$"
    )

    match = re.search(pattern, text)

    if not match:
        return None

    return parse_decimal(match.group(1))


def parse_date(value):

    if not value:
        return None

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d %b %Y",
        "%d %B %Y"
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                value.strip(),
                fmt
            ).date()

        except ValueError:
            continue

    return None


def parse_bank_account(text):

    pattern = (
        r"(?im)^\s*(?:Bank\s+)?"
        r"(?:A/C|Account)"
        r"(?:\s*(?:No\.?|Number))?"
        r"\s*[:#-]\s*([0-9][0-9 -]{7,22})\s*$"
    )

    match = re.search(pattern, text)

    if match:
        return re.sub(r"\s|-", "", match.group(1))

    return None


def parse_invoice_items(text):

    items = []

    number = r"[0-9][0-9,]*(?:\.\d{1,3})?"

    pattern = re.compile(
        rf"^(?P<description>.+?)\s{{2,}}"
        rf"(?P<quantity>{number})\s+"
        rf"(?P<unit_price>{number})\s+"
        rf"(?P<line_total>{number})$"
    )

    ignored = (
        "description",
        "quantity",
        "subtotal",
        "grand total",
        "tax",
        "gst",
        "invoice total"
    )

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if any(word in line.lower() for word in ignored):
            continue

        match = pattern.match(line)

        if not match:
            continue

        item = match.groupdict()

        quantity = parse_decimal(item["quantity"])
        unit_price = parse_decimal(item["unit_price"])
        line_total = parse_decimal(item["line_total"])

        if (
            not quantity
            or unit_price is None
            or line_total is None
            or quantity <= 0
            or unit_price < 0
            or line_total < 0
        ):
            continue

        items.append({
            "description": item["description"].strip(),
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total
        })

    return items


def parse_invoice_text(raw_text: str):

    text = normalize_text(raw_text)

    vendor_name = find_labeled_value(
        text,
        r"Vendor\s*Name|Supplier(?:\s*Name)?|Seller"
    )

    invoice_number = find_labeled_value(
        text,
        r"Invoice\s*(?:No\.?|Number|#)|Bill\s*No\.?"
    )

    date_value = find_labeled_value(
        text,
        r"Invoice\s*Date|Bill\s*Date"
    )

    invoice_date = parse_date(date_value)

    gstin_match = GSTIN_PATTERN.search(text)

    gstin = (
        gstin_match.group(0).upper()
        if gstin_match else None
    )

    ifsc_match = IFSC_PATTERN.search(text)

    ifsc = (
        ifsc_match.group(0).upper()
        if ifsc_match else None
    )

    bank_account = parse_bank_account(text)

    subtotal = find_money(
        text,
        r"Sub\s*Total|Taxable\s*Value|Net\s*Amount"
    )

    tax = find_money(
        text,
        r"Total\s*Tax|Tax\s*Amount|GST\s*Amount|Tax"
    )

    if tax is None:

        cgst = find_money(text, r"CGST")
        sgst = find_money(text, r"SGST")
        igst = find_money(text, r"IGST")

        tax_parts = [
            value for value in [cgst, sgst, igst]
            if value is not None
        ]

        if tax_parts:
            tax = sum(tax_parts, Decimal("0"))

    total = find_money(
        text,
        r"Grand\s*Total|Invoice\s*Total|Total\s*Amount|Amount\s*Due|Total"
    )

    items = parse_invoice_items(text)

    fields = {
        "vendor_name": vendor_name,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "gstin": gstin,
        "bank_account": bank_account,
        "ifsc": ifsc,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "items": items
    }

    confidence = {
        key: (
            0.95 if value is not None and value != []
            else 0.0
        )
        for key, value in fields.items()
    }

    overall = round(
        sum(confidence.values()) / len(confidence),
        2
    )

    return {
        **fields,
        "field_confidence": confidence,
        "extraction_confidence": overall
    }