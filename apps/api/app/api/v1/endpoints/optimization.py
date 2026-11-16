"""
FastAPI Router for Network Optimization & Hydraulic Decision Engine (Task 14)
Prefix: /api/v1/optimization
Enforces zero-trust JWT authentication and Task 13.6 role-based access control.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import uuid

from app.database.session import get_db
from app.models.user import UserModel
from app.core.auth import get_current_user, require_engineer, require_operator, require_viewer
from app.services.hydraulic_network_service import HydraulicNetworkService, DEFAULT_NETWORK_ID
from app.services.scenario_manager_service import ScenarioManagerService
from app.services.hydraulic_engine.network_adapter import NetworkAdapter
from app.services.hydraulic_engine.simulation_runner import SimulationRunner
from app.services.hydraulic_engine.network_performance_service import NetworkPerformanceService
from app.services.hydraulic_engine.optimization_engine import OptimizationEngine
from app.services.hydraulic_engine.optimization_validator import OptimizationValidator
from app.services.hydraulic_engine.multi_scenario_optimizer import MultiScenarioOptimizer
from app.services.hydraulic_engine.pareto_analysis_service import PROFILE_WEIGHTS
from app.repositories.optimization_repository import OptimizationRepository
from app.schemas.optimization import (
    OptimizationTriggerRequest,
    OptimizationJobDetailResponse,
    OptimizationCandidateSchema,
    BaselineComparisonSchema,
    OptimizationRecommendRequest,
    OptimizationConstraintsSchema,
)
from app.schemas.network_performance import NetworkPerformanceReport
from app.models.operational_intelligence import OperationalRecommendationModel


router = APIRouter()


@router.get("/status")
def get_optimization_status():
    """
    Returns optimization engine health, algorithms, and supported profiles.
    """
    return {
        "status": "OPERATIONAL",
        "supported_algorithms": [
            "DIFFERENTIAL_EVOLUTION",
            "MULTI_OBJECTIVE_PARETO",
            "SEQUENTIAL_LOCAL",
            "GRID_EXPLORATION",
        ],
        "objective_profiles": list(PROFILE_WEIGHTS.keys()),
        "hydraulic_solver": "WNTR / EPANET 2.2",
        "hardware_actuators_disabled": True,
        "is_simulated": True,
        "source": "VIRTUAL_SIMULATION_ENGINE",
    }


@router.get("/network/baseline", response_model=NetworkPerformanceReport)
def get_network_baseline(
    network_id: str = Query(DEFAULT_NETWORK_ID),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Computes and returns the nominal baseline hydraulic performance report.
    """
    net = HydraulicNetworkService.get_or_create_default_network(db)
    nodes = HydraulicNetworkService.list_nodes(db, network_id)
    links = HydraulicNetworkService.list_links(db, network_id)
    net_dict = NetworkAdapter.to_solver_dict(net, nodes, links)

    sim_res = SimulationRunner.execute(
        network_data=net_dict,
        scenario_id="SCEN-BASELINE-01",
        scenario_type="BASELINE",
        duration_hours=24,
    )

    return NetworkPerformanceService.evaluate(
        result=sim_res,
        network_data=net_dict,
        scenario_name="Nominal Baseline Municipal Grid",
        duration_hours=24,
    )


@router.post("/evaluate")
def evaluate_candidate_configuration(
    candidate_variables: Dict[str, float],
    network_id: str = Query(DEFAULT_NETWORK_ID),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Evaluates an arbitrary candidate decision vector against physical constraints.
    """
    net = HydraulicNetworkService.get_or_create_default_network(db)
    nodes = HydraulicNetworkService.list_nodes(db, network_id)
    links = HydraulicNetworkService.list_links(db, network_id)
    net_dict = NetworkAdapter.to_solver_dict(net, nodes, links)

    constraints = OptimizationConstraintsSchema()
    is_valid, sim_res, violations = OptimizationValidator.verify_candidate(
        candidate_variables=candidate_variables,
        base_network_data=net_dict,
        scenario_overrides={},
        constraints=constraints,
    )

    report = None
    if is_valid and sim_res:
        report = NetworkPerformanceService.evaluate(
            result=sim_res,
            network_data=net_dict,
            scenario_name="Candidate Evaluation",
        )

    return {
        "is_hydraulically_verified": is_valid,
        "violations": violations,
        "performance_report": report,
        "decision_variables": candidate_variables,
        "is_simulated": True,
        "source": "VIRTUAL_SIMULATION_ENGINE",
    }


@router.post("/optimize", response_model=OptimizationJobDetailResponse)
def trigger_optimization_job(
    request: OptimizationTriggerRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_engineer),
):
    """
    Executes a constrained multi-objective optimization run and persists results.
    Restricted to ENGINEER and ADMINISTRATOR roles.
    """
    net = HydraulicNetworkService.get_or_create_default_network(db)
    nodes = HydraulicNetworkService.list_nodes(db, request.network_id)
    links = HydraulicNetworkService.list_links(db, request.network_id)
    net_dict = NetworkAdapter.to_solver_dict(net, nodes, links)

    # Resolve scenario overrides
    scenarios = ScenarioManagerService.list_scenarios(db, request.network_id)
    target_scen = next((s for s in scenarios if s.id == request.scenario_id), None)
    overrides = {}
    if target_scen and target_scen.parameters_override_json:
        try:
            overrides = json.loads(target_scen.parameters_override_json)
        except Exception:
            overrides = {}

    job_result = OptimizationEngine.execute_optimization(
        network_data=net_dict,
        request=request,
        user_id=current_user.id,
        scenario_overrides=overrides,
    )

    # Persist job and candidate models
    OptimizationRepository.save_job(db, job_result)
    return job_result


@router.post("/optimize/compare")
def compare_multi_scenarios(
    candidate_variables: Dict[str, float],
    network_id: str = Query(DEFAULT_NETWORK_ID),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Evaluates candidate configuration across 10 operational conditions.
    """
    net = HydraulicNetworkService.get_or_create_default_network(db)
    nodes = HydraulicNetworkService.list_nodes(db, network_id)
    links = HydraulicNetworkService.list_links(db, network_id)
    net_dict = NetworkAdapter.to_solver_dict(net, nodes, links)

    scenarios_evaluated = MultiScenarioOptimizer.evaluate_all_scenarios(
        network_data=net_dict,
        candidate_variables=candidate_variables,
    )

    return {
        "candidate_variables": candidate_variables,
        "total_scenarios_evaluated": len(scenarios_evaluated),
        "scenarios": scenarios_evaluated,
        "is_simulated": True,
        "source": "VIRTUAL_SIMULATION_ENGINE",
    }


@router.get("/jobs")
def list_optimization_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists persisted optimization jobs.
    """
    # Administrators can list all jobs; standard users see jobs filtered by user_id
    u_filter = None if current_user.role == "ADMINISTRATOR" else current_user.id
    return OptimizationRepository.list_jobs(db, limit=limit, offset=offset, user_id=u_filter)


@router.get("/jobs/{job_id}", response_model=OptimizationJobDetailResponse)
def get_optimization_job(
    job_id: str = Path(..., description="Optimization Job ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves full details for a specified optimization job.
    """
    job = OptimizationRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Optimization job '{job_id}' not found.")
    return job


@router.get("/jobs/{job_id}/candidates", response_model=List[OptimizationCandidateSchema])
def get_job_candidates(
    job_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves candidate configurations evaluated during the specified job.
    """
    job = OptimizationRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Optimization job '{job_id}' not found.")
    return job.candidates


@router.get("/jobs/{job_id}/pareto", response_model=List[OptimizationCandidateSchema])
def get_job_pareto_frontier(
    job_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves non-dominated Pareto-optimal candidates for the specified job.
    """
    job = OptimizationRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Optimization job '{job_id}' not found.")
    return job.pareto_frontier


@router.get("/jobs/{job_id}/validation")
def get_job_validation_summary(
    job_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves verification status and constraint violations for candidates.
    """
    job = OptimizationRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Optimization job '{job_id}' not found.")

    verified = [c for c in job.candidates if c.is_hydraulically_verified]
    rejected = [c for c in job.candidates if not c.is_hydraulically_verified]

    return {
        "job_id": job_id,
        "total_evaluated": len(job.candidates),
        "verified_count": len(verified),
        "rejected_count": len(rejected),
        "rejection_summary": [
            {"candidate_id": r.candidate_id, "reason": r.rejection_reason, "violations": r.constraint_violations}
            for r in rejected
        ],
    }


@router.get("/jobs/{job_id}/report")
def get_job_comparison_report(
    job_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns baseline-versus-optimized performance comparison.
    """
    job = OptimizationRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Optimization job '{job_id}' not found.")

    return {
        "job_id": job.job_id,
        "objective_profile": job.objective_profile,
        "best_candidate": job.best_candidate,
        "comparison_with_baseline": job.comparison_with_baseline,
        "pareto_optimal_count": len(job.pareto_frontier),
        "execution_duration_ms": job.execution_time_ms,
        "is_simulated": True,
        "source": "VIRTUAL_SIMULATION_ENGINE",
    }


@router.post("/jobs/{job_id}/cancel")
def cancel_optimization_job(
    job_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_engineer),
):
    """
    Cancels an active optimization job.
    """
    success = OptimizationRepository.cancel_job(db, job_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Optimization job '{job_id}' not found.")
    return {"success": True, "message": f"Optimization job '{job_id}' successfully cancelled."}


@router.post("/jobs/{job_id}/recommend")
def recommend_optimized_candidate(
    job_id: str = Path(...),
    body: OptimizationRecommendRequest = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Converts an optimized candidate configuration into a pending operational recommendation.
    Enforces Task 13.6 Human-in-the-Loop governance.
    """
    job = OptimizationRepository.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Optimization job '{job_id}' not found.")

    target_cand = job.best_candidate
    if body and body.target_candidate_id:
        target_cand = next((c for c in job.candidates if c.candidate_id == body.target_candidate_id), job.best_candidate)

    if not target_cand or not target_cand.is_hydraulically_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot recommend an unverified or infeasible candidate configuration."
        )

    rec_id = f"REC-OPT-{uuid.uuid4().hex[:8].upper()}"
    notes = body.notes if body and body.notes else "Recommended via Task 14 Network Optimization Engine."

    rec = OperationalRecommendationModel(
        id=rec_id,
        category="HYDRAULIC_OPTIMIZATION_RECOMMENDED",
        pipeline_segment_id="PIPE-SEC-4B-92",
        segment_name="Metro Central Distribution Grid",
        risk_severity="MODERATE",
        priority_score=round(100.0 - (target_cand.objective_score * 10.0), 1),
        priority_tier="HIGH_PLANNED",
        recommended_action=(
            f"Apply optimized setpoints: pump_speed={target_cand.decision_variables.get('pump_speed_P1', 1.0)}, "
            f"prv_setting={target_cand.decision_variables.get('prv_setting_PRV01', 3.5)} bar."
        ),
        why_explanation=(
            f"Achieves verified {job.comparison_with_baseline.leakage_reduction_pct:.1f}% leakage reduction "
            f"and {job.comparison_with_baseline.energy_saved_pct:.1f}% pump energy savings while preserving 100% demand."
            if job.comparison_with_baseline else "Verified optimal hydraulic setpoint recommendation."
        ),
        what_missing="Manual field verification of downstream PRV gauge pressure required prior to physical implementation.",
        expected_impact=(
            f"Saves ~{job.comparison_with_baseline.leakage_reduction_m3:.1f} m³ water/day and ~{job.comparison_with_baseline.energy_saved_kwh:.1f} kWh/day."
            if job.comparison_with_baseline else "Energy efficiency and pressure stabilization impact."
        ),
        status="PENDING_REVIEW",
        approval_status="PENDING",
        is_simulated=True,
    )
    db.add(rec)
    db.commit()

    return {
        "success": True,
        "recommendation_id": rec_id,
        "candidate_id": target_cand.candidate_id,
        "status": "PENDING_REVIEW",
        "human_approval_required": True,
        "hardware_actuators_disabled": True,
        "message": f"Optimization recommendation '{rec_id}' created for human supervisor review.",
    }
