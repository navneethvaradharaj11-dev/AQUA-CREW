"""
AQUA CREW — Prometheus Metrics HTTP Endpoint (Task 17)
Exposes aggregated application, security, simulation, and telemetry metrics.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.database.session import get_db
from app.core.metrics import metrics_collector
from app.websocket.connection_manager import ws_manager
from app.repositories.rover_repository import RoverRepository

router = APIRouter()


@router.get(
    "/metrics",
    summary="Prometheus Metrics Exposition",
    description="Returns standard Prometheus text format metrics.",
    response_class=Response,
)
def get_prometheus_metrics(db: Session = Depends(get_db)):
    # Measure db latency
    start_time = time.time()
    try:
        db.execute(text("SELECT 1"))
        db_latency = (time.time() - start_time) * 1000.0
    except Exception:
        db_latency = -1.0

    # Count active rovers
    active_rovers = 0
    try:
        rovers = RoverRepository.get_all(db)
        active_rovers = sum(1 for r in rovers if r.operating_state in ["MOVING", "INSPECTING", "RETURNING"])
    except Exception:
        pass

    content = metrics_collector.generate_prometheus_text(
        active_ws=ws_manager.client_count,
        active_rovers=active_rovers,
        db_latency_ms=max(0.0, db_latency),
    )

    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )

