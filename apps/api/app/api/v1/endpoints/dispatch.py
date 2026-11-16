"""
AQUA CREW — Autonomous Dispatch & Fleet Suitability Endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.database.session import get_db
from app.repositories.rover_repository import RoverRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.services.rover_selection_service import RoverSelectionService
from app.models.user import UserModel
from app.core.auth import require_viewer
from app.schemas.dispatch import (
    DispatchEvaluationRequest,
    DispatchEvaluationResponse,
    RoverSuitability,
)

router = APIRouter()


@router.get("/eligible-rovers", response_model=List[RoverSuitability])
def get_eligible_rovers(
    target_segment_id: Optional[str] = Query("PIPE-SEC-4B-92", description="Target pipeline segment ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Evaluates and ranks all fleet rovers for availability and battery readiness.
    """
    pipe = PipelineRepository.get_by_id(db, target_segment_id)
    target_lat, target_lng = 40.7128, -74.0060
    pipe_meta = None

    if pipe:
        coords = json.loads(pipe.coordinates_json)
        mid = coords[len(coords) // 2]
        target_lng, target_lat = mid[0], mid[1]
        pipe_meta = {"category": pipe.category, "diameter_mm": pipe.diameter_mm}

    rovers = RoverRepository.get_all(db)
    eligible, ineligible = RoverSelectionService.rank_rovers_for_target(
        rovers, target_lat, target_lng, pipe_meta
    )
    return eligible + ineligible


@router.post("/evaluate", response_model=DispatchEvaluationResponse)
def evaluate_fleet_dispatch(
    req: DispatchEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Calculates detailed battery feasibility, proximity, and suitability scores for all fleet rovers
    against target pipeline segment or coordinates.
    """
    pipe = PipelineRepository.get_by_id(db, req.pipeline_segment_id)
    target_lat = req.target_lat or 40.7128
    target_lng = req.target_lng or -74.0060
    pipe_meta = None

    if pipe:
        coords = json.loads(pipe.coordinates_json)
        mid = coords[len(coords) // 2]
        if req.target_lat is None or req.target_lng is None:
            target_lng, target_lat = mid[0], mid[1]
        pipe_meta = {"category": pipe.category, "diameter_mm": pipe.diameter_mm}

    rovers = RoverRepository.get_all(db)
    eligible, ineligible = RoverSelectionService.rank_rovers_for_target(
        rovers, target_lat, target_lng, pipe_meta
    )

    return DispatchEvaluationResponse(
        pipeline_segment_id=req.pipeline_segment_id,
        eligible_rovers=eligible,
        ineligible_rovers=ineligible,
        is_simulated=True,
    )

