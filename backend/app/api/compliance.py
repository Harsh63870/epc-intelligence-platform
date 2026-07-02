"""Specification compliance API routes."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.spec_compliance_agent import check_submittal_compliance
from app.database import get_db
from app.models import NCStatus, NonConformance, Specification, Submittal
from app.services.text_extraction import extract_text_from_bytes

router = APIRouter(prefix="/compliance", tags=["compliance"])


class NCOut(BaseModel):
    id: int
    submittal_id: int
    spec_id: int | None
    severity: str
    deviation: str
    status: str
    requirement_key: str | None = None
    required_value: str | None = None
    submitted_value: str | None = None
    standard_ref: str | None = None


class ComplianceCheckResponse(BaseModel):
    submittal_id: int
    vendor: str
    equipment_class: str
    filename: str
    parsed_attributes: dict
    checks: list[dict]
    non_conformances: list[dict]
    passed: int
    failed: int


class NCStatusUpdate(BaseModel):
    status: str


@router.post("/check-submittal", response_model=ComplianceCheckResponse)
async def check_submittal(
    file: UploadFile = File(...),
    project_id: int = Form(default=1),
    vendor: str = Form(default="Unknown Vendor"),
    db: Session = Depends(get_db),
) -> ComplianceCheckResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    content = await file.read()
    try:
        text = extract_text_from_bytes(content, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = check_submittal_compliance(
        db,
        project_id=project_id,
        vendor=vendor,
        text=text,
        filename=file.filename,
    )
    return ComplianceCheckResponse(**result)


@router.get("/non-conformances", response_model=list[NCOut])
def list_non_conformances(
    project_id: int = Query(default=1),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[NCOut]:
    query = (
        db.query(NonConformance, Submittal, Specification)
        .join(Submittal, NonConformance.submittal_id == Submittal.id)
        .outerjoin(Specification, NonConformance.spec_id == Specification.id)
        .filter(Submittal.project_id == project_id)
    )
    if status:
        query = query.filter(NonConformance.status == status)

    results = []
    for nc, submittal, spec in query.order_by(NonConformance.id.desc()).all():
        results.append(
            NCOut(
                id=nc.id,
                submittal_id=nc.submittal_id,
                spec_id=nc.spec_id,
                severity=nc.severity,
                deviation=nc.deviation,
                status=nc.status,
                requirement_key=spec.requirement_key if spec else None,
                required_value=spec.required_value if spec else None,
                submitted_value=(submittal.parsed_attributes or {}).get(spec.requirement_key) if spec else None,
                standard_ref=spec.standard_ref if spec else None,
            )
        )
    return results


@router.patch("/nc/{nc_id}/status", response_model=NCOut)
def update_nc_status(
    nc_id: int,
    body: NCStatusUpdate,
    db: Session = Depends(get_db),
) -> NCOut:
    allowed = {s.value for s in NCStatus}
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {allowed}")

    nc = db.query(NonConformance).filter(NonConformance.id == nc_id).first()
    if not nc:
        raise HTTPException(status_code=404, detail="Non-conformance not found")

    nc.status = body.status
    db.commit()
    db.refresh(nc)

    submittal = db.query(Submittal).filter(Submittal.id == nc.submittal_id).first()
    spec = db.query(Specification).filter(Specification.id == nc.spec_id).first() if nc.spec_id else None

    return NCOut(
        id=nc.id,
        submittal_id=nc.submittal_id,
        spec_id=nc.spec_id,
        severity=nc.severity,
        deviation=nc.deviation,
        status=nc.status,
        requirement_key=spec.requirement_key if spec else None,
        required_value=spec.required_value if spec else None,
        submitted_value=(submittal.parsed_attributes or {}).get(spec.requirement_key) if spec and submittal else None,
        standard_ref=spec.standard_ref if spec else None,
    )
