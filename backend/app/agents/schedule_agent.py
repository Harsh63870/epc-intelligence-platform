"""Schedule risk analysis and mitigation."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AuditEvent, ProcurementItem, ScheduleTask
from app.services.groq_client import GroqError, chat_completion

MITIGATION_FALLBACK = [
    "Expedite procurement with alternate supplier quote",
    "Re-sequence non-critical path activities to absorb delay",
    "Parallelize installation prep while awaiting delivery",
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def compute_task_risks(db: Session, project_id: int) -> list[dict]:
    tasks = (
        db.query(ScheduleTask)
        .filter(ScheduleTask.project_id == project_id)
        .order_by(ScheduleTask.planned_start)
        .all()
    )
    results = []

    for task in tasks:
        procurement = None
        if task.depends_on_procurement_id:
            procurement = (
                db.query(ProcurementItem)
                .filter(ProcurementItem.id == task.depends_on_procurement_id)
                .first()
            )

        delay_days = 0
        procurement_eta = None
        equipment = None
        if procurement and task.planned_start:
            eta = _ensure_aware(procurement.eta)
            start = _ensure_aware(task.planned_start)
            if eta and start:
                delay_days = (eta - start).days
                procurement_eta = eta.isoformat()
                equipment = procurement.equipment_type

        risk_score = 0.0
        if delay_days > 7:
            risk_score = min(1.0, delay_days / 21)
        elif delay_days > 0:
            risk_score = 0.4
        elif procurement and procurement.status in ("at_risk", "delayed"):
            risk_score = 0.65

        task.risk_score = risk_score
        days_until_start = None
        if task.planned_start:
            start = _ensure_aware(task.planned_start)
            days_until_start = (start - _utcnow()).days if start else None

        results.append(
            {
                "task_id": task.id,
                "name": task.name,
                "planned_start": task.planned_start.isoformat() if task.planned_start else None,
                "planned_end": task.planned_end.isoformat() if task.planned_end else None,
                "critical_path": task.critical_path,
                "status": task.status,
                "risk_score": round(risk_score, 2),
                "delay_days": delay_days,
                "days_until_start": days_until_start,
                "procurement_equipment": equipment,
                "procurement_eta": procurement_eta,
                "risk_level": "high" if risk_score >= 0.5 else "medium" if risk_score >= 0.3 else "low",
            }
        )

    db.commit()
    return sorted(results, key=lambda r: r["risk_score"], reverse=True)


def generate_mitigations(task_name: str, delay_days: int, equipment: str | None) -> list[str]:
    context = f"Task: {task_name}. Procurement delay: {delay_days} days. Equipment: {equipment or 'N/A'}."
    try:
        raw = chat_completion(
            system=(
                "You are a data centre EPC scheduler. Return exactly 3 short mitigation options "
                'as a JSON object: {"mitigations": ["...", "...", "..."]}'
            ),
            user=context,
            json_mode=True,
        )
        import json

        data = json.loads(raw)
        return data.get("mitigations", MITIGATION_FALLBACK)[:3]
    except (GroqError, Exception):
        return MITIGATION_FALLBACK


def get_schedule_risks(db: Session, project_id: int, min_risk: float = 0.3) -> list[dict]:
    all_risks = compute_task_risks(db, project_id)
    return [r for r in all_risks if r["risk_score"] >= min_risk]


def log_mitigation_request(db: Session, project_id: int, task_id: int) -> None:
    db.add(
        AuditEvent(
            project_id=project_id,
            entity_type="schedule_risk",
            entity_id=task_id,
            action="Schedule mitigation options generated",
            actor="schedule_agent",
        )
    )
    db.commit()
