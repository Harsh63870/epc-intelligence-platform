"""Seed demo project for development."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.seed_service import run_full_seed

router = APIRouter()


@router.post("/seed")
def seed_demo_data(db: Session = Depends(get_db)) -> dict:
    return run_full_seed(db)
