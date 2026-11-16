from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RiskFindingOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int

    invoice_id: int

    rule_code: str

    severity: str

    action: str

    message: str

    evidence: dict

    created_at: datetime


class InvoiceRiskOut(BaseModel):

    invoice_id: int

    risk_status: str

    risk_score: int

    findings: list[RiskFindingOut] = Field(
        default_factory=list
    )

class InvoiceItemOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class InvoiceOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)
    
    risk_status: str

    risk_score: int

    risk_findings: list[RiskFindingOut] = Field(
        default_factory=list
    )

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
    approval_status: str

    review_status: str

    reviewed_by_id: int | None

    reviewed_at: datetime | None

    review_note: str | None

    verification_status: str

    verified_by_id: int | None

    verified_at: datetime | None

    verification_method: str | None

    verification_reference: str | None

    verification_note: str | None

    approved_by_id: int | None

    approved_at: datetime | None

    rejected_by_id: int | None

    rejected_at: datetime | None

    rejection_reason: str | None

    extraction_warning: str | None

    uploaded_at: datetime

    items: list[InvoiceItemOut] = Field(
        default_factory=list
    )