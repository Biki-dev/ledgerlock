# Kane CLI Integration

This guide supplements the [root setup and judge README](../README.md). It documents the current `backend/services/kane_runner.py`, `kane_execution.py`, `kane_parser.py`, and `routes/assurance.py` behavior.

## Prerequisites and verified interface

The inspected development machine has `@testmuai/kane-cli` **0.10.5**, Google Chrome at `/usr/bin/google-chrome`, and an authenticated Kane profile with credits. The tested commands were confirmed against `kane-cli --help`, `kane-cli run --help`, `kane-cli login --help`, and `kane-cli evidence --help`.

Official resources:

- [Kane CLI introduction](https://www.testmuai.com/support/docs/kane-cli-introduction/)
- [Kane CLI cookbook](https://www.testmuai.com/kane-cli-cookbook/)
- [Kane CLI source](https://github.com/LambdaTest/kane-cli)

Install Kane using the current official CLI documentation, then:

```bash
kane-cli --version
kane-cli login --oauth
kane-cli whoami
kane-cli balance
```

A TestMu account and sufficient credit are external prerequisites. No credit amount is assumed here. Browser runs use the configured local Chrome desktop target unless the user's Kane configuration selects another target.

## How a run works

1. `GET /api/assurance/scenarios` returns the scenario catalog.
2. `POST /api/assurance/runs` validates invoice risk state/findings, PENDING approval state, and optional retest parent. It persists a QUEUED `AssuranceRun` and schedules a background task.
3. `kane_execution.py` starts `kane-cli run OBJECTIVE --url ... --agent --max-steps 30 --timeout 180 --variables-file ...`. The CLI help confirms these options. The approver email/password are variables; the password is marked secret in a mode-0600 temporary file and removed after execution. It is not embedded in the persisted objective or process argument list.
4. Agent mode emits newline-delimited JSON (NDJSON). `kane_parser.py` ignores non-JSON lines, collects `step` events, and keeps the last `run_end` event.
5. The backend records exit code, bounded stdout/stderr, steps, status, summary/reason, duration/credits/Test Manager URL only when supplied, session directory, and an evidence path only if an actual `.evidence` file is found.
6. Overall PASS requires both exit code 0 and `run_end.status == "passed"`. A missing `run_end` is ERROR. A timeout, missing CLI, and unknown scenario are errors. Assertion failures are FAILED, not PASSED.
7. A linked retest must point to a FAILED run with the same invoice and scenario. A passing retest marks the parent run's agent status COMPLETED; that agent label is not a Kane verdict.

## Scenarios

| Code | Preconditions | Kane objective |
|---|---|---|
| `bank_change_approval_guard` | PENDING invoice, HOLD, sole `BANK_DETAILS_CHANGED`, verification PENDING | Attempt approval before verification; expect backend denial and invoice to remain pending/HOLD. |
| `review_clearance_guard` | PENDING REVIEW, review PENDING | Attempt approval before reviewer clearance; expect backend denial. |
| `duplicate_approval_guard` | PENDING duplicate HOLD | Attempt approval; expect duplicate HOLD rejection, not bank exception. |
| `clear_invoice_approval` | PENDING CLEAR | Approve as an authorized approver; expect APPROVED and audit event. |

## Run from the UI or API

Open <http://localhost:5173/assurance>, select a compatible PENDING invoice and scenario, and start the run. The page polls run history; select a run to view status, steps, summary/reason, Test Manager URL, and evidence path.

Example direct requests (first log in and put the returned access token in `$TOKEN`):

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/assurance/scenarios

curl -X POST http://localhost:8000/api/assurance/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"invoice_id": 12, "scenario_code": "bank_change_approval_guard"}'

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/assurance/runs/1
```

Use real IDs from your local database. API creation returns 202 and an Assurance run object. The current backend prevents concurrent QUEUED/RUNNING runs.

## Evidence

When Kane returns a session directory, `find_evidence_pack()` searches its `evidence` subdirectory for `*.evidence`. It returns `None` when no file exists; it does not return the directory as though it were a pack. Use the exact returned path:

```bash
kane-cli evidence serve "/absolute/path/from-the-run.evidence"
```

A missing Test Manager URL, session directory, evidence pack, or credits value remains missing; LedgerLock does not synthesize these values. The one-off browser smoke may produce a Kane session/evidence pack without creating an AssuranceRun because it was launched directly from the CLI.

## Retesting

Only a FAILED run can be retested. Click **Run same scenario again** in the failed-run panel. The UI sends the failed run ID; the server verifies the same invoice and scenario, and persists `retest_of_run_id`. Inspect the parent and child in run history. The `agent_status` on the parent becomes COMPLETED only when the linked Kane retest is PASSED.

## Local smoke status

A non-mutating smoke was run against the local login page using Kane CLI 0.10.5 and desktop Chrome. It passed checks for brand, email field, password field, and Sign in button without submitting credentials. This does **not** verify login, upload, approval, or API security. Those require a backend started with valid demo secrets; the current local secrets fail the minimum-length policy.
