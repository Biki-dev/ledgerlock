from typing import Literal

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ReviewRequest(BaseModel):

    decision: Literal[
        "CLEAR_FOR_APPROVAL",
        "REJECT"
    ]

    note: str = Field(
        min_length=10,
        max_length=1000
    )


class BankVerificationRequest(BaseModel):

    method: Literal[
        "PHONE_TO_KNOWN_CONTACT",
        "VERIFIED_VENDOR_PORTAL",
        "IN_PERSON"
    ]

    reference: str = Field(
        min_length=3,
        max_length=255
    )

    note: str = Field(
        min_length=10,
        max_length=1000
    )


class RejectRequest(BaseModel):

    reason: str = Field(
        min_length=10,
        max_length=1000
    )


class AuditEventOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int

    invoice_id: int | None

    actor_id: int | None

    action: str

    outcome: str

    details: dict

    created_at: datetime