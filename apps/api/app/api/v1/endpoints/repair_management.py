"""
AQUA CREW — Repair Planning & Management API Router (Task 16)
Provides REST endpoints for damage assessments, repair recommendations, resource planning,
cost estimates, virtual crew scheduling, digital twin simulations, workflow state transitions,
and post-repair cryptographic verifications.
Enforces Zero-Trust RBAC: VIEWER read-only, OPERATOR/ENGINEER for approvals and transitions.
"""
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import UserModel
from app.core.auth import get_current_user, require_operator, require_viewer, require_engineer
from app.core.exceptions import AquaCrewException
from app.schemas.repair_management import (
    DamageAssessmentSchema,
    DamageAssessmentCreateRequest,
    RepairRecommendationSchema,
    RepairPlanSchema,
    RepairPlanCreateRequest,
    RepairPlanApprovalRequest,
    RepairPlanRejectionRequest,
    RepairWorkflowTransitionRequest,
    RepairWorkflowEventSchema,
    RepairResourceItemSchema,
    RepairScheduleItemSchema,
    RepairVerificationSchema,
    RepairVerificationRequest,
    RepairOverviewSummarySchema,
    DigitalTwinRepairScenarioSchema,
    DigitalTwinRepairComparisonSchema,
    RepairCrewSchema,
)
from app.repositories.repair_repository import RepairRepository
from app.services.repair_intelligence import (
    DamageAssessmentEngine,
    RepairMethodEngine,
    ResourcePlanningEngine,
    CostEstimationEngine,
    RepairPrioritizationEngine,
    CrewSchedulingEngine,
    DigitalTwinRepairSimulator,
    RepairVerificationEngine,
    RepairIntelligenceService,
)


router = APIRouter()


@router.get("/status")
def get_repair_engine_status():
    """
    Returns repair intelligence engine operational status and module info.
    """
    return {
        "status": "OPERATIONAL",
        "module": "INTELLIGENT_REPAIR_PLANNING_AND_MANAGEMENT",
        "task": "TASK_16",
        "environment": "VIRTUAL_SIMULATION_SANDBOX",
        "zero_physical_actuation_enforced": True,
    }


