"""
AQUA CREW — Inspection Intelligence & Multi-Rover Orchestration API Endpoints (Task 15)
Prefix: /api/v1/inspection-intelligence
Enforces zero-trust JWT authentication and Task 13.6 role-based access control.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime, timezone

from app.database.session import get_db
from app.models.user import UserModel
from app.core.auth import get_current_user, require_operator, require_viewer, require_engineer
from app.schemas.inspection_intelligence import (
    InspectionRecommendationSchema,
    RoverSuitabilitySchema,
    InspectionPlanSchema,
    GeneratePlanRequest,
    PlanApprovalRequest,
    PlanRejectionRequest,
    RouteAdaptationRequest,
    InspectionExecutionProgressSchema,
    InspectionReportSchema,
    InspectionPlanTargetSchema,
)
from app.repositories.inspection_intelligence_repository import InspectionIntelligenceRepository
from app.repositories.rover_repository import RoverRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.services.inspection_intelligence import (
    InspectionIntelligenceService,
    RoverAllocationService,
    AdaptiveRouteService,
    InspectionExecutionEngine,
)


router = APIRouter()


@router.get("/status")
def get_inspection_status():
    """
    Returns inspection intelligence engine operational readiness.
    """
    return {
        "status": "OPERATIONAL",
        "module": "AUTONOMOUS_INSPECTION_INTELLIGENCE",
        "task": "TASK_15",
        "supported_methods": [
            "ACOUSTIC_CORRELATION",
            "VISUAL_CCTV",
            "THERMAL_INFRARED",
            "MULTI_SENSOR_CRAWLER",
            "ULTRASONIC_THICKNESS",
        ],
        "is_simulated": True,
        "provenance": "VIRTUAL_SIMULATION_BACKEND",
    }


# -----------------------------------------------------------------------------
# Recommendations
# -----------------------------------------------------------------------------
@router.get("/recommendations", response_model=List[InspectionRecommendationSchema])
def list_recommendations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by approval status"),
    priority_filter: Optional[str] = Query(None, alias="priority", description="Filter by priority category"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves ranked inspection recommendations. Requires VIEWER role.
    """
    recs = InspectionIntelligenceRepository.list_recommendations(
        db, status=status_filter, priority=priority_filter, limit=limit
    )

    if not recs:
        # If database table is empty, generate initial set
        schema_list = InspectionIntelligenceService.generate_recommendations_for_all(db)
        if status_filter:
            schema_list = [r for r in schema_list if r.human_approval_status == status_filter.upper()]
        if priority_filter:
            schema_list = [r for r in schema_list if r.priority_category == priority_filter.upper()]
        return schema_list[:limit]

    out: List[InspectionRecommendationSchema] = []
    for m in recs:
        out.append(InspectionRecommendationSchema(
            id=m.id,
            pipeline_segment_id=m.pipeline_segment_id,
            segment_name=m.segment_name,
            priority_score=m.priority_score,
            priority_category=m.priority_category,
            urgency_factors=json.loads(m.urgency_factors_json or "{}"),
            supporting_evidence=json.loads(m.supporting_evidence_json or "[]"),
            primary_classification=m.primary_classification,
            confidence=m.confidence,
            uncertainty_radius_m=m.uncertainty_radius_m,
            recommended_method=m.recommended_method,
            estimated_duration_minutes=m.estimated_duration_minutes,
            required_rover_capabilities=json.loads(m.required_rover_capabilities_json or "[]"),
            recommended_action=m.recommended_action,
            human_approval_status=m.human_approval_status,
            rejection_reason=m.rejection_reason,
            approved_by=m.approved_by,
            approved_at=m.approved_at.isoformat() if m.approved_at else None,
            created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
            is_simulated=m.is_simulated,
        ))
    return out


@router.get("/recommendations/{rec_id}", response_model=InspectionRecommendationSchema)
def get_recommendation_details(
    rec_id: str = Path(..., description="Recommendation ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves full details and supporting evidence for a single inspection recommendation.
    """
    m = InspectionIntelligenceRepository.get_recommendation(db, rec_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Recommendation '{rec_id}' not found.")

    return InspectionRecommendationSchema(
        id=m.id,
        pipeline_segment_id=m.pipeline_segment_id,
        segment_name=m.segment_name,
        priority_score=m.priority_score,
        priority_category=m.priority_category,
        urgency_factors=json.loads(m.urgency_factors_json or "{}"),
        supporting_evidence=json.loads(m.supporting_evidence_json or "[]"),
        primary_classification=m.primary_classification,
        confidence=m.confidence,
        uncertainty_radius_m=m.uncertainty_radius_m,
        recommended_method=m.recommended_method,
        estimated_duration_minutes=m.estimated_duration_minutes,
        required_rover_capabilities=json.loads(m.required_rover_capabilities_json or "[]"),
        recommended_action=m.recommended_action,
        human_approval_status=m.human_approval_status,
        rejection_reason=m.rejection_reason,
        approved_by=m.approved_by,
        approved_at=m.approved_at.isoformat() if m.approved_at else None,
        created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
        is_simulated=m.is_simulated,
    )


@router.post("/recommendations/generate", response_model=List[InspectionRecommendationSchema])
def generate_recommendations(
    min_urgency: float = Query(30.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Forces recalculation of inspection recommendations across all network pipelines.
    Requires OPERATOR or higher role.
    """
    return InspectionIntelligenceService.generate_recommendations_for_all(db, min_urgency=min_urgency)


# -----------------------------------------------------------------------------
# Rover Suitability
# -----------------------------------------------------------------------------
@router.get("/rovers/suitability", response_model=List[RoverSuitabilitySchema])
def get_fleet_suitability_for_target(
    target_lat: float = Query(..., description="Target latitude"),
    target_lng: float = Query(..., description="Target longitude"),
    method: str = Query("ACOUSTIC_CORRELATION", description="Required inspection method"),
    duration_minutes: int = Query(30, ge=5, le=180),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Evaluates virtual rover fleet suitability for a target location and method.
    """
    rovers = RoverRepository.get_all(db)
    eligible, ineligible = RoverAllocationService.rank_fleet_for_target(
        rovers=rovers,
        target_lat=target_lat,
        target_lng=target_lng,
        required_method=method, # type: ignore
        inspection_duration_minutes=duration_minutes,
    )
    return eligible + ineligible


# -----------------------------------------------------------------------------
# Multi-Rover Inspection Plans
# -----------------------------------------------------------------------------
@router.post("/plans/generate", response_model=InspectionPlanSchema)
def generate_inspection_plan(
    req: GeneratePlanRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Generates a coordinated multi-rover inspection plan across top urgent recommendations.
    Requires OPERATOR or higher role.
    """
    # 1. Fetch recommendations to cover
    all_recs = InspectionIntelligenceRepository.list_recommendations(db, status="PENDING_APPROVAL", limit=20)
    if not all_recs:
        schema_recs = InspectionIntelligenceService.generate_recommendations_for_all(db)
    else:
        schema_recs = [
            InspectionRecommendationSchema(
                id=m.id,
                pipeline_segment_id=m.pipeline_segment_id,
                segment_name=m.segment_name,
                priority_score=m.priority_score,
                priority_category=m.priority_category,
                urgency_factors=json.loads(m.urgency_factors_json or "{}"),
                supporting_evidence=json.loads(m.supporting_evidence_json or "[]"),
                confidence=m.confidence,
                uncertainty_radius_m=m.uncertainty_radius_m,
                recommended_method=m.recommended_method, # type: ignore
                estimated_duration_minutes=m.estimated_duration_minutes,
                required_rover_capabilities=json.loads(m.required_rover_capabilities_json or "[]"),
                recommended_action=m.recommended_action,
                created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
            )
            for m in all_recs
        ]

    if req.recommendation_ids:
        schema_recs = [r for r in schema_recs if r.id in req.recommendation_ids]

    if not schema_recs:
        raise HTTPException(status_code=400, detail="No active recommendations available to formulate inspection plan.")

    # 2. Build Plan Targets
    targets: List[InspectionPlanTargetSchema] = []
    unreachable_targets: List[str] = []
    all_pipelines = PipelineRepository.get_all(db)

    for rec in schema_recs:
        seg = PipelineRepository.get_by_id(db, rec.pipeline_segment_id)
        if seg and seg.coordinates_json:
            coords = json.loads(seg.coordinates_json)
            midpoint = coords[len(coords) // 2] if coords else [-74.006, 40.712]
        else:
            midpoint = [-74.006, 40.712]

        is_connected = AdaptiveRouteService.check_reachability(db, midpoint, all_pipelines)
        if not is_connected:
            unreachable_targets.append(rec.pipeline_segment_id)
            continue

        targets.append(InspectionPlanTargetSchema(
            target_id=f"TGT-{rec.pipeline_segment_id}",
            pipeline_segment_id=rec.pipeline_segment_id,
            target_coordinates=midpoint,
            inspection_method=rec.recommended_method,
            priority_score=rec.priority_score,
            estimated_duration_minutes=rec.estimated_duration_minutes,
        ))

    # 3. Multi-Rover Allocation
    alloc_map, unallocated = RoverAllocationService.allocate_multi_rover_targets(
        db=db,
        targets=targets,
        preferred_rover_ids=req.preferred_rover_ids,
        max_targets_per_rover=req.max_targets_per_rover,
        safety_reserve_pct=req.battery_safety_reserve_pct,
    )

    if not alloc_map:
        raise HTTPException(
            status_code=400,
            detail="No available rovers could be allocated. Verify rovers are ONLINE, IDLE, and sufficiently charged.",
        )

    # 4. Generate Routes for Each Rover
    allocations_list = []
    for r_id, rover_targets in alloc_map.items():
        rover = RoverRepository.get_by_id(db, r_id)
        if rover:
            route_alloc = AdaptiveRouteService.plan_multi_target_route(
                db=db,
                rover=rover,
                targets=rover_targets,
                safety_reserve_pct=req.battery_safety_reserve_pct,
            )
            allocations_list.append(route_alloc)

    plan_id = f"INSP-PLAN-{uuid.uuid4().hex[:8].upper()}"
    plan_schema = InspectionPlanSchema(
        id=plan_id,
        plan_name=req.plan_name or f"Autonomous Inspection Campaign ({len(targets)} targets)",
        allocations=allocations_list,
        unreachable_targets=unreachable_targets + unallocated,
        conflict_checks_passed=True,
        total_rovers_assigned=len(allocations_list),
        total_targets_covered=sum(len(a.assigned_targets) for a in allocations_list),
        human_approval_status="PENDING_APPROVAL",
        created_at=datetime.now(timezone.utc).isoformat(),
        is_simulated=True,
    )

    InspectionIntelligenceRepository.save_plan(db, plan_schema)
    return plan_schema


@router.get("/plans", response_model=List[InspectionPlanSchema])
def list_inspection_plans(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists generated inspection plans.
    """
    models = InspectionIntelligenceRepository.list_plans(db, limit=limit)
    out: List[InspectionPlanSchema] = []
    for m in models:
        out.append(InspectionPlanSchema(
            id=m.id,
            plan_name=m.plan_name,
            allocations=json.loads(m.allocations_json),
            unreachable_targets=json.loads(m.unreachable_targets_json or "[]"),
            conflict_checks_passed=m.conflict_checks_passed,
            total_rovers_assigned=m.total_rovers_assigned,
            total_targets_covered=m.total_targets_covered,
            human_approval_status=m.human_approval_status, # type: ignore
            rejection_reason=m.rejection_reason,
            approved_by=m.approved_by,
            approved_at=m.approved_at.isoformat() if m.approved_at else None,
            created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
            is_simulated=m.is_simulated,
        ))
    return out


@router.get("/plans/{plan_id}", response_model=InspectionPlanSchema)
def get_inspection_plan(
    plan_id: str = Path(..., description="Plan ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves details of an inspection plan.
    """
    m = InspectionIntelligenceRepository.get_plan(db, plan_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found.")

    return InspectionPlanSchema(
        id=m.id,
        plan_name=m.plan_name,
        allocations=json.loads(m.allocations_json),
        unreachable_targets=json.loads(m.unreachable_targets_json or "[]"),
        conflict_checks_passed=m.conflict_checks_passed,
        total_rovers_assigned=m.total_rovers_assigned,
        total_targets_covered=m.total_targets_covered,
        human_approval_status=m.human_approval_status, # type: ignore
        rejection_reason=m.rejection_reason,
        approved_by=m.approved_by,
        approved_at=m.approved_at.isoformat() if m.approved_at else None,
        created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
        is_simulated=m.is_simulated,
    )


@router.post("/plans/{plan_id}/approve", response_model=InspectionPlanSchema)
def approve_inspection_plan(
    plan_id: str = Path(..., description="Plan ID"),
    req: PlanApprovalRequest = Body(default_factory=PlanApprovalRequest),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Human operator approval of inspection plan. Requires OPERATOR or higher role.
    """
    m = InspectionIntelligenceRepository.atomically_approve_plan(
        db=db,
        plan_id=plan_id,
        operator_id=current_user.username,
        notes=req.operator_notes,
    )

    return InspectionPlanSchema(
        id=m.id,
        plan_name=m.plan_name,
        allocations=json.loads(m.allocations_json),
        unreachable_targets=json.loads(m.unreachable_targets_json or "[]"),
        conflict_checks_passed=m.conflict_checks_passed,
        total_rovers_assigned=m.total_rovers_assigned,
        total_targets_covered=m.total_targets_covered,
        human_approval_status=m.human_approval_status, # type: ignore
        approved_by=m.approved_by,
        approved_at=m.approved_at.isoformat() if m.approved_at else None,
        created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
        is_simulated=m.is_simulated,
    )


@router.post("/plans/{plan_id}/reject", response_model=InspectionPlanSchema)
def reject_inspection_plan(
    plan_id: str = Path(..., description="Plan ID"),
    req: PlanRejectionRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Human operator rejection of inspection plan. Requires OPERATOR or higher role.
    """
    m = InspectionIntelligenceRepository.atomically_reject_plan(
        db=db,
        plan_id=plan_id,
        operator_id=current_user.username,
        reason=req.rejection_reason,
    )

    return InspectionPlanSchema(
        id=m.id,
        plan_name=m.plan_name,
        allocations=json.loads(m.allocations_json),
        unreachable_targets=json.loads(m.unreachable_targets_json or "[]"),
        conflict_checks_passed=m.conflict_checks_passed,
        total_rovers_assigned=m.total_rovers_assigned,
        total_targets_covered=m.total_targets_covered,
        human_approval_status=m.human_approval_status, # type: ignore
        rejection_reason=m.rejection_reason,
        created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
        is_simulated=m.is_simulated,
    )


# -----------------------------------------------------------------------------
# Simulated Execution & Adaptive Route Updates
# -----------------------------------------------------------------------------
@router.post("/missions/{plan_id}/launch/{rover_id}", response_model=InspectionExecutionProgressSchema)
def launch_mission(
    plan_id: str = Path(..., description="Plan ID"),
    rover_id: str = Path(..., description="Rover ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Launches virtual rover inspection execution for an approved plan.
    Requires OPERATOR or higher role.
    """
    return InspectionExecutionEngine.start_mission_execution(db, plan_id=plan_id, rover_id=rover_id)


@router.post("/missions/{mission_id}/step", response_model=InspectionExecutionProgressSchema)
def advance_mission_step(
    mission_id: str = Path(..., description="Mission ID"),
    step_increment_m: float = Query(100.0, ge=10.0, le=500.0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Simulates advancement of rover along its inspection route by one step.
    Synthesizes sensor observations and checks safety thresholds.
    Requires OPERATOR or higher role.
    """
    return InspectionExecutionEngine.execute_next_step(db, mission_id=mission_id, step_increment_m=step_increment_m)


@router.post("/missions/{mission_id}/adapt-route", response_model=InspectionExecutionProgressSchema)
def adapt_mission_route(
    mission_id: str = Path(..., description="Mission ID"),
    req: RouteAdaptationRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Adapts remaining inspection route in response to a newly detected acoustic anomaly.
    Requires OPERATOR or higher role.
    """
    return InspectionExecutionEngine.trigger_adaptive_reroute(
        db=db,
        mission_id=mission_id,
        adaptation_reason=req.adaptation_reason,
        new_anomaly_coord=req.new_anomaly_coordinates,
        new_target_segment_id=req.new_target_segment_id,
    )


@router.get("/missions/{mission_id}/progress", response_model=InspectionExecutionProgressSchema)
def get_mission_progress(
    mission_id: str = Path(..., description="Mission ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves live execution progress, battery state, and sensor telemetry.
    """
    return InspectionExecutionEngine.get_progress(db, mission_id=mission_id)


# -----------------------------------------------------------------------------
# Evidence-Grounded Inspection Reports
# -----------------------------------------------------------------------------
@router.get("/reports", response_model=List[InspectionReportSchema])
def list_inspection_reports(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists completed inspection reports. Requires VIEWER role.
    """
    models = InspectionIntelligenceRepository.list_reports(db, limit=limit)
    out: List[InspectionReportSchema] = []
    for m in models:
        out.append(InspectionReportSchema(
            id=m.id,
            plan_id=m.plan_id,
            mission_id=m.mission_id,
            rover_id=m.rover_id,
            pipeline_segment_id=m.pipeline_segment_id,
            segment_name=m.segment_name,
            inspection_method=m.inspection_method, # type: ignore
            start_time=m.start_time,
            completion_time=m.completion_time,
            route_distance_m=m.route_distance_m,
            inspected_distance_m=m.inspected_distance_m,
            sensor_observations_count=m.sensor_observations_count,
            detected_anomalies=json.loads(m.detected_anomalies_json or "[]"),
            evidence_provenance=m.evidence_provenance, # type: ignore
            ai_classification=json.loads(m.ai_classification_json) if m.ai_classification_json else None,
            updated_infrastructure_risk=m.updated_infrastructure_risk,
            inspection_outcome=m.inspection_outcome, # type: ignore
            unresolved_uncertainties=json.loads(m.unresolved_uncertainties_json or "[]"),
            recommended_next_action=m.recommended_next_action,
            operator_review_status=m.operator_review_status, # type: ignore
            reviewed_by=m.reviewed_by,
            operator_notes=m.operator_notes,
            created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
            is_simulated=m.is_simulated,
        ))
    return out


@router.get("/reports/{report_id}", response_model=InspectionReportSchema)
def get_inspection_report(
    report_id: str = Path(..., description="Report ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves a single inspection report by ID.
    """
    m = InspectionIntelligenceRepository.get_report(db, report_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    return InspectionReportSchema(
        id=m.id,
        plan_id=m.plan_id,
        mission_id=m.mission_id,
        rover_id=m.rover_id,
        pipeline_segment_id=m.pipeline_segment_id,
        segment_name=m.segment_name,
        inspection_method=m.inspection_method, # type: ignore
        start_time=m.start_time,
        completion_time=m.completion_time,
        route_distance_m=m.route_distance_m,
        inspected_distance_m=m.inspected_distance_m,
        sensor_observations_count=m.sensor_observations_count,
        detected_anomalies=json.loads(m.detected_anomalies_json or "[]"),
        evidence_provenance=m.evidence_provenance, # type: ignore
        ai_classification=json.loads(m.ai_classification_json) if m.ai_classification_json else None,
        updated_infrastructure_risk=m.updated_infrastructure_risk,
        inspection_outcome=m.inspection_outcome, # type: ignore
        unresolved_uncertainties=json.loads(m.unresolved_uncertainties_json or "[]"),
        recommended_next_action=m.recommended_next_action,
        operator_review_status=m.operator_review_status, # type: ignore
        reviewed_by=m.reviewed_by,
        operator_notes=m.operator_notes,
        created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
        is_simulated=m.is_simulated,
    )


@router.post("/reports/{report_id}/review", response_model=InspectionReportSchema)
def review_inspection_report(
    report_id: str = Path(..., description="Report ID"),
    review_status: str = Query("REVIEWED", pattern="^(REVIEWED|ACTION_APPROVED)$"),
    notes: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Operator signs off on completed inspection report. Requires OPERATOR role.
    """
    m = InspectionIntelligenceRepository.get_report(db, report_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    m.operator_review_status = review_status
    m.reviewed_by = current_user.username
    m.operator_notes = notes
    db.commit()
    db.refresh(m)

    InspectionIntelligenceRepository.log_event(
        db,
        event_type="INSPECTION_REPORT_REVIEWED",
        user_id=current_user.username,
        details={"report_id": report_id, "review_status": review_status, "notes": notes},
    )

    return InspectionReportSchema(
        id=m.id,
        plan_id=m.plan_id,
        mission_id=m.mission_id,
        rover_id=m.rover_id,
        pipeline_segment_id=m.pipeline_segment_id,
        segment_name=m.segment_name,
        inspection_method=m.inspection_method, # type: ignore
        start_time=m.start_time,
        completion_time=m.completion_time,
        route_distance_m=m.route_distance_m,
        inspected_distance_m=m.inspected_distance_m,
        sensor_observations_count=m.sensor_observations_count,
        detected_anomalies=json.loads(m.detected_anomalies_json or "[]"),
        evidence_provenance=m.evidence_provenance, # type: ignore
        ai_classification=json.loads(m.ai_classification_json) if m.ai_classification_json else None,
        updated_infrastructure_risk=m.updated_infrastructure_risk,
        inspection_outcome=m.inspection_outcome, # type: ignore
        unresolved_uncertainties=json.loads(m.unresolved_uncertainties_json or "[]"),
        recommended_next_action=m.recommended_next_action,
        operator_review_status=m.operator_review_status, # type: ignore
        reviewed_by=m.reviewed_by,
        operator_notes=m.operator_notes,
        created_at=m.created_at.isoformat() if m.created_at else datetime.now(timezone.utc).isoformat(),
        is_simulated=m.is_simulated,
    )


# -----------------------------------------------------------------------------
# Operational Events
# -----------------------------------------------------------------------------
@router.get("/events")
def list_inspection_events(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists tamper-evident inspection operational events.
    """
    evts = InspectionIntelligenceRepository.list_events(db, limit=limit)
    return [
        {
            "id": e.id,
            "plan_id": e.plan_id,
            "mission_id": e.mission_id,
            "rover_id": e.rover_id,
            "event_type": e.event_type,
            "details": json.loads(e.details_json or "{}"),
            "user_id": e.user_id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in evts
    ]
