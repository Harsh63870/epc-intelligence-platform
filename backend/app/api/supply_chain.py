"""Supply chain API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.agents.supply_chain_agent import get_shipments, get_supply_alerts, log_shipment_check
from app.database import get_db

router = APIRouter(prefix="/supply-chain", tags=["supply-chain"])


@router.get("/shipments")
def shipments(project_id: int = Query(default=1), db: Session = Depends(get_db)) -> list[dict]:
    return get_shipments(db, project_id)


@router.get("/alerts")
def alerts(project_id: int = Query(default=1), db: Session = Depends(get_db)) -> list[dict]:
    return get_supply_alerts(db, project_id)


@router.post("/shipments/{shipment_id}/acknowledge")
def acknowledge_shipment(
    shipment_id: int,
    project_id: int = Query(default=1),
    db: Session = Depends(get_db),
) -> dict:
    log_shipment_check(db, project_id, shipment_id)
    return {"acknowledged": True, "shipment_id": shipment_id}
