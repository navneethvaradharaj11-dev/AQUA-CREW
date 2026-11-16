"""
AQUA CREW — Infrastructure Intelligence & Geospatial Risk Prediction API Endpoints (Task 11)
Provides unified REST interfaces for pipeline vulnerability profiles, spatial incident clustering,
geographic risk zones, temporal trends, predictive forecasts, and prioritized inspection dispatch.
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database.session import get_db
from app.schemas.infrastructure_intelligence import (
    InfrastructureOverviewResponse,
    PipelineVulnerabilityListResponse,
    SegmentDeepDiveResponse,
    SpatialClusterItem,
    GeographicRiskZoneItem,
    HeatmapPointItem,
    TemporalTrendItem,
    PredictionItem,
    InspectionPriorityItem,
    AcknowledgeInspectionRequest,
    DismissInspectionRequest,
    RequestInspectionRequest,
    InspectionDispatchResponse,
)
from app.services.infrastructure_intelligence.infrastructure_intelligence_service import InfrastructureIntelligenceService
from app.services.infrastructure_intelligence.inspection_priority_service import InspectionPriorityService
from app.models.user import UserModel
from app.core.auth import require_viewer, require_operator

router = APIRouter()


@router.get("/overview", response_model=InfrastructureOverviewResponse, summary="Infrastructure Intelligence Overview")
def get_overview(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns executive-level infrastructure health summary, high risk counts,
    active clusters, deteriorating asset metrics, and key focus targets.
    """
    return InfrastructureIntelligenceService.get_overview(db)


