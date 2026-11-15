from decimal import Decimal
from statistics import median

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.invoice import Invoice, InvoiceItem


MIN_HISTORY = 3

SIMILARITY_THRESHOLD = 85

INFLATION_THRESHOLD = Decimal("0.30")


def normalize_description(value):

    return " ".join(
        value.lower().split()
    )


def detect_price_anomalies(
    db: Session,
    invoice: Invoice
):

    findings = []

    if not invoice.vendor_id:
        return findings

    # Fetch historical items from the same vendor.

    history = db.execute(
        select(InvoiceItem, Invoice)
        .join(
            Invoice,
            Invoice.id == InvoiceItem.invoice_id
        )
        .where(
            Invoice.vendor_id == invoice.vendor_id,
            Invoice.id != invoice.id
        )
    ).all()

    historical_items = [
        item for item, old_invoice in history
    ]

    for current_item in invoice.items:

        current_description = normalize_description(
            current_item.description
        )

        matching_prices = []

        for old_item in historical_items:

            old_description = normalize_description(
                old_item.description
            )

            similarity = fuzz.token_set_ratio(
                current_description,
                old_description
            )

            if similarity >= SIMILARITY_THRESHOLD:

                matching_prices.append({
                    "price": Decimal(str(old_item.unit_price)),
                    "description": old_item.description,
                    "invoice_id": old_item.invoice_id,
                    "similarity": similarity
                })

        # Not enough history to establish a baseline.

        if len(matching_prices) < MIN_HISTORY:
            continue

        prices = [
            item["price"]
            for item in matching_prices
        ]

        historical_median = median(prices)

        current_price = Decimal(
            str(current_item.unit_price)
        )

        if historical_median <= 0:
            continue

        increase = (
            current_price - historical_median
        ) / historical_median

        if increase >= INFLATION_THRESHOLD:

            percentage = (
                increase * Decimal("100")
            ).quantize(Decimal("0.01"))

            findings.append({

                "rule_code": "PRICE_INFLATION",

                "severity": "MEDIUM",

                "action": "REVIEW",

                "message": (
                    f"{current_item.description} is "
                    f"{percentage}% above its historical median."
                ),

                "evidence": {

                    "product": current_item.description,

                    "current_price": str(current_price),

                    "historical_median": str(historical_median),

                    "increase_percentage": str(percentage),

                    "history_count": len(matching_prices),

                    "historical_prices": [
                        str(price)
                        for price in prices
                    ]
                }
            })

    return findings