# LedgerLock

Invoice PDF analysis, fraud flags, approval controls, audit history, and Kane CLI browser verification.

**Stack:** Python 3.13 · FastAPI · SQLAlchemy · SQLite · PyMuPDF · Tesseract · RapidFuzz · React 19 · TypeScript · Vite · Tailwind · Kane CLI

## 1. Setup

### Requirements

- Python 3.13
- Node.js 20 and npm
- Tesseract OCR (`sudo dnf install tesseract` on Fedora)
- Chrome/Chromium for Kane browser runs

### Install

```bash
git clone https://github.com/Biki-dev/ledgerlock.git
cd ledgerlock

python3.13 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-lock.txt

cp .env.example backend/.env
# Set the secrets listed below in backend/.env.

cd frontend
npm ci
cd ..

cd backend
python migrate_phase2.py
python migrate_phase3.py
python migrate_phase5.py
python seed_demo.py
python seed_users.py
cd ..
```

### Required `backend/.env` values

Generate unique values locally; do not commit or share them:

```bash
openssl rand -hex 32  # JWT_SECRET_KEY
openssl rand -hex 24  # DEMO_REVIEWER_PASSWORD
openssl rand -hex 24  # DEMO_APPROVER_PASSWORD
openssl rand -hex 24  # DEMO_ADMIN_PASSWORD
```

Set these four values in `backend/.env`. Each demo password must be unique and at least 16 characters. `seed_users.py` updates the local password hashes. Set `KANE_BASE_URL=http://localhost:5173` for local Kane runs. Optional settings: `KANE_APPROVER_EMAIL`, `FRONTEND_ORIGINS`, and `VITE_API_URL`.

Demo accounts (passwords are generated locally):

| Email | Role |
|---|---|
| `reviewer@ledgerlock.demo` | `FINANCE_REVIEWER` |
| `approver@ledgerlock.demo` | `FINANCE_APPROVER` |
| `admin@ledgerlock.demo` | `ADMIN` |

## 2. Run

Terminal 1:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev -- --host 127.0.0.1
```

| Service | URL |
|---|---|
| Frontend | http://127.0.0.1:5173/ |
| API health | http://127.0.0.1:8000/health |
| Swagger | http://127.0.0.1:8000/docs |
| Kane Assurance Lab | http://127.0.0.1:5173/assurance |

## 3. Demo workflow

Generate synthetic PDFs:

```bash
cd backend
python tests/create_test_invoices.py
```

1. Sign in as `reviewer@ledgerlock.demo`.
2. Upload `tests/generated/normal.pdf`; inspect extracted fields, line items, risk findings, and PDF preview.
3. Upload `bank_changed.pdf`; expect `BANK_DETAILS_CHANGED` / `HOLD`.
4. As reviewer, submit the bank verification details. Sign in as a separate approver and approve the verified invoice.
5. Upload `price_inflated.pdf`; expect a price-history `REVIEW` finding.
6. Upload `normal.pdf` twice with identical bytes; the second upload should trigger `EXACT_FILE_DUPLICATE` / `HOLD`.
7. Inspect invoice and global audit history.
8. Use a separate compatible pending invoice to run a Kane scenario. Do not verify a bank-change invoice before running `bank_change_approval_guard`; that scenario expects verification to remain pending.

## 4. Risk states

| State | Meaning in the implementation |
|---|---|
| `CLEAR` | No configured detector/completeness finding |
| `REVIEW` | One or more non-HOLD findings |
| `HOLD` | At least one blocking finding |

Configured checks: exact-file duplicate, invoice-number duplicate, near duplicate, vendor bank change, historical price increase, line/subtotal/total arithmetic, and missing/incomplete fields. Risk score is a capped heuristic, not a fraud probability. A `CLEAR` result is not a guarantee that an invoice is genuine.

## 5. Tests

Backend:

```bash
cd backend
source .venv/bin/activate
pytest -v
```

Frontend:

```bash
cd frontend
npm ci
npm run lint
npm run build
```

There is no frontend unit-test script. ESLint and the production build are the available frontend checks.

## 6. Important API routes

All routes below require Bearer JWT except login.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/auth/login` | Sign in |
| `GET` | `/api/auth/me` | Current user |
| `POST` | `/api/invoices/upload` | Upload and analyze PDF |
| `GET` | `/api/invoices` | List newest 100 invoices |
| `GET` | `/api/invoices/{id}` | Invoice details |
| `GET` | `/api/invoices/{id}/source` | Authenticated PDF bytes |
| `GET` | `/api/invoices/{id}/risk` | Risk state and findings |
| `POST` | `/api/invoices/{id}/review` | Reviewer decision |
| `POST` | `/api/invoices/{id}/verify-bank-change` | Record bank verification |
| `POST` | `/api/invoices/{id}/approve` | Approver action |
| `POST` | `/api/invoices/{id}/reject` | Reject invoice |
| `GET` | `/api/invoices/{id}/audit` | Invoice audit history |
| `GET` | `/api/audit` | Global audit history |
| `GET` | `/api/assurance/scenarios` | Kane scenarios |
| `POST` | `/api/assurance/runs` | Start Kane run or linked retest |
| `GET` | `/api/assurance/runs` | Kane run history |
| `GET` | `/api/assurance/runs/{id}` | Kane run details |

## 7. Kane CLI

Install and authenticate Kane using the [official Kane CLI documentation](https://www.testmuai.com/support/docs/kane-cli-introduction/):

```bash
kane-cli --version
kane-cli login --oauth
kane-cli whoami
kane-cli balance
```

Start LedgerLock and open `/assurance`. Select a pending invoice matching one of these scenarios:

- `bank_change_approval_guard` — sole bank-change HOLD; verification pending.
- `review_clearance_guard` — REVIEW; reviewer clearance pending.
- `duplicate_approval_guard` — duplicate HOLD.
- `clear_invoice_approval` — CLEAR invoice pending approval.

A run is `PASSED` only when the process exits with code `0` **and** Kane emits `run_end.status == "passed"`. Missing `run_end` is `ERROR`. See [Kane integration](docs/KANE_INTEGRATION.md) for runner details, API examples, evidence, and retesting.

## 8. Coding-agent handoff

For a failed Kane run:

```bash
# From repository root
backend/.venv/bin/python scripts/repair_from_kane.py RUN_ID --manual
```

The report is written to `artifacts/agent-feedback/repair_run_RUN_ID.md`. Codex CLI is the only automated adapter:

```bash
backend/.venv/bin/python scripts/repair_from_kane.py RUN_ID
```

Claude Code, Cursor, Windsurf, and Kiro use manual Markdown handoff. Review the code diff, run tests/build, and then run the linked same-invoice/same-scenario Kane retest. Agent process `COMPLETED` does not prove a repair; a linked Kane `PASS` does. See [agent integration](docs/AGENT_INTEGRATION.md).

## 9. Judging criteria

| Criterion | Implementation | Reproducible evidence |
|---|---|---|
| **SHIPS (25%)** | PDF upload, extraction, fraud checks, review/approval, audit | Run the demo workflow and inspect invoice details/audit |
| **VERIFIED (25%)** | Kane CLI scenarios and persisted run results | Run a scenario; inspect `run_end`, backend response, audit, and evidence pack |
| **CLOSED LOOP (25%)** | Failure report, agent handoff, linked retest | Repair a failed run and obtain Kane PASS on the same invoice/scenario |
| **CRAFT (25%)** | Modular services, role checks, policy service, tests, frontend | `pytest -v`, `npm run lint`, `npm run build`; test separate reviewer/approver roles |

Implementation map: [Architecture](docs/ARCHITECTURE.md) · [Judge steps](docs/JUDGE_GUIDE.md) · [Kane commands](docs/KANE_INTEGRATION.md) · [Agent workflow](docs/AGENT_INTEGRATION.md).
