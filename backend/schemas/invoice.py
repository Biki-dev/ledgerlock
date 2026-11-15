from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceItemOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class InvoiceOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int | None

    vendor_name: str | None
    invoice_number: str | None
    invoice_date: date | None

    gstin: str | None
    bank_account: str | None
    ifsc: str | None

    subtotal: Decimal | None
    tax: Decimal | None
    total: Decimal | None

    source_filename: str

    extraction_method: str
    extraction_status: str
    extraction_confidence: float

    field_confidence: dict

    extraction_warning: str | None

    uploaded_at: datetime

    items: list[InvoiceItemOut] = Field(
        default_factory=list
    )