from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    BackgroundTasks
)

from sqlalchemy.orm import Session

from sqlalchemy import select, desc, func

from database import get_db

from models.assurance_run import AssuranceRun

from models.invoice import Invoice

from models.user import User

from schemas.assurance import (
    AssuranceRunCreate,
    AssuranceRunOut,
    AssuranceRunListOut
)

from core.dependencies import require_roles

from services.kane_runner import SCENARIOS

from services.kane_execution import execute_kane_run


router = APIRouter(
    prefix="/api/assurance",
    tags=["Kane Assurance"]
)


def validate_invoice_for_scenario(
    invoice,
    scenario_code
):

    scenario = SCENARIOS.get(scenario_code)

    if not scenario:
        raise HTTPException(400, "Unknown scenario")

    if invoice.approval_status != "PENDING":

        raise HTTPException(
            409,
            "Only pending invoices can be tested."
        )

    if invoice.risk_status != scenario["risk_status"]:

        raise HTTPException(
            409,
            f"Scenario requires risk status {scenario['risk_status']}."
        )

    finding_codes = {
        finding.rule_code
        for finding in invoice.risk_findings
    }

    if scenario_code == "bank_change_approval_guard":

        if (
            finding_codes != {"BANK_DETAILS_CHANGED"}
            or len(invoice.risk_findings) != 1
            or invoice.verification_status != "PENDING"
        ):

            raise HTTPException(
                409,
                "Invoice must have an unverified bank-change finding."
            )

    if scenario_code == "duplicate_approval_guard":

        if finding_codes.isdisjoint(
            {"EXACT_FILE_DUPLICATE", "DUPLICATE_INVOICE_NUMBER"}
        ):

            raise HTTPException(
                409,
                "Invoice must contain a duplicate HOLD finding."
            )

    if scenario_code == "review_clearance_guard":

        if invoice.review_status != "PENDING":

            raise HTTPException(
                409,
                "Invoice must have pending reviewer clearance."
            )

    return scenario


# ------------------------------------------
# GET SCENARIOS
# ------------------------------------------

@router.get("/scenarios")
def get_scenarios(

    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "FINANCE_APPROVER",
            "ADMIN"
        )
    )

):

    return [

        {
            "code": code,

            "title": data["title"],

            "description": data["description"],

            "required_risk_status": data["risk_status"]

        }

        for code, data in SCENARIOS.items()

    ]


# ------------------------------------------
# START KANE RUN
# ------------------------------------------

@router.post(
    "/runs",
    status_code=202,
    response_model=AssuranceRunOut
)
def create_assurance_run(

    payload: AssuranceRunCreate,

    background_tasks: BackgroundTasks,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "FINANCE_APPROVER",
            "ADMIN"
        )
    )

):

    # Do not allow concurrent runs.

    running = db.scalar(
        select(AssuranceRun).where(
            AssuranceRun.status.in_(
                ["QUEUED", "RUNNING"]
            )
        ).limit(1)
    )

    if running:

        raise HTTPException(
            409,
            "Another Kane run is currently active."
        )

    invoice = db.get(
        Invoice,
        payload.invoice_id
    )

    if not invoice:

        raise HTTPException(
            404,
            "Invoice not found"
        )

    scenario = validate_invoice_for_scenario(
        invoice,
        payload.scenario_code
    )

    previous_run = None

    # Validate retest relationship.

    if payload.retest_of_run_id is not None:

        previous_run = db.get(
            AssuranceRun,
            payload.retest_of_run_id
        )

        if not previous_run:

            raise HTTPException(
                404,
                "Previous run not found"
            )

        if (
            previous_run.status != "FAILED"
            or previous_run.invoice_id != invoice.id
            or previous_run.scenario_code != payload.scenario_code
        ):

            raise HTTPException(
                409,
                "Retest must reuse the same failed scenario and invoice."
            )

    objective = scenario["objective"](
        invoice.id
    )

    run = AssuranceRun(

        invoice_id=invoice.id,

        created_by_id=current_user.id,

        scenario_code=payload.scenario_code,

        scenario_title=scenario["title"],

        objective=objective,

        status="QUEUED",

        agent_status="NOT_STARTED",

        retest_of_run_id=(
            previous_run.id
            if previous_run
            else None
        )

    )

    db.add(run)

    db.commit()

    db.refresh(run)

    # Run Kane after returning the HTTP response.

    background_tasks.add_task(
        execute_kane_run,
        run.id
    )

    return run


# ------------------------------------------
# GET RUN HISTORY
# ------------------------------------------

@router.get(
    "/runs",
    response_model=AssuranceRunListOut
)
def get_assurance_runs(

    limit: int = 50,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "FINANCE_APPROVER",
            "ADMIN"
        )
    )

):

    limit = max(1, min(limit, 200))

    total = db.scalar(
        select(func.count(AssuranceRun.id))
    ) or 0

    runs = db.scalars(
        select(AssuranceRun)
        .order_by(desc(AssuranceRun.created_at))
        .limit(limit)
    ).all()

    return {
        "runs": runs,
        "total": total
    }


# ------------------------------------------
# GET ONE RUN
# ------------------------------------------

@router.get(
    "/runs/{run_id}",
    response_model=AssuranceRunOut
)
def get_assurance_run(

    run_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_roles(
            "FINANCE_REVIEWER",
            "FINANCE_APPROVER",
            "ADMIN"
        )
    )

):

    run = db.get(
        AssuranceRun,
        run_id
    )

    if not run:

        raise HTTPException(
            404,
            "Kane run not found"
        )

    return run