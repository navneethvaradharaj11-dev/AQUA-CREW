"""
Repository for Optimization Persistence & Auditability (Task 14)
Manages transactional persistence for OptimizationJobModel, OptimizationCandidateModel,
and OptimizationAuditEventModel.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import uuid

from app.models.optimization import (
    OptimizationJobModel,
    OptimizationCandidateModel,
    OptimizationAuditEventModel,
)
from app.schemas.optimization import (
    OptimizationJobDetailResponse,
    OptimizationCandidateSchema,
    BaselineComparisonSchema,
    ObjectiveWeightsSchema,
    OptimizationConstraintsSchema,
)


class OptimizationRepository:
    """
    Data access layer for network optimization jobs, candidates, and audit records.
    """

    @classmethod
    def save_job(cls, db: Session, job: OptimizationJobDetailResponse) -> OptimizationJobModel:
        """
        Persists a completed optimization job and its candidates within a single transaction.
        """
        job_model = OptimizationJobModel(
            id=job.job_id,
            user_id=job.user_id,
            network_id=job.network_id,
            scenario_id=job.scenario_id,
            scenario_name=job.scenario_name,
            status=job.status,
            objective_profile=job.objective_profile,
            algorithm=job.algorithm,
            weights_json=job.weights.model_dump_json(),
            constraints_json=job.constraints.model_dump_json(),
            evaluation_count=job.evaluation_count,
            execution_time_ms=job.execution_time_ms,
            best_candidate_id=job.best_candidate.candidate_id if job.best_candidate else None,
            comparison_summary_json=job.comparison_with_baseline.model_dump_json() if job.comparison_with_baseline else "{}",
            pareto_frontier_json=json.dumps([c.model_dump() for c in job.pareto_frontier]),
            created_at=datetime.fromisoformat(job.created_at) if job.created_at else datetime.now(timezone.utc),
            completed_at=datetime.fromisoformat(job.completed_at) if job.completed_at else datetime.now(timezone.utc),
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
        db.add(job_model)

        for c in job.candidates:
            cand_model = OptimizationCandidateModel(
                id=f"{job.job_id}-{c.candidate_id}",
                job_id=job.job_id,
                rank=c.rank,
                is_pareto_optimal=c.is_pareto_optimal,
                decision_variables_json=json.dumps(c.decision_variables),
                objective_score=c.objective_score,
                water_loss_m3=c.water_loss_score,
                energy_kwh=c.energy_score,
                pressure_penalty=c.pressure_penalty,
                demand_satisfaction_ratio=c.demand_satisfaction_ratio,
                estimated_cost_usd=c.estimated_cost_usd,
                is_hydraulically_verified=c.is_hydraulically_verified,
                constraint_violations_json=json.dumps(c.constraint_violations),
                rejection_reason=c.rejection_reason,
                created_at=datetime.now(timezone.utc),
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            )
            db.add(cand_model)

        audit = OptimizationAuditEventModel(
            id=f"OPTAUD-{job.job_id}",
            job_id=job.job_id,
            user_id=job.user_id,
            event_type="JOB_COMPLETED",
            details_json=json.dumps({"evaluations": job.evaluation_count, "best_candidate": job.best_candidate.candidate_id if job.best_candidate else None}),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(audit)
        db.commit()
        db.refresh(job_model)
        return job_model

    @classmethod
    def get_job(cls, db: Session, job_id: str) -> Optional[OptimizationJobDetailResponse]:
        """
        Retrieves job and reconstitutes full OptimizationJobDetailResponse.
        """
        job = db.query(OptimizationJobModel).filter(OptimizationJobModel.id == job_id).first()
        if not job:
            return None

        candidates = (
            db.query(OptimizationCandidateModel)
            .filter(OptimizationCandidateModel.job_id == job_id)
            .order_by(OptimizationCandidateModel.rank.asc())
            .all()
        )

        cand_schemas = []
        best_cand = None
        for c in candidates:
            c_schema = OptimizationCandidateSchema(
                candidate_id=c.id.replace(f"{job.id}-", "", 1) if c.id.startswith(f"{job.id}-") else c.id,
                rank=c.rank,
                is_pareto_optimal=c.is_pareto_optimal,
                decision_variables=json.loads(c.decision_variables_json),
                objective_score=c.objective_score,
                water_loss_score=c.water_loss_m3,
                energy_score=c.energy_kwh,
                pressure_penalty=c.pressure_penalty,
                demand_satisfaction_ratio=c.demand_satisfaction_ratio,
                estimated_cost_usd=c.estimated_cost_usd,
                is_hydraulically_verified=c.is_hydraulically_verified,
                constraint_violations=json.loads(c.constraint_violations_json),
                rejection_reason=c.rejection_reason,
            )
            cand_schemas.append(c_schema)
            if job.best_candidate_id and (c.id.endswith(job.best_candidate_id) or c.id == job.best_candidate_id):
                best_cand = c_schema

        if not best_cand and cand_schemas:
            best_cand = cand_schemas[0]

        weights = ObjectiveWeightsSchema(**json.loads(job.weights_json))
        constraints = OptimizationConstraintsSchema(**json.loads(job.constraints_json))
        comparison = (
            BaselineComparisonSchema(**json.loads(job.comparison_summary_json))
            if job.comparison_summary_json and job.comparison_summary_json != "{}"
            else None
        )

        pareto_raw = json.loads(job.pareto_frontier_json) if job.pareto_frontier_json else []
        pareto_frontier = [OptimizationCandidateSchema(**item) for item in pareto_raw]

        return OptimizationJobDetailResponse(
            job_id=job.id,
            user_id=job.user_id,
            network_id=job.network_id,
            scenario_id=job.scenario_id,
            scenario_name=job.scenario_name,
            status=job.status,
            objective_profile=job.objective_profile,
            algorithm=job.algorithm,
            weights=weights,
            constraints=constraints,
            evaluation_count=job.evaluation_count,
            execution_time_ms=job.execution_time_ms,
            best_candidate=best_cand,
            candidates=cand_schemas,
            comparison_with_baseline=comparison,
            pareto_frontier=pareto_frontier,
            created_at=job.created_at.isoformat() if job.created_at else "",
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            is_simulated=True,
            source=job.source,
        )

    @classmethod
    def list_jobs(
        cls,
        db: Session,
        limit: int = 20,
        offset: int = 0,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lists optimization job metadata summaries.
        """
        q = db.query(OptimizationJobModel)
        if user_id:
            q = q.filter(OptimizationJobModel.user_id == user_id)
        jobs = q.order_by(OptimizationJobModel.created_at.desc()).offset(offset).limit(limit).all()

        out = []
        for j in jobs:
            out.append({
                "job_id": j.id,
                "user_id": j.user_id,
                "network_id": j.network_id,
                "scenario_id": j.scenario_id,
                "scenario_name": j.scenario_name,
                "status": j.status,
                "objective_profile": j.objective_profile,
                "algorithm": j.algorithm,
                "evaluation_count": j.evaluation_count,
                "execution_time_ms": j.execution_time_ms,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            })
        return out

    @classmethod
    def cancel_job(cls, db: Session, job_id: str, user_id: str) -> bool:
        """
        Marks an active job as CANCELLED and logs an audit event.
        """
        job = db.query(OptimizationJobModel).filter(OptimizationJobModel.id == job_id).first()
        if not job:
            return False

        job.status = "CANCELLED"
        job.completed_at = datetime.now(timezone.utc)

        audit = OptimizationAuditEventModel(
            id=f"OPTAUD-CANCEL-{uuid.uuid4().hex[:8]}",
            job_id=job_id,
            user_id=user_id,
            event_type="JOB_CANCELLED",
            details_json=json.dumps({"cancelled_by": user_id}),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(audit)
        db.commit()
        return True
