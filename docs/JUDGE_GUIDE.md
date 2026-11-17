# Judge Guide

Start with the [root README](../README.md) for fresh install, environment setup, API reference, all four judging criteria, and troubleshooting. This page is a short execution card.

## Local application

1. Install Python 3.13, Node.js 20/npm, and Tesseract. Install Kane CLI separately only if evaluating browser assurance.
2. Clone and configure secrets as shown in the root README. Seed with `python seed_demo.py` and `python seed_users.py` from `backend/`.
3. Run backend in one terminal (`uvicorn main:app --reload`) and frontend in another (`npm run dev`). Open <http://localhost:5173/>.
4. Log in using the reviewer account and its locally generated password.
5. Generate sample test PDFs: `python tests/create_test_invoices.py` from `backend/`.
6. Upload normal, bank-change, and price-inflated invoices. Inspect detail-page extraction, findings, risk state, line items, PDF preview, and audit history.
7. Log in separately as the approver; attempt approval before review/verification and inspect the backend's 409 response plus BLOCKED audit event.

## Kane browser verification

1. Register/authenticate with TestMu and ensure credits; `kane-cli login --oauth`, `kane-cli whoami`, `kane-cli balance`.
2. Ensure `KANE_BASE_URL` points to the local frontend and `DEMO_APPROVER_PASSWORD` matches the seeded account.
3. Open `/assurance`, pick a scenario-compatible pending invoice, start Kane, then inspect steps, `run_end` verdict, Test Manager URL, and evidence file path when returned.
4. A single smoke run verifies only the tested login-page conditions. It is not evidence for approval, upload, or fraud behavior.

## Closed loop

For an actual FAILED run, create the prompt with `backend/.venv/bin/python scripts/repair_from_kane.py RUN_ID --manual` from repository root. Provide `artifacts/agent-feedback/repair_run_RUN_ID.md` to the coding agent. Review the diff, run backend tests and frontend build, then use **Run same scenario again**. The second run must link to the original and PASS in Kane. Do not fault-inject in the shared repository or use non-demo invoices; any controlled fault experiment must remain in an isolated disposable clone and never be committed.

## Evidence to inspect

- API behavior and risk findings: `/docs`, `/api/invoices/{id}`, `/api/invoices/{id}/risk`.
- Human actions: `/api/invoices/{id}/audit` and `/api/audit`.
- Kane: `/api/assurance/runs`, `/api/assurance/runs/{id}`, Assurance Lab run history.
- Browser evidence: exact `*.evidence` path from the run, opened with `kane-cli evidence serve PATH.evidence`.

A local browser smoke was run on 2026-11-17: Kane CLI 0.10.5 with Chrome checked the login brand and fields, did not submit credentials, and returned PASS. Full approval scenario testing remains blocked until valid demo passwords are configured and the backend is started.
