"""
Mission Management REST Endpoints
"""
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json

from app.database.session import get_db
from app.models.mission import MissionModel
from app.models.mission_recommendation import MissionRecommendationModel
from app.models.user import UserModel
from app.core.auth import require_roles, require_viewer, require_operator
from app.repositories.event_repository import EventRepository
from app.services.mission_service import MissionService
from app.services.mission_planning_service import MissionPlanningService
from app.schemas.mission import (
    MissionResponse,
    MissionListResponse,
    MissionCreateRequest,
    MissionAssignRequest,
)
from app.schemas.dispatch import (
    MissionPlanRequest,
    MissionRecommendationResponse,
    RecommendationApprovalRequest,
    RecommendationRejectionRequest,
)
from app.core.exceptions import AquaCrewException

router = APIRouter()


def _format_recommendation(rec: MissionRecommendationModel) -> Dict[str, Any]:
    waypoints = []
    if rec.route_waypoints_json:
        try:
            waypoints = json.loads(rec.route_waypoints_json)
        except Exception:
            waypoints = []

    segments = []
    if rec.route_segments_json:
        try:
            segments = json.loads(rec.route_segments_json)
        except Exception:
            segments = []

    factors = {}
    if rec.contributing_factors:
        try:
            factors = json.loads(rec.contributing_factors)
        except Exception:
            factors = {}

    return {
        "id": rec.id,
        "detection_id": rec.detection_id,
        "pipeline_segment_id": rec.pipeline_segment_id,
        "recommended_rover_id": rec.recommended_rover_id,
        "recommended_rover_name": rec.recommended_rover_name,
        "priority_score": rec.priority_score,
        "priority_category": rec.priority_category,
        "status": rec.status,
        "route_distance_m": rec.route_distance_m,
        "estimated_duration_s": rec.estimated_duration_s,
        "estimated_energy_pct": rec.estimated_energy_pct,
        "battery_reserve_after_pct": rec.battery_reserve_after_pct,
        "destination_lat": rec.destination_lat,
        "destination_lng": rec.destination_lng,
        "localization_uncertainty_m": rec.localization_uncertainty_m,
        "waypoints": waypoints,
        "segments_traversed": segments,
        "contributing_factors": factors,
        "explanation": rec.explanation or "",
        "assigned_mission_id": rec.assigned_mission_id,
        "rejection_reason": rec.rejection_reason,
        "operator_notes": rec.operator_notes,
        "created_at": rec.created_at,
        "is_simulated": True,
        "source": rec.source,
    }


