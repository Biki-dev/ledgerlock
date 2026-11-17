import argparse
import subprocess
import shutil
import sys

from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]

BACKEND = ROOT / "backend"

sys.path.insert(0, str(BACKEND))

from database import SessionLocal

from models.assurance_run import AssuranceRun


OUTPUT_DIR = ROOT / "artifacts" / "agent-feedback"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def build_prompt(run):

    failed_steps = [

        step

        for step in (run.step_events or [])

        if step.get("status") == "failed"

    ]

    return f"""
# LedgerLock — Kane Failure Report

You are the coding agent responsible for repairing
LedgerLock.

Kane independently tested the actual application
and reported a failure.

## Run information

Run ID: {run.id}

Scenario: {run.scenario_title}

Scenario code: {run.scenario_code}

Invoice ID: {run.invoice_id}

Kane status: {run.kane_status}

Exit code: {run.exit_code}

Summary: {run.summary}

Reason: {run.reason}

## Original Kane objective

{run.objective}

## Failed execution steps

{failed_steps}

## Evidence pack

{run.evidence_path}

## Kane Test Manager link

{run.test_url}

## Your task

1. Inspect the failed execution and relevant evidence.
2. Inspect the LedgerLock source code.
3. Identify the actual root cause.
4. Fix the defect in the application.
5. Do not weaken the invoice approval rules.
6. Do not modify the original Kane scenario.
7. Do not remove or weaken assertions.
8. Preserve audit logging and separation of duties.
9. Run relevant backend tests.
10. Run the frontend production build.
11. Report the exact files changed and test results.

Do not declare the issue fixed without running the
appropriate local tests.

This is a local hackathon development environment.
Do not deploy any changes automatically.

Generated at: {datetime.now(timezone.utc).isoformat()}
"""


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "run_id",
        type=int
    )

    parser.add_argument(
        "--manual",
        action="store_true"
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:

        run = db.get(
            AssuranceRun,
            args.run_id
        )

        if not run:
            raise SystemExit("Kane run not found.")

        if run.status != "FAILED":

            raise SystemExit(
                "Only FAILED runs can generate repair tasks."
            )

        prompt = build_prompt(run)

        feedback_path = (
            OUTPUT_DIR /
            f"repair_run_{run.id}.md"
        )

        feedback_path.write_text(
            prompt,
            encoding="utf-8"
        )

        run.agent_feedback_path = str(
            feedback_path.relative_to(ROOT)
        )

        run.agent_status = "READY"

        db.commit()

        print("Feedback generated:")
        print(feedback_path)

        # Manual mode: hand prompt to an existing IDE agent.

        if args.manual:

            print(
                "\nOpen this file in your coding agent:"
            )

            print(feedback_path)

            return

        codex = shutil.which("codex")

        if not codex:

            print(
                "\nCodex CLI unavailable."
                "\nUse --manual and send the generated "
                "prompt to your existing coding agent."
            )

            return

        run.agent_status = "RUNNING"

        db.commit()

        print("\nStarting Codex repair...")

        try:

            result = subprocess.run(

                [
                    codex,
                    "exec",
                    "--sandbox",
                    "workspace-write",
                    "-"
                ],

                input=prompt,

                capture_output=True,

                text=True,

                cwd=ROOT,

                timeout=900,

                check=False

            )

        except subprocess.TimeoutExpired as exc:

            run.agent_output = (
                "Codex CLI timed out after 900 seconds.\n"
                + str(exc.stderr or "")[-50000:]
            )

            run.agent_status = "FAILED"

            db.commit()

            print("Codex repair timed out; inspect saved agent output.")

            return

        except OSError as exc:

            run.agent_output = str(exc)[:50000]

            run.agent_status = "FAILED"

            db.commit()

            print("Codex CLI could not be executed; inspect saved output.")

            return

        output = (

            result.stdout
            + "\n"
            + result.stderr
        )

        run.agent_output = output[-50000:]

        run.agent_status = (
            "COMPLETED"
            if result.returncode == 0
            else "FAILED"
        )

        db.commit()

        print("\nAgent output:\n")
        print(output)

        if result.returncode != 0:

            print(
                "\nAgent execution failed. "
                "Inspect the saved output."
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()