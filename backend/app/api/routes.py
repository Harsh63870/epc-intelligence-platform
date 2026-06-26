"""API route handlers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditEvent, CommissioningTest, NonConformance, ProcurementItem, Project, RFI, ScheduleTask
from app.schemas import DashboardMetrics, HealthOut, ProjectOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health_check(db: Session = Depends(get_db)) -> HealthOut:
    db_status = "connected"
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
    return HealthOut(status="ok", service="epc-intelligence-api", database=db_status)


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.id).all()


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
def dashboard_metrics(project_id: int = 1, db: Session = Depends(get_db)) -> DashboardMetrics:
    active_ncs = db.query(NonConformance).filter(NonConformance.status == "open").count()
    open_rfis = db.query(RFI).filter(RFI.project_id == project_id, RFI.status == "open").count()
    schedule_risks = db.query(ScheduleTask).filter(
        ScheduleTask.project_id == project_id, ScheduleTask.risk_score >= 0.5
    ).count()
    at_risk = db.query(ProcurementItem).filter(
        ProcurementItem.project_id == project_id,
        ProcurementItem.status.in_(["at_risk", "delayed"]),
    ).count()
    tests = db.query(CommissioningTest).filter(CommissioningTest.project_id == project_id).all()
    if tests:
        completed = sum(1 for t in tests if t.status in ("passed", "failed", "nc"))
        commissioning_progress_pct = round(completed / len(tests) * 100, 1)
    else:
        commissioning_progress_pct = 0.0
    hours_saved = db.query(AuditEvent).count() * 0.5
    return DashboardMetrics(
        active_ncs=active_ncs,
        open_rfis=open_rfis,
        schedule_risks=schedule_risks,
        at_risk_shipments=at_risk,
        commissioning_progress_pct=commissioning_progress_pct,
        hours_saved_week=round(hours_saved, 1),
    )
