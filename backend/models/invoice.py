from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Invoice(Base):

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    vendor_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendors.id"),
        nullable=True
    )

    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    gstin: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    bank_account: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )

    ifsc: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    subtotal: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )

    tax: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )

    total: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True
    )

    source_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )

    extraction_method: Mapped[str] = mapped_column(
        String(30),
        default="TEXT"
    )

    extraction_status: Mapped[str] = mapped_column(
        String(30),
        default="NEEDS_REVIEW"
    )

    extraction_confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    field_confidence: Mapped[dict] = mapped_column(
        JSON,
        default=dict
    )

    extraction_warning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan"
    )


class InvoiceItem(Base):

    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(
        back_populates="items"
    )
