"""Commissioning test management."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AuditEvent, CommissioningTest, TestStatus


def list_tests(db: Session, project_id: int, system_type: str | None = None) -> list[dict]:
    query = db.query(CommissioningTest).filter(CommissioningTest.project_id == project_id)
    if system_type:
        query = query.filter(CommissioningTest.system_type == system_type)
    tests = query.order_by(CommissioningTest.id).all()
    return [
        {
            "id": t.id,
            "standard_ref": t.standard_ref,
            "procedure": t.procedure,
            "system_type": t.system_type,
            "acceptance_criteria": t.acceptance_criteria,
            "status": t.status,
            "result": t.result,
        }
        for t in tests
    ]


def get_progress(db: Session, project_id: int) -> dict:
    tests = db.query(CommissioningTest).filter(CommissioningTest.project_id == project_id).all()
    if not tests:
        return {"total": 0, "completed": 0, "progress_pct": 0.0, "by_system": {}}

    completed_statuses = {TestStatus.PASSED.value, TestStatus.FAILED.value, TestStatus.NC.value}
    completed = sum(1 for t in tests if t.status in completed_statuses)
    by_system: dict[str, dict] = {}

    for t in tests:
        sys = t.system_type
        if sys not in by_system:
            by_system[sys] = {"total": 0, "completed": 0}
        by_system[sys]["total"] += 1
        if t.status in completed_statuses:
            by_system[sys]["completed"] += 1

    for sys in by_system:
        total = by_system[sys]["total"]
        by_system[sys]["progress_pct"] = round(by_system[sys]["completed"] / total * 100, 1) if total else 0

    return {
        "total": len(tests),
        "completed": completed,
        "progress_pct": round(completed / len(tests) * 100, 1),
        "by_system": by_system,
    }


def record_test_result(
    db: Session,
    test_id: int,
    *,
    status: str,
    notes: str = "",
    measured_value: str | None = None,
) -> dict:
    test = db.query(CommissioningTest).filter(CommissioningTest.id == test_id).first()
    if not test:
        raise ValueError("Test not found")

    allowed = {TestStatus.PASSED.value, TestStatus.FAILED.value, TestStatus.NC.value, TestStatus.IN_PROGRESS.value}
    if status not in allowed:
        raise ValueError(f"Invalid status. Must be one of: {allowed}")

    test.status = status
    test.result = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
        "measured_value": measured_value,
        "acceptance_criteria": test.acceptance_criteria,
        "standard_ref": test.standard_ref,
    }
    db.add(
        AuditEvent(
            project_id=test.project_id,
            entity_type="commissioning",
            entity_id=test.id,
            action=f"Commissioning test recorded: {test.procedure[:80]} — {status}",
            actor="commissioning_agent",
        )
    )
    db.commit()
    db.refresh(test)

    return {
        "id": test.id,
        "procedure": test.procedure,
        "status": test.status,
        "result": test.result,
    }
