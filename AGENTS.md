# LedgerLock Coding Agent Instructions

## Project
LedgerLock is an invoice fraud detection and
accounts payable approval security platform.

## Kane verification rules

When a Kane Assurance run fails:

1. Read its failure report and execution evidence.
2. Identify the underlying application defect.
3. Inspect the relevant backend and frontend files.
4. Make the smallest correct code change.
5. Never weaken invoice fraud detection policies.
6. Never bypass reviewer-approver separation.
7. Never modify the Kane objective to hide a failure.
8. Never delete a failing assertion.
9. Run relevant Python tests.
10. Run frontend production build.
11. Report files modified and tests executed.

## Important constraints

- HOLD invoices must remain blocked unless an
  explicitly supported human verification workflow
  has been completed.
- Duplicate HOLD invoices cannot be released through
  the bank verification exception.
- Frontend restrictions are not substitutes for
  backend authorization.
- Audit history must be preserved.
- Never hardcode production credentials.
- Do not modify synthetic test expectations to make
  a failed verification pass.