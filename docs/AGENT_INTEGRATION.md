# Coding-Agent Handoff

LedgerLock's failure-to-repair workflow uses a provider-neutral Markdown report. See the [root README](../README.md) for the complete product, API, and security guide.

## State meanings

| Agent status | Meaning |
|---|---|
| `NOT_STARTED` | No failure feedback generated. |
| `READY` | Repair prompt generated. |
| `RUNNING` | Automated coding-agent process is running. |
| `COMPLETED` | Agent process exited successfully. This does not prove the defect was fixed. |
| `FAILED` | Automated agent process returned failure. |

A successful linked Kane retest is the evidence of corrected behavior; an agent status never substitutes for that retest.

## Generate feedback

Only a FAILED run can generate feedback. From repository root:

```bash
backend/.venv/bin/python scripts/repair_from_kane.py RUN_ID --manual
```

The script reads the run from the backend SQLite database, generates `artifacts/agent-feedback/repair_run_RUN_ID.md`, records its relative path/status, and preserves Kane objective, scenario, failed steps, reason, evidence reference, and Test Manager URL when present. Generated output is ignored by Git.

## Codex CLI adapter

The only automated adapter currently implemented is Codex CLI. Install Codex on macOS/Linux using the official installer and authenticate through its first-run flow:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
cd /path/to/ledgerlock
codex
```

See [OpenAI's CLI documentation](https://learn.chatgpt.com/docs/codex/cli) for supported operating systems, authentication, and sandbox settings. If `codex` is available on PATH:

```bash
backend/.venv/bin/python scripts/repair_from_kane.py RUN_ID
```

The script runs the equivalent of:

```bash
codex exec --sandbox workspace-write -
```

It feeds the generated prompt on stdin and saves process output to `AssuranceRun.agent_output`. It does not declare Kane PASS. Review Codex's diff, run `cd backend && .venv/bin/pytest -v` and `cd frontend && npm run build`, then retest the same scenario in the Lab. The Codex adapter has not been exercised in the current environment because the `codex` executable was not installed.

## Manual agents

These agents do not have a LedgerLock adapter in this repository. Open the repository in the chosen tool, open the generated Markdown, and ask the agent to execute the report's instructions. Review every source/test change before validating.

- **Claude Code:** on Linux/macOS, follow the official installer and authenticate interactively:

	```bash
	curl -fsSL https://claude.ai/install.sh | bash
	cd /path/to/ledgerlock
	claude
	```

	See [Claude Code setup](https://code.claude.com/docs/en/setup) for platform prerequisites and account options. Open the generated Markdown report in the session.
- **Cursor:** install the desktop application from the [official Cursor site/docs](https://cursor.com/docs), open the repository, then attach/reference the report in Cursor Chat or Agent mode.
- **Windsurf:** use the current vendor download/docs; the old Windsurf docs host redirects to [Devin Desktop setup](https://docs.devin.ai/desktop/getting-started). Open the repository and paste/attach the report in the agent panel.
- **Kiro:** use the [official Kiro installation guide](https://kiro.dev/docs/getting-started/installation/), open the repository, and provide the report. Include `AGENTS.md` as project instructions/steering where supported.
- **Other terminal/IDE agent:** provide the report text and local evidence path; ask it to inspect actual source, fix the root cause, and run tests.

Manual workflow:

1. Inspect the failed run and sealed evidence with `kane-cli evidence serve PATH.evidence` when a pack exists.
2. Ask the agent to modify application code, not the Kane objective or expected result.
3. Review the diff. Reject changes that weaken HOLD, reviewer/approver separation, bank verification, audit history, or tests.
4. Run relevant backend tests and frontend production build.
5. Reset only a clearly marked `DEMO_` bank-change invoice if the intentional local demonstration approved it.
6. Run the linked same-invoice/same-scenario Kane retest.
7. Accept the repair only after Kane returns PASS.

There is no automatic integration for Claude Code, Cursor, Windsurf, Kiro, or other agents. A Markdown handoff is not an agent process execution. Provider installation/authentication may require a provider account; the manual report can be used without a paid AI subscription if the user performs the repair themselves.
