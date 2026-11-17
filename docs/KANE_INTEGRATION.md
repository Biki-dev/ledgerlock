# Kane CLI Integration

## Install / authenticate

Install using the [official Kane CLI guide](https://www.testmuai.com/support/docs/kane-cli-introduction/), then:

```bash
kane-cli --version
kane-cli login --oauth
kane-cli whoami
kane-cli balance
```

Requires a TestMu account, authentication, available credits, local LedgerLock frontend/backend, and Chrome/Chromium.

## Configuration

In `backend/.env`:

```dotenv
KANE_BASE_URL=http://localhost:5173
KANE_APPROVER_EMAIL=approver@ledgerlock.demo
DEMO_APPROVER_PASSWORD=<same password used by seed_users.py>
```

Never commit the password. The backend provides it to Kane through a temporary mode-0600 variables file and removes the file after execution.

## Scenarios

| Scenario code | Required invoice state | Expected result |
|---|---|---|
| `bank_change_approval_guard` | `PENDING`, sole `BANK_DETAILS_CHANGED` HOLD, verification `PENDING` | Approval blocked; invoice remains pending/HOLD |
| `review_clearance_guard` | `PENDING` REVIEW, review `PENDING` | Approval blocked |
| `duplicate_approval_guard` | `PENDING` duplicate HOLD | Approval blocked; bank exception unavailable |
| `clear_invoice_approval` | `PENDING` CLEAR | Authorized approver can approve |

## Run from UI

1. Start backend and frontend.
2. Sign in to LedgerLock with a compatible user.
3. Open http://localhost:5173/assurance.
4. Select a pending invoice matching the scenario.
5. Start the run and inspect status, steps, summary, Test Manager URL, and evidence path.

## API

Get a token from login, then:

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

Use real local invoice/run IDs. Run creation returns `202`; concurrent `QUEUED`/`RUNNING` runs are blocked.

## Runner behavior

The backend starts:

```bash
kane-cli run OBJECTIVE --url ... --agent --max-steps 30 --timeout 180 --variables-file ...
```

- Kane Agent mode output is parsed as NDJSON.
- The parser collects `step` events and the final `run_end` event.
- `PASSED` requires process exit code `0` and `run_end.status == "passed"`.
- Missing `run_end`, timeout, missing CLI, or unknown scenario is `ERROR`.
- Assertion failure is `FAILED`.
- Evidence path is saved only when a real `*.evidence` file is found.
- Missing URL, session directory, evidence, or credits remain missing; values are not fabricated.

## Retest

Only a `FAILED` run can be retested. Use **Run same scenario again** from the failed-run panel. The backend checks that the retest uses the same invoice and scenario and records `retest_of_run_id`.

A linked Kane `PASS` verifies the behavior. Agent process status `COMPLETED` is not a Kane verdict.

## Evidence

```bash
kane-cli evidence serve "/absolute/path/returned/by/the/run.evidence"
```

Use the exact path returned in the Assurance run. A session directory is not an evidence pack.

## Implementation

- `backend/services/kane_runner.py` — scenario definitions
- `backend/services/kane_execution.py` — CLI execution, persistence, evidence lookup
- `backend/services/kane_parser.py` — NDJSON parsing
- `backend/routes/assurance.py` — scenario validation and retest linkage
- `frontend/src/pages/AssuranceLabPage.tsx` — Assurance UI