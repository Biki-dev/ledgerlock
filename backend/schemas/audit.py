from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GlobalAuditEventOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int | None
    invoice_number: str | None
    actor_id: int | None
    actor_name: str
    action: str
    outcome: str
    details: dict
    created_at: datetime