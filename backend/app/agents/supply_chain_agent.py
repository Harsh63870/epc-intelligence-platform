"""Supply chain visibility and alerts."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AuditEvent, ProcurementItem, ScheduleTask


def get_shipments(db: Session, project_id: int) -> list[dict]:
    items = (
        db.query(ProcurementItem)
        .filter(ProcurementItem.project_id == project_id)
        .order_by(ProcurementItem.eta)
        .all()
    )
    return [
        {
            "id": item.id,
            "equipment_type": item.equipment_type,
            "supplier": item.supplier,
            "eta": item.eta.isoformat() if item.eta else None,
            "status": item.status,
            "risk_score": item.risk_score,
            "origin_lat": item.origin_lat,
            "origin_lng": item.origin_lng,
            "dest_lat": item.dest_lat,
            "dest_lng": item.dest_lng,
            "current_lat": item.current_lat,
            "current_lng": item.current_lng,
        }
        for item in items
    ]


def get_supply_alerts(db: Session, project_id: int) -> list[dict]:
    items = (
        db.query(ProcurementItem)
        .filter(
            ProcurementItem.project_id == project_id,
            ProcurementItem.status.in_(["at_risk", "delayed"]),
        )
        .all()
    )
    alerts = []
    for item in items:
        impacted_tasks = (
            db.query(ScheduleTask)
            .filter(
                ScheduleTask.project_id == project_id,
                ScheduleTask.depends_on_procurement_id == item.id,
                ScheduleTask.critical_path.is_(True),
            )
            .all()
        )
        delay_note = "Delayed delivery" if item.status == "delayed" else "At-risk delivery"
        for task in impacted_tasks:
            alerts.append(
                {
                    "shipment_id": item.id,
                    "equipment_type": item.equipment_type,
                    "supplier": item.supplier,
                    "status": item.status,
                    "eta": item.eta.isoformat() if item.eta else None,
                    "message": f"{delay_note}: {item.equipment_type} impacts critical path task '{task.name}'",
                    "task_id": task.id,
                    "task_name": task.name,
                    "severity": "high" if item.status == "delayed" else "medium",
                }
            )
        if not impacted_tasks:
            alerts.append(
                {
                    "shipment_id": item.id,
                    "equipment_type": item.equipment_type,
                    "supplier": item.supplier,
                    "status": item.status,
                    "eta": item.eta.isoformat() if item.eta else None,
                    "message": f"{delay_note}: {item.equipment_type} from {item.supplier}",
                    "task_id": None,
                    "task_name": None,
                    "severity": "medium",
                }
            )
    return alerts


def log_shipment_check(db: Session, project_id: int, shipment_id: int) -> None:
    db.add(
        AuditEvent(
            project_id=project_id,
            entity_type="supply_chain",
            entity_id=shipment_id,
            action="Supply chain status reviewed",
            actor="supply_chain_agent",
        )
    )
    db.commit()