@router.post("/plan", response_model=MissionRecommendationResponse, summary="Generate autonomous mission recommendation for an AI leak detection")
def plan_mission_for_detection(
    req: MissionPlanRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    rec = MissionPlanningService.plan_mission_for_detection(
        db,
        detection_id=req.detection_id,
        preferred_rover_id=req.preferred_rover_id,
        priority_override=req.priority_override,
    )
    return _format_recommendation(rec)


@router.get("/recommendations", response_model=List[MissionRecommendationResponse], summary="List all mission recommendations")
def list_recommendations(
    status: Optional[str] = Query(None, description="Filter by status: PENDING_APPROVAL, APPROVED, REJECTED, CANCELLED"),
    priority: Optional[str] = Query(None, description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    recs = MissionPlanningService.list_recommendations(db, status=status, priority=priority, limit=limit)
    return [_format_recommendation(r) for r in recs]


@router.get("/recommendations/{recommendation_id}", response_model=MissionRecommendationResponse, summary="Get mission recommendation details")
def get_recommendation(
    recommendation_id: str = Path(..., description="Recommendation ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    rec = MissionPlanningService.get_recommendation_by_id(db, recommendation_id)
    if not rec:
        raise AquaCrewException(status_code=404, code="RECOMMENDATION_NOT_FOUND", message=f"Recommendation {recommendation_id} not found.")
    return _format_recommendation(rec)


@router.post("/recommendations/{recommendation_id}/approve", summary="Human operator approves recommendation and dispatches rover")
async def approve_recommendation(
    recommendation_id: str = Path(..., description="Recommendation ID"),
    body: Optional[RecommendationApprovalRequest] = None,
    current_user: UserModel = Depends(require_roles(["OPERATOR", "ENGINEER", "ADMINISTRATOR"])),
    db: Session = Depends(get_db),
):
    op_id = current_user.id
    notes = body.notes if body else None
    return await MissionPlanningService.approve_recommendation(
        db, recommendation_id=recommendation_id, operator_id=op_id, notes=notes
    )


@router.post("/recommendations/{recommendation_id}/reject", response_model=MissionRecommendationResponse, summary="Human operator rejects recommendation with documented reason")
def reject_recommendation(
    recommendation_id: str = Path(..., description="Recommendation ID"),
    body: RecommendationRejectionRequest = ...,
    current_user: UserModel = Depends(require_roles(["OPERATOR", "ENGINEER", "ADMINISTRATOR"])),
    db: Session = Depends(get_db),
):
    rec = MissionPlanningService.reject_recommendation(
        db,
        recommendation_id=recommendation_id,
        reason=body.rejection_reason,
        operator_notes=body.operator_notes,
    )
    return _format_recommendation(rec)


@router.post("/recommendations/{recommendation_id}/recalculate", response_model=MissionRecommendationResponse, summary="Recalculate route and rover suitability for a recommendation")
def recalculate_recommendation(
    recommendation_id: str = Path(..., description="Recommendation ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    rec = MissionPlanningService.recalculate_recommendation(db, recommendation_id=recommendation_id)
    return _format_recommendation(rec)


def mission_model_to_schema(mission: MissionModel) -> MissionResponse:
    return MissionResponse(
        isSimulated=mission.is_simulated,
        source="VIRTUAL_SIMULATION_ENGINE",
        simulatedAt=mission.updated_at or datetime.now(timezone.utc),
        id=mission.id,
        assignedRoverId=mission.assigned_rover_id or "",
        assignedRoverName=mission.assigned_rover_name or "",
        missionType=mission.mission_type,
        progressPercentage=mission.progress_percentage,
        status=mission.status,
        startTime=mission.start_time,
        estimatedCompletionTime=mission.estimated_completion_time,
        targetSegmentId=mission.target_segment_id,
        waypointCount=mission.waypoint_count,
        completedWaypoints=mission.completed_waypoints,
    )


@router.get("", response_model=MissionListResponse, summary="List all missions")
def list_missions(
    status: Optional[str] = Query(None, description="Filter by mission status: In Progress, Scheduled, Paused, Completed, Cancelled"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    missions = MissionService.list_missions(db, status=status)
    return MissionListResponse(
        success=True,
        total=len(missions),
        missions=[mission_model_to_schema(m) for m in missions],
    )


@router.get("/{mission_id}", response_model=MissionResponse, summary="Get mission details by ID")
def get_mission(
    mission_id: str = Path(..., description="Mission ID (e.g. MSN-2026-042)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    mission = MissionService.get_mission_by_id(db, mission_id)
    if not mission:
        raise AquaCrewException(status_code=404, code="MISSION_NOT_FOUND", message=f"Mission {mission_id} not found.")
    return mission_model_to_schema(mission)


@router.post("", response_model=MissionResponse, summary="Create a new scheduled inspection mission")
def create_mission(
    mission_in: MissionCreateRequest = ...,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    model = MissionService.create_mission(db, mission_in.model_dump())
    return mission_model_to_schema(model)


@router.post("/{mission_id}/assign", summary="Assign an available IDLE rover to a mission")
async def assign_rover_to_mission(
    mission_id: str = Path(..., description="Mission ID"),
    assign_in: MissionAssignRequest = ...,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    result = await MissionService.assign_mission(db, mission_id=mission_id, rover_id=assign_in.rover_id)
    return result


@router.post("/{mission_id}/start", summary="Start mission execution")
async def start_mission(
    mission_id: str = Path(..., description="Mission ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    return await MissionService.update_mission_status(db, mission_id, "In Progress", "Operator started mission")


@router.post("/{mission_id}/pause", summary="Pause mission execution")
async def pause_mission(
    mission_id: str = Path(..., description="Mission ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    return await MissionService.update_mission_status(db, mission_id, "Paused", "Operator paused mission")


@router.post("/{mission_id}/resume", summary="Resume paused mission")
async def resume_mission(
    mission_id: str = Path(..., description="Mission ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    return await MissionService.update_mission_status(db, mission_id, "In Progress", "Operator resumed mission")


@router.post("/{mission_id}/cancel", summary="Cancel mission")
async def cancel_mission(
    mission_id: str = Path(..., description="Mission ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    return await MissionService.update_mission_status(db, mission_id, "Cancelled", "Operator cancelled mission")


@router.get("/{mission_id}/route", summary="Get planned route waypoints for a mission")
def get_mission_route(
    mission_id: str = Path(..., description="Mission ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    mission = MissionService.get_mission_by_id(db, mission_id)
    if not mission:
        raise AquaCrewException(status_code=404, code="MISSION_NOT_FOUND", message=f"Mission {mission_id} not found.")

    waypoints = []
    if mission.route_waypoints_json:
        try:
            waypoints = json.loads(mission.route_waypoints_json)
        except Exception:
            waypoints = []

    return {
        "mission_id": mission.id,
        "target_segment_id": mission.target_segment_id,
        "assigned_rover_id": mission.assigned_rover_id,
        "route_distance_m": mission.route_distance_m,
        "waypoint_count": len(waypoints),
        "waypoints": waypoints,
        "is_simulated": True,
    }


@router.get("/{mission_id}/progress", summary="Get mission real-time execution progress")
def get_mission_progress(
    mission_id: str = Path(..., description="Mission ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    mission = MissionService.get_mission_by_id(db, mission_id)
    if not mission:
        raise AquaCrewException(status_code=404, code="MISSION_NOT_FOUND", message=f"Mission {mission_id} not found.")

    return {
        "mission_id": mission.id,
        "status": mission.status,
        "progress_percentage": mission.progress_percentage,
        "inspected_distance_m": mission.inspected_distance_m or 0.0,
        "total_distance_m": mission.route_distance_m or 1000.0,
        "completed_waypoints": mission.completed_waypoints,
        "total_waypoints": mission.waypoint_count,
        "start_time": mission.start_time,
        "estimated_completion_time": mission.estimated_completion_time,
        "is_simulated": True,
    }


@router.get("/{mission_id}/events", summary="Get audit events associated with a mission")
def get_mission_events(
    mission_id: str = Path(..., description="Mission ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    events = EventRepository.get_events(db, limit=50)
    # Filter by mention of mission_id in details
    mission_events = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "details": e.details,
            "rover_id": e.rover_id,
            "mission_id": e.mission_id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else "",
        }
        for e in events
        if (e.mission_id == mission_id) or (mission_id in (e.details or ""))
    ]
    return {
        "mission_id": mission_id,
        "total_events": len(mission_events),
        "events": mission_events,
        "is_simulated": True,
    }