@router.post("/assess", summary="Trigger Full Intelligence Assessment Pipeline")
def trigger_assessment(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Runs complete vulnerability scoring, spatial clustering, trend computation,
    and inspection queue synchronization.
    """
    return InfrastructureIntelligenceService.run_assessment(db)


@router.get("/segments", response_model=PipelineVulnerabilityListResponse, summary="List Pipeline Vulnerability Profiles")
def list_segments(
    risk_level: Optional[str] = Query(None, description="Filter by risk category: VERY_LOW, LOW, MODERATE, HIGH, CRITICAL"),
    zone: Optional[str] = Query(None, description="Filter by pressure zone ID (e.g. PZ-01)"),
    trend: Optional[str] = Query(None, description="Filter by trend direction: DETERIORATING, STABLE, IMPROVING"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves paginated pipeline vulnerability profiles with multi-dimensional filtering.
    """
    return InfrastructureIntelligenceService.get_segments(
        db=db,
        risk_level=risk_level,
        zone=zone,
        trend=trend,
        limit=limit,
        offset=offset,
    )


@router.get("/segments/{segment_id}", response_model=SegmentDeepDiveResponse, summary="Segment Vulnerability Deep Dive")
def get_segment_deep_dive(
    segment_id: str = Path(..., description="Pipeline segment identifier"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns granular 4-factor breakdown (Hydraulic, Structural, Incident, Environmental),
    data completeness, uncertainty margins, predictive forecasts, and inspection queue status.
    """
    return InfrastructureIntelligenceService.get_segment_deep_dive(db, segment_id)


@router.get("/risk-assessments", summary="List Detailed Risk Assessments")
def get_risk_assessments(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns multi-horizon risk projections and mitigation urgencies.
    """
    return InfrastructureIntelligenceService.get_predictions(db)


@router.get("/heatmap", response_model=List[HeatmapPointItem], summary="Geospatial Risk Heatmap Points")
def get_heatmap(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns weighted coordinates along pipeline vertices and cluster centroids
    for GIS heatmap and risk gradient visualization.
    """
    return InfrastructureIntelligenceService.get_heatmap(db)


@router.get("/clusters", response_model=List[SpatialClusterItem], summary="Spatial Incident Clusters")
def get_clusters(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns active density-based incident clusters, centroids, radii,
    incident counts, and dominant pipe materials.
    """
    return InfrastructureIntelligenceService.get_clusters(db)


@router.get("/zones", response_model=List[GeographicRiskZoneItem], summary="Geographic Risk Zones")
def get_zones(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns operational geographic risk zones with aggregated vulnerability metrics.
    """
    return InfrastructureIntelligenceService.get_zones(db)


@router.get("/trends", response_model=List[TemporalTrendItem], summary="Temporal Deterioration Trends")
def get_trends(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns 24-hour, 7-day, and 30-day deterioration deltas and velocity classifications.
    """
    return InfrastructureIntelligenceService.get_trends(db)


@router.get("/predictions", response_model=List[PredictionItem], summary="Predictive Risk Projections")
def get_predictions(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns future risk projections, drivers, and mitigation urgencies across 24h, 7d, and 30d.
    """
    return InfrastructureIntelligenceService.get_predictions(db)


@router.get("/inspection-priorities", response_model=List[InspectionPriorityItem], summary="Inspection Prioritization Queue")
def get_inspection_priorities(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, ACKNOWLEDGED, DISPATCHED, DISMISSED"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns prioritized queue of inspection targets ranked by urgency and consequence.
    """
    return InfrastructureIntelligenceService.get_inspection_priorities(db, status=status)


def _format_priority_model(r) -> Dict[str, Any]:
    import json
    reasons = []
    if r.reasons:
        try:
            reasons = json.loads(r.reasons) if isinstance(r.reasons, str) else r.reasons
        except Exception:
            reasons = [str(r.reasons)]
    return {
        "id": r.id,
        "pipeline_segment_id": r.pipeline_segment_id,
        "segment_name": r.segment_name,
        "priority_score": r.priority_score,
        "priority_level": r.priority_level,
        "status": r.status,
        "target_latitude": r.target_latitude,
        "target_longitude": r.target_longitude,
        "reasons": reasons,
        "suggested_action": r.suggested_action,
        "assigned_rover_id": r.assigned_rover_id,
        "mission_recommendation_id": r.mission_recommendation_id,
        "reviewed_by": r.reviewed_by,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        "operator_notes": r.operator_notes,
        "dismissal_reason": r.dismissal_reason,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "is_simulated": r.is_simulated,
    }


@router.post("/inspection-priorities/{priority_id}/acknowledge", response_model=InspectionPriorityItem, summary="Acknowledge Inspection Target")
def acknowledge_priority(
    priority_id: str = Path(..., description="Inspection priority record ID"),
    payload: AcknowledgeInspectionRequest = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Operator acknowledges an inspection target in the queue.
    """
    operator = (payload.operator_name if payload and payload.operator_name else None) or current_user.username
    notes = payload.notes if payload else None
    res = InspectionPriorityService.acknowledge_priority(db, priority_id, operator, notes)
    return _format_priority_model(res)


@router.post("/inspection-priorities/{priority_id}/dismiss", response_model=InspectionPriorityItem, summary="Dismiss Inspection Target")
def dismiss_priority(
    priority_id: str = Path(..., description="Inspection priority record ID"),
    payload: DismissInspectionRequest = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Operator dismisses an inspection target with a stated reason.
    """
    operator = (payload.operator_name if payload and payload.operator_name else None) or current_user.username
    reason = payload.reason if payload else "Dismissed by operator after inspection review."
    res = InspectionPriorityService.dismiss_priority(db, priority_id, operator, reason)
    return _format_priority_model(res)


@router.post("/inspection-priorities/{priority_id}/request-inspection", response_model=InspectionDispatchResponse, summary="Request Rover Inspection Dispatch")
def request_inspection(
    priority_id: str = Path(..., description="Inspection priority record ID"),
    payload: RequestInspectionRequest = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Generates an autonomous rover inspection mission recommendation.
    Enforces human operator review gate (operator_approval_required: true).
    """
    operator = (payload.operator_name if payload and payload.operator_name else None) or current_user.username
    preferred_rover = payload.preferred_rover_id if payload else None
    notes = payload.notes if payload else None
    return InspectionPriorityService.request_inspection(
        db=db,
        priority_id=priority_id,
        operator_name=operator,
        preferred_rover_id=preferred_rover,
        notes=notes,
    )
