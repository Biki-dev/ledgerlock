from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class AssuranceRun(Base):

    __tablename__ = "assurance_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False,
        index=True
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    # Scenario information

    scenario_code: Mapped[str] = mapped_column(
        String(80),
        nullable=False
    )

    scenario_title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    objective: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Run lifecycle

    status: Mapped[str] = mapped_column(
        String(20),
        default="QUEUED",
        nullable=False
    )

    exit_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    kane_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    credits_consumed: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    # Kane references

    test_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    session_dir: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    evidence_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Kane outputs

    step_events: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    raw_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    stderr_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Agent feedback

    agent_status: Mapped[str] = mapped_column(
        String(30),
        default="NOT_STARTED",
        nullable=False
    )

    agent_feedback_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    agent_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Link before and after runs

    retest_of_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("assurance_runs.id"),
        nullable=True
    )

    # Timestamps

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )