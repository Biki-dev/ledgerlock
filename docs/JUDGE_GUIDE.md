# Judge Guide

## Start the app

Follow the root [README setup](../README.md), configure `backend/.env`, then start:

```bash
# Terminal 1
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd frontend
npm run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:5173/.

## Generate demo PDFs

```bash
cd backend
python tests/create_test_invoices.py
```

Generated files are in `backend/tests/generated/`.

## Core workflow

1. Sign in as `reviewer@ledgerlock.demo` with the local password.
2. Upload `normal.pdf`; inspect extracted data, line items, risk, PDF preview.
3. Upload `bank_changed.pdf`; confirm bank-change `HOLD` finding.
4. As reviewer, record bank verification. Sign out and sign in as `approver@ledgerlock.demo`; approve the verified invoice.
5. Upload `price_inflated.pdf`; inspect the price-history `REVIEW` finding.
6. Upload `normal.pdf` twice with identical bytes; the second upload should show `EXACT_FILE_DUPLICATE` / `HOLD`.
7. Inspect invoice audit and global audit.

## Kane browser scenario

```bash
kane-cli --version
kane-cli login --oauth
kane-cli whoami
kane-cli balance
```

Set `KANE_BASE_URL=http://localhost:5173` and ensure `DEMO_APPROVER_PASSWORD` matches the seeded approver account. Open `/assurance`, select a compatible pending invoice, and run a scenario.

For `bank_change_approval_guard`, use an invoice whose bank verification is still `PENDING`. Do not run the scenario after completing bank verification.

## Evidence to inspect

| What | Location |
|---|---|
| API schemas | `/docs` |
| Invoice details/risk | `/api/invoices/{id}`, `/api/invoices/{id}/risk` |
| Audit | `/api/invoices/{id}/audit`, `/api/audit` |
| Kane runs | `/api/assurance/runs`, `/api/assurance/runs/{id}` |
| Browser evidence | Exact `.evidence` path returned by the run |

```bash
kane-cli evidence serve "/absolute/path/to/run.evidence"
```