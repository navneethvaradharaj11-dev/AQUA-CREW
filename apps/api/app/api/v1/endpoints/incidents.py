"""
AQUA CREW — Unified Incident Management API Router (Task 19)
Provides REST endpoints for the 10-stage Master End-to-End Incident Lifecycle.
Enforces Zero-Trust RBAC:
- VIEWER: read-only incident list, detail, overview metrics.
- OPERATOR: create incidents, approve inspection missions, execute transitions.
- ENGINEER: certified engineering repair approvals, digital twin simulated resolutions.
- ADMIN: complete administrative authority.
Simulation-First: Hardware actuation strictly prohibited.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import UserModel
from app.core.auth import get_current_user, require_operator, require_viewer, require_engineer
from app.models.incident import UnifiedIncidentModel
from app.repositories.incident_repository import IncidentRepository
from app.schemas.incident import (
    UnifiedIncidentResponse,
    IncidentListResponse,
    IncidentCreateRequest,
    IncidentTransitionRequest,
    IncidentApprovalDecisionRequest,
    IncidentResolutionRequest,
    IncidentStatsOverview,
    MasterE2ERequest,
)
from app.services.incident_orchestration_service import (
    IncidentOrchestrationService,
    IncidentLifecycleError,
)
from app.modules.hardware_gateway import (
    HARDWARE_ACTUATION_ENABLED,
    HARDWARE_STATUS,
    PROHIBITED_ACTUATION_COMMANDS,
)


router = APIRouter()


@router.get("/status")
def get_incident_system_status():
    """
    Returns incident intelligence system status, simulation status, and safety invariants.
    """
    return {
        "status": "OPERATIONAL",
        "system": "UNIFIED_INCIDENT_INTELLIGENCE",
        "task": "TASK_19_COMPLETE_SYSTEM_INTEGRATION_AND_ACCEPTANCE",
        "hardware_status": HARDWARE_STATUS,
        "hardware_actuation_enabled": HARDWARE_ACTUATION_ENABLED,
        "hardware_actuation_strictly_blocked": True,
        "is_simulated": True,
    }


@router.get("/stats/overview", response_model=IncidentStatsOverview)
def get_incident_stats_overview(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns aggregated KPI metrics for the Unified Incident Command Center.
    Requires VIEWER or higher.
    """
    return IncidentRepository.get_incident_stats(db)


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    status: Optional[str] = Query(None, description="Filter by lifecycle status (e.g. DETECTED, TRIAGED, CLOSED)"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    category: Optional[str] = Query(None, description="Filter by category (ACOUSTIC_ANOMALY, BURST, etc.)"),
    dma_zone: Optional[str] = Query(None, description="Filter by DMA zone"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists unified incidents with optional filtering.
    Requires VIEWER or higher.
    """
    items, total = IncidentRepository.list_incidents(
        db=db,
        status=status,
        severity=severity,
        category=category,
        dma_zone=dma_zone,
        limit=limit,
        offset=offset,
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=UnifiedIncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    req: IncidentCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Creates a new unified incident record.
    Requires OPERATOR or higher.
    """
    incident = IncidentRepository.create_incident(
        db=db,
        title=req.title,
        pipeline_segment_id=req.pipeline_segment_id,
        latitude=req.latitude,
        longitude=req.longitude,
        description=req.description or "",
        category=req.category,
        severity=req.severity,
        priority=req.priority,
        dma_zone=req.dma_zone,
        detection_source=req.detection_source,
        sensor_ids=req.sensor_ids,
        ai_leak_probability=req.ai_leak_probability,
        ai_confidence=req.ai_confidence,
        hydraulic_headloss_delta=req.hydraulic_headloss_delta,
        estimated_loss_lps=req.estimated_loss_lps,
        risk_score=req.risk_score,
        created_by=current_user.username,
    )
    return incident


@router.get("/{incident_id}", response_model=UnifiedIncidentResponse)
def get_incident_by_id(
    incident_id: str = Path(..., description="Incident ID or Incident Code"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves full details of a unified incident, including audit events and approvals.
    Requires VIEWER or higher.
    """
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        incident = IncidentRepository.get_by_code(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found.",
        )
    return incident


@router.post("/{incident_id}/transition", response_model=UnifiedIncidentResponse)
def transition_incident_status(
    req: IncidentTransitionRequest,
    incident_id: str = Path(..., description="Incident ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Executes a valid lifecycle transition on an incident.
    Requires OPERATOR or higher.
    """
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    try:
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, req.target_status)
    except IncidentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    old_status = incident.lifecycle_status
    incident.lifecycle_status = req.target_status
    IncidentRepository.add_workflow_event(
        db=db,
        incident_id=incident.id,
        from_status=old_status,
        to_status=req.target_status,
        stage_number=2,
        action="LIFECYCLE_TRANSITION_MANUAL",
        actor_id=current_user.username,
        actor_role=current_user.role,
        notes=req.notes or f"Transitioned from {old_status} to {req.target_status}",
        payload=req.payload,
    )
    db.commit()
    db.refresh(incident)
    return incident


@router.post("/{incident_id}/approve", response_model=UnifiedIncidentResponse)
def approve_or_reject_incident_step(
    req: IncidentApprovalDecisionRequest,
    incident_id: str = Path(..., description="Incident ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Records a human operator or engineer approval decision.
    - INSPECTION_DISPATCH requires OPERATOR or higher.
    - REPAIR_PLAN requires ENGINEER or ADMIN.
    """
    user_role = current_user.role.upper()
    if req.approval_type == "REPAIR_PLAN":
        if user_role not in ["ENGINEER", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' is not authorized to approve repair plans. Requires ENGINEER or ADMIN.",
            )
        try:
            return IncidentOrchestrationService.execute_stage_9_certified_engineering_approval(
                db=db,
                incident_id=incident_id,
                engineer_id=current_user.username,
                engineer_role=user_role,
                approved=req.approved,
                comments=req.comments or ("Approved" if req.approved else "Rejected"),
            )
        except IncidentLifecycleError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    elif req.approval_type == "INSPECTION_DISPATCH":
        if user_role not in ["OPERATOR", "ENGINEER", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' is not authorized to approve inspection missions.",
            )
        try:
            return IncidentOrchestrationService.execute_stage_7_human_approval_and_inspection(
                db=db,
                incident_id=incident_id,
                operator_id=current_user.username,
                operator_role=user_role,
                approved=req.approved,
                comments=req.comments or ("Approved" if req.approved else "Rejected"),
            )
        except IncidentLifecycleError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported approval type '{req.approval_type}'.",
        )


@router.post("/{incident_id}/simulation-resolution", response_model=UnifiedIncidentResponse)
def execute_simulated_resolution(
    req: IncidentResolutionRequest,
    incident_id: str = Path(..., description="Incident ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_engineer),
):
    """
    Executes post-repair digital twin simulation verification and closes incident.
    Requires ENGINEER or higher.
    Strictly prohibits physical actuation.
    """
    # Safety verification
    for cmd in PROHIBITED_ACTUATION_COMMANDS:
        if cmd in req.verification_notes.upper():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"HARDWARE_ACTUATION_PROHIBITED: Command '{cmd}' involves physical actuation and is blocked.",
            )

    try:
        return IncidentOrchestrationService.execute_stage_10_simulated_resolution_and_closure(
            db=db,
            incident_id=incident_id,
            actor_id=current_user.username,
            actor_role=current_user.role,
            verification_notes=req.verification_notes,
        )
    except IncidentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/scenarios/master-e2e")
def run_master_acceptance_scenario(
    req: MasterE2ERequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Executes the complete 15-step Master Acceptance Scenario from sensor reading to closure.
    Requires OPERATOR or higher.
    """
    result = IncidentOrchestrationService.run_master_e2e_scenario(
        db=db,
        actor_id=current_user.username,
        actor_role=current_user.role,
        pipeline_segment_id=req.pipeline_segment_id or "PIPE-SEC-4B-92",
        acoustic_db=req.acoustic_db or 88.5,
    )
    return result


@router.post("/scenarios/demo-reset")
def reset_demonstration_scenario(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Resets the demonstration scenario and restores baseline seeded incidents.
    Does not delete unrelated user data.
    Requires OPERATOR or higher.
    """
    return IncidentOrchestrationService.reset_demo_scenario(db)


@router.get("/{incident_id}/report")
def get_incident_final_report(
    incident_id: str = Path(..., description="Incident ID or Incident Code"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns the comprehensive 15-step publication-grade Incident Report.
    Requires VIEWER or higher.
    """
    try:
        return IncidentOrchestrationService.generate_final_incident_report(db, incident_id)
    except IncidentLifecycleError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

