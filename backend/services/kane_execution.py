import shutil
import subprocess

from pathlib import Path

from datetime import datetime, timezone

from database import SessionLocal

from models.assurance_run import AssuranceRun

from services.kane_runner import (
    SCENARIOS,
    KANE_BASE_URL,
    get_kane_variables_file,
    get_approver_password,
)

from services.kane_parser import parse_kane_output


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def redact_kane_output(output, secret):

    if not output or not secret:
        output = output or ""

    if isinstance(output, bytes):
        output = output.decode("utf-8", errors="replace")

    if not secret:
        return output

    return output.replace(secret, "[REDACTED]")


def find_evidence_pack(session_dir):

    if not session_dir:
        return None

    directory = Path(
        session_dir
    ).expanduser() / "evidence"

    if not directory.exists():
        return None

    packs = sorted(directory.rglob("*.evidence"))

    if packs:
        return str(packs[0])

    return None


def execute_kane_run(run_id: int):

    db = SessionLocal()
    kane_variables_directory = None

    try:

        run = db.get(
            AssuranceRun,
            run_id
        )

        if not run:
            return

        # Mark run as active.

        run.status = "RUNNING"

        run.started_at = datetime.now(timezone.utc)

        db.commit()

        kane_binary = shutil.which("kane-cli")

        if not kane_binary:

            run.status = "ERROR"

            run.reason = (
                "kane-cli executable not found in PATH"
            )

            run.completed_at = datetime.now(timezone.utc)

            db.commit()

            return

        scenario = SCENARIOS.get(
            run.scenario_code
        )

        if not scenario:

            run.status = "ERROR"

            run.reason = "Unknown Kane scenario"

            run.completed_at = datetime.now(timezone.utc)

            db.commit()

            return

        objective = run.objective
        kane_variables_directory, variables_path = (
            get_kane_variables_file()
        )

        command = [

            kane_binary,

            "run",

            objective,

            "--url",
            KANE_BASE_URL,

            "--agent",

            "--max-steps",
            "30",

            "--timeout",
            "180",

            "--variables-file",
            variables_path

        ]

        # Execute Kane.

        try:

            process = subprocess.run(

                command,

                cwd=PROJECT_ROOT,

                capture_output=True,

                text=True,

                timeout=300,

                check=False

            )

        except subprocess.TimeoutExpired as exc:

            approver_password = get_approver_password()
            stdout = redact_kane_output(
                exc.stdout,
                approver_password
            )
            stderr = redact_kane_output(
                exc.stderr,
                approver_password
            )
            parsed = parse_kane_output(stdout)
            result = parsed["run_end"] or {}

            run.raw_output = stdout[-200000:]
            run.stderr_output = stderr[-30000:]
            run.step_events = parsed["steps"][-100:]
            run.kane_status = result.get("status")
            run.summary = result.get("summary")
            run.reason = (
                "Kane subprocess timed out; its result is not considered "
                "verified. "
                + (result.get("reason") or "")
            )
            run.duration_seconds = result.get("duration")
            run.test_url = result.get("test_url")
            run.session_dir = result.get("session_dir")
            run.evidence_path = find_evidence_pack(
                run.session_dir
            )
            run.status = "ERROR"
            run.completed_at = datetime.now(timezone.utc)

            db.commit()

            return

        approver_password = get_approver_password()

        stdout = redact_kane_output(
            process.stdout,
            approver_password
        )

        stderr = redact_kane_output(
            process.stderr,
            approver_password
        )

        # Parse Kane output.

        parsed = parse_kane_output(stdout)

        result = parsed["run_end"]

        run.exit_code = process.returncode

        run.raw_output = stdout[-200000:]

        run.stderr_output = stderr[-30000:]

        run.step_events = parsed["steps"][-100:]

        if not result:

            run.status = "ERROR"

            run.reason = (
                "Kane did not produce a run_end event. "
                "Check exit code and stderr."
            )

            run.completed_at = datetime.now(timezone.utc)

            db.commit()

            return

        # Store final result.

        run.kane_status = result.get("status")

        run.summary = result.get("summary")

        run.reason = result.get("reason")

        run.duration_seconds = result.get("duration")

        run.credits_consumed = result.get(
            "credits_consumed",
            result.get("credits")
        )

        run.test_url = result.get("test_url")

        run.session_dir = result.get("session_dir")

        run.evidence_path = find_evidence_pack(
            run.session_dir
        )

        # Determine overall result.

        if (
            process.returncode == 0
            and result.get("status") == "passed"
        ):

            run.status = "PASSED"

        elif (
            process.returncode == 1
            or result.get("status") == "failed"
        ):

            run.status = "FAILED"

        else:

            run.status = "ERROR"

        run.completed_at = datetime.now(timezone.utc)

        if run.status == "PASSED" and run.retest_of_run_id:

            previous_run = db.get(
                AssuranceRun,
                run.retest_of_run_id
            )

            if previous_run:
                previous_run.agent_status = "COMPLETED"

        db.commit()

    except Exception as exc:

        db.rollback()

        run = db.get(
            AssuranceRun,
            run_id
        )

        if run:

            run.status = "ERROR"

            run.reason = str(exc)[:2000]

            run.completed_at = datetime.now(timezone.utc)

            db.commit()

    finally:

        if kane_variables_directory:
            kane_variables_directory.cleanup()

        db.close()