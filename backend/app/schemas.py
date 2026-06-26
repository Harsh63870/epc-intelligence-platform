"""Pydantic schemas for API responses."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tier_target: str
    location: str
    status: str
    created_at: datetime | None = None


class HealthOut(BaseModel):
    status: str
    service: str
    database: str


class DashboardMetrics(BaseModel):
    active_ncs: int = 0
    open_rfis: int = 0
    schedule_risks: int = 0
    at_risk_shipments: int = 0
    commissioning_progress_pct: float = 0.0
    hours_saved_week: float = 0.0