@router.get("/overview", response_model=RepairOverviewSummarySchema)
def get_repair_overview(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Aggregates platform KPI metrics for the Repair Management Command Center.
    Requires VIEWER or higher.
    """
    return RepairIntelligenceService.get_overview(db)


@router.get("/assessments", response_model=List[DamageAssessmentSchema])
def list_damage_assessments(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists historical and active damage assessments.
    Requires VIEWER or higher.
    """
    models = RepairRepository.list_assessments(db, limit=limit)
    return [RepairRepository.model_to_assessment_schema(m) for m in models]


@router.post("/assessments/evaluate", response_model=DamageAssessmentSchema)
def evaluate_damage_assessment(
    req: DamageAssessmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Executes multi-factor damage assessment for a pipeline segment.
    Requires OPERATOR or higher.
    """
    assessment = DamageAssessmentEngine.assess_damage(
        db=db,
        pipeline_segment_id=req.pipeline_segment_id,
        source_inspection_report_id=req.source_inspection_report_id,
        operator_notes=req.notes,
    )
    RepairRepository.save_assessment(db, assessment)
    return assessment


@router.get("/assessments/{assessment_id}", response_model=DamageAssessmentSchema)
def get_damage_assessment_details(
    assessment_id: str = Path(..., description="Assessment ID (e.g. DMG-PIPE-01)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves full damage assessment details by ID.
    Requires VIEWER or higher.
    """
    m = RepairRepository.get_assessment(db, assessment_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")
    return RepairRepository.model_to_assessment_schema(m)


@router.get("/recommendations/{assessment_id}", response_model=RepairRecommendationSchema)
def get_repair_recommendations(
    assessment_id: str = Path(..., description="Assessment ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Generates or retrieves repair method recommendation options for an assessment.
    Requires VIEWER or higher.
    """
    assessment_model = RepairRepository.get_assessment(db, assessment_id)
    if not assessment_model:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")

    assessment_schema = DamageAssessmentEngine.assess_damage(db, assessment_model.pipeline_segment_id)
    rec = RepairMethodEngine.evaluate_repair_methods(assessment_schema)
    RepairRepository.save_recommendation(db, rec)
    return rec


@router.post("/plans/generate", response_model=RepairPlanSchema)
def generate_repair_plan(
    req: RepairPlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Orchestrates full repair plan formulation across damage assessment,
    method selection, resource bills, cost models, and virtual crew scheduling.
    Requires OPERATOR or higher.
    """
    plan = RepairIntelligenceService.generate_full_repair_plan(
        db=db,
        pipeline_segment_id=req.pipeline_segment_id,
        plan_name=req.plan_name,
        selected_method_override=req.selected_method,
        operator_notes=req.override_notes,
        user_id=current_user.username,
    )
    return plan


@router.get("/plans", response_model=List[RepairPlanSchema])
def list_repair_plans(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists repair plans, optionally filtered by workflow status.
    Requires VIEWER or higher.
    """
    models = RepairRepository.list_plans(db, status=status_filter, limit=limit)
    res = []
    for m in models:
        plan_detail = RepairIntelligenceService.get_plan_details(db, m.id)
        if plan_detail:
            res.append(plan_detail)
    return res


@router.get("/plans/{plan_id}", response_model=RepairPlanSchema)
def get_repair_plan_details(
    plan_id: str = Path(..., description="Plan ID (e.g. PLAN-REP-A1B2C3)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves full details of a specific repair plan.
    Requires VIEWER or higher.
    """
    plan = RepairIntelligenceService.get_plan_details(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Repair plan '{plan_id}' not found.")
    return plan


@router.post("/plans/{plan_id}/approve", response_model=RepairPlanSchema)
def approve_repair_plan(
    req: RepairPlanApprovalRequest,
    plan_id: str = Path(..., description="Plan ID to approve"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_engineer),
):
    """
    Formally approves a proposed repair plan.
    Requires certified ENGINEER or ADMINISTRATOR role.
    """
    plan = RepairRepository.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Repair plan '{plan_id}' not found.")

    if req.override_selected_method:
        plan.selected_method = req.override_selected_method

    updated_model = RepairRepository.transition_plan_status(
        db=db,
        plan_id=plan_id,
        target_status="APPROVED",
        user_id=current_user.username,
        reason=f"Engineering approval granted: {req.engineer_notes}",
        details={"engineer_notes": req.engineer_notes, "override_method": req.override_selected_method},
    )

    full_plan = RepairIntelligenceService.get_plan_details(db, plan_id)
    return full_plan


@router.post("/plans/{plan_id}/reject", response_model=RepairPlanSchema)
def reject_repair_plan(
    req: RepairPlanRejectionRequest,
    plan_id: str = Path(..., description="Plan ID to reject"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_engineer),
):
    """
    Formally rejects a proposed repair plan with mandatory engineering justification.
    Requires certified ENGINEER or ADMINISTRATOR role.
    """
    plan = RepairRepository.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Repair plan '{plan_id}' not found.")

    updated_model = RepairRepository.transition_plan_status(
        db=db,
        plan_id=plan_id,
        target_status="REJECTED",
        user_id=current_user.username,
        reason=req.rejection_reason,
        details={"rejection_reason": req.rejection_reason},
    )

    full_plan = RepairIntelligenceService.get_plan_details(db, plan_id)
    return full_plan


@router.post("/plans/{plan_id}/transition", response_model=RepairPlanSchema)
def transition_repair_plan_workflow(
    req: RepairWorkflowTransitionRequest,
    plan_id: str = Path(..., description="Plan ID to transition"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Transitions the repair plan through its 12-stage lifecycle.
    Requires OPERATOR or higher.
    """
    updated_model = RepairRepository.transition_plan_status(
        db=db,
        plan_id=plan_id,
        target_status=req.target_status,
        user_id=current_user.username,
        reason=req.reason,
        details={"notes": req.notes},
    )

    full_plan = RepairIntelligenceService.get_plan_details(db, plan_id)
    return full_plan


@router.get("/crews", response_model=List[Dict[str, Any]])
def list_virtual_repair_crews(
    available_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists virtual repair crews and availability.
    Requires VIEWER or higher.
    """
    RepairRepository.seed_default_crews(db)
    crews = RepairRepository.list_crews(db, available_only=available_only)
    res = []
    for c in crews:
        res.append({
            "crew_id": c.id,
            "crew_name": c.crew_name,
            "specialization": c.specialization,
            "skills": json.loads(c.skills_json) if c.skills_json else [],
            "members": json.loads(c.members_json) if c.members_json else [],
            "is_available": c.is_available,
            "base_location_lat": c.base_location_lat,
            "base_location_lng": c.base_location_lng,
            "current_assigned_job_id": c.current_assigned_job_id,
        })
    return res


@router.get("/simulation/{plan_id}", response_model=Dict[str, Any])
def run_or_get_repair_simulation(
    plan_id: str = Path(..., description="Plan ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves digital twin hydraulic simulation comparing pre-repair and post-repair conditions.
    Requires VIEWER or higher.
    """
    plan = RepairRepository.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Repair plan '{plan_id}' not found.")

    assessment = RepairRepository.get_assessment(db, plan.damage_assessment_id)
    pre_leak = assessment.estimated_water_loss_lph if assessment else 250.0

    scen, comp = DigitalTwinRepairSimulator.simulate_repair_impact(
        db=db,
        repair_plan_id=plan_id,
        pipeline_segment_id=plan.pipeline_segment_id,
        pre_repair_leak_lph=pre_leak,
    )
    return {
        "scenario": scen.model_dump(),
        "comparison": comp.model_dump(),
    }


@router.post("/verify", response_model=RepairVerificationSchema)
def submit_post_repair_verification(
    req: RepairVerificationRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_engineer),
):
    """
    Submits empirical and simulated post-repair measurements and signs off on verification.
    Requires certified ENGINEER or ADMINISTRATOR.
    """
    verif = RepairVerificationEngine.verify_repair(
        db=db,
        request=req,
        verified_by_user_id=current_user.username,
    )
    return verif


@router.get("/verifications/{plan_id}", response_model=RepairVerificationSchema)
def get_repair_verification(
    plan_id: str = Path(..., description="Plan ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves post-repair verification record and SHA-256 tamper-evident digest.
    Requires VIEWER or higher.
    """
    m = RepairRepository.get_verification_by_plan(db, plan_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Verification for plan '{plan_id}' not found.")

    evidence = []
    if m.supporting_evidence_json:
        try:
            evidence = json.loads(m.supporting_evidence_json)
        except Exception:
            evidence = []

    return RepairVerificationSchema(
        id=m.id,
        repair_plan_id=m.repair_plan_id,
        pipeline_segment_id=m.pipeline_segment_id,
        verification_outcome=m.verification_outcome,
        pre_repair_leakage_lph=m.pre_repair_leakage_lph,
        post_repair_leakage_lph=m.post_repair_leakage_lph,
        leakage_reduction_pct=m.leakage_reduction_pct,
        acoustic_anomaly_cleared=m.acoustic_anomaly_cleared,
        pressure_gradient_restored=m.pressure_gradient_restored,
        remaining_uncertainty_pct=m.remaining_uncertainty_pct,
        supporting_evidence=evidence,
        verified_by=m.verified_by,
        verified_at=m.verified_at.isoformat() if m.verified_at else "",
        tamper_proof_hash=m.tamper_proof_hash,
        is_simulated=m.is_simulated,
    )


@router.get("/events", response_model=List[RepairWorkflowEventSchema])
def list_workflow_events(
    plan_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves the audit trail of workflow state transitions.
    Requires VIEWER or higher.
    """
    events = RepairRepository.list_workflow_events(db, plan_id=plan_id, limit=limit)
    res = []
    for e in events:
        details = {}
        if e.details_json:
            try:
                details = json.loads(e.details_json)
            except Exception:
                details = {}
        res.append(RepairWorkflowEventSchema(
            id=e.id,
            repair_plan_id=e.repair_plan_id,
            from_status=e.from_status,
            to_status=e.to_status,
            changed_by=e.changed_by,
            reason=e.reason,
            details=details,
            timestamp=e.timestamp.isoformat() if e.timestamp else "",
        ))
    return res
