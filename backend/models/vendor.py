from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Vendor(Base):

    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    gstin: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True
    )

    bank_account: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )

    ifsc: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
