"""Schedule risk API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.schedule_agent import compute_task_risks, generate_mitigations, get_schedule_risks, log_mitigation_request
from app.database import get_db

router = APIRouter(prefix="/schedule", tags=["schedule"])


class MitigationResponse(BaseModel):
    task_id: int
    task_name: str
    mitigations: list[str]


@router.get("/tasks")
def list_tasks(project_id: int = Query(default=1), db: Session = Depends(get_db)) -> list[dict]:
    return compute_task_risks(db, project_id)


@router.get("/risks")
def schedule_risks(project_id: int = Query(default=1), db: Session = Depends(get_db)) -> list[dict]:
    return get_schedule_risks(db, project_id)


@router.post("/mitigate/{task_id}", response_model=MitigationResponse)
def mitigate_task(
    task_id: int,
    project_id: int = Query(default=1),
    db: Session = Depends(get_db),
) -> MitigationResponse:
    risks = compute_task_risks(db, project_id)
    task = next((r for r in risks if r["task_id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    mitigations = generate_mitigations(
        task["name"],
        task.get("delay_days", 0),
        task.get("procurement_equipment"),
    )
    log_mitigation_request(db, project_id, task_id)
    return MitigationResponse(task_id=task_id, task_name=task["name"], mitigations=mitigations)
