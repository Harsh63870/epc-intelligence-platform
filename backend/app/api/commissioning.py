"""Commissioning API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.commissioning_agent import get_progress, list_tests, record_test_result
from app.database import get_db

router = APIRouter(prefix="/commissioning", tags=["commissioning"])


class TestRecordRequest(BaseModel):
    status: str = Field(..., pattern="^(passed|failed|nc|in_progress)$")
    notes: str = ""
    measured_value: str | None = None


@router.get("/tests")
def tests(
    project_id: int = Query(default=1),
    system_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_tests(db, project_id, system_type)


@router.get("/progress")
def progress(project_id: int = Query(default=1), db: Session = Depends(get_db)) -> dict:
    return get_progress(db, project_id)


@router.post("/tests/{test_id}/record")
def record_test(test_id: int, body: TestRecordRequest, db: Session = Depends(get_db)) -> dict:
    try:
        return record_test_result(
            db,
            test_id,
            status=body.status,
            notes=body.notes,
            measured_value=body.measured_value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
