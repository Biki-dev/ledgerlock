import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.repair_from_kane import build_prompt


def test_failure_report_includes_objective_steps_and_repair_constraints():
    run = SimpleNamespace(
        id=42,
        scenario_title="Unverified bank change approval protection",
        scenario_code="bank_change_approval_guard",
        invoice_id=123,
        kane_status="failed",
        exit_code=1,
        summary="The invoice was approved without verification.",
        reason="Expected a blocked approval.",
        objective="Approve the unverified bank-change HOLD invoice.",
        step_events=[
            {"step": 3, "status": "failed", "remark": "Invoice approved"}
        ],
        evidence_path="/tmp/run.evidence",
        test_url="https://test-manager.example/run/42",
    )

    prompt = build_prompt(run)

    assert "Run ID: 42" in prompt
    assert "Invoice ID: 123" in prompt
    assert run.objective in prompt
    assert "Invoice approved" in prompt
    assert run.evidence_path in prompt
    assert "Do not modify the original Kane scenario" in prompt
    assert "Do not remove or weaken assertions" in prompt
