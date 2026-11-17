from datetime import datetime

from pydantic import BaseModel, Field


class AssuranceRunCreate(BaseModel):

    invoice_id: int

    scenario_code: str

    retest_of_run_id: int | None = None


class AssuranceScenarioOut(BaseModel):

    code: str

    title: str

    description: str

    required_risk_status: str


class AssuranceRunOut(BaseModel):

    id: int

    invoice_id: int

    scenario_code: str

    scenario_title: str

    status: str

    exit_code: int | None

    kane_status: str | None

    summary: str | None

    reason: str | None

    duration_seconds: float | None

    credits_consumed: float | None

    test_url: str | None

    session_dir: str | None

    evidence_path: str | None

    step_events: list[dict] = Field(
        default_factory=list
    )

    agent_status: str

    agent_feedback_path: str | None

    retest_of_run_id: int | None

    created_at: datetime

    started_at: datetime | None

    completed_at: datetime | None


class AssuranceRunListOut(BaseModel):

    runs: list[AssuranceRunOut]

    total: int