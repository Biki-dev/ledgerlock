# Coding-Agent Handoff

## Generate a repair report

Only a persisted `FAILED` Kane run can generate a report.

```bash
# From repository root
backend/.venv/bin/python scripts/repair_from_kane.py RUN_ID --manual
```

Output:

```text
artifacts/agent-feedback/repair_run_RUN_ID.md
```

The report includes the failed scenario, objective, steps, failure reason, evidence reference, and repair instructions.

## Agent support

| Agent | Integration |
|---|---|
| Codex CLI | Automated adapter available |
| Claude Code | Manual Markdown handoff |
| Cursor | Manual Markdown handoff |
| Windsurf | Manual Markdown handoff |
| Kiro | Manual Markdown handoff |
| Other IDE/CLI agents | Manual Markdown handoff |

### Run Codex adapter

Install/authenticate Codex using the [official CLI docs](https://learn.chatgpt.com/docs/codex/cli), then:

```bash
backend/.venv/bin/python scripts/repair_from_kane.py RUN_ID
```

The adapter runs:

```bash
codex exec --sandbox workspace-write -
```

It sends the generated prompt on stdin and stores process output in the Assurance run. The adapter has not been exercised in the inspected environment because the `codex` executable was not installed.

### Manual agent flow

1. Open the repository in the agent.
2. Open `artifacts/agent-feedback/repair_run_RUN_ID.md`.
3. Ask the agent to fix the application source, not the Kane objective or expected result.
4. Review the diff. Reject changes that weaken HOLD, reviewer/approver separation, bank verification, audit history, or tests.
5. Run tests/build:

```bash
cd backend && .venv/bin/pytest -v
cd ../frontend && npm run lint && npm run build
```

6. Run the linked same-invoice/same-scenario Kane retest.
7. Accept the repair only after the linked Kane retest returns `PASS`.

## Agent states

| State | Meaning |
|---|---|
| `NOT_STARTED` | No repair feedback generated |
| `READY` | Repair prompt generated |
| `RUNNING` | Automated agent process running |
| `COMPLETED` | Agent process exited successfully; repair is not yet verified |
| `FAILED` | Agent process returned failure |

**Verification rule:** agent `COMPLETED` does not prove the defect was fixed. Only a linked Kane `PASS` verifies the repaired behavior.
