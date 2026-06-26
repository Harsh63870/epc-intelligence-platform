"""Seed demo project for development."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, ProjectStatus

router = APIRouter()


@router.post("/seed")
def seed_demo_data(db: Session = Depends(get_db)) -> dict:
    existing = db.query(Project).filter(Project.name == "Mumbai Hyperscale DC-01").first()
    if existing:
        return {"message": "Demo project already exists", "project_id": existing.id}

    project = Project(
        name="Mumbai Hyperscale DC-01",
        tier_target="Tier III",
        location="Mumbai, Maharashtra, India",
        status=ProjectStatus.CONSTRUCTION.value,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"message": "Demo project seeded", "project_id": project.id}
