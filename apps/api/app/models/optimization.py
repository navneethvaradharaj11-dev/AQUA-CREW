"""
SQLAlchemy Persistent Models for Network Optimization & Decision Engine (Task 14)
Preserves optimization jobs, candidate evaluations, Pareto frontiers, and user audit trails.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, ForeignKey
from datetime import datetime, timezone
import json

from app.database.session import Base


class OptimizationJobModel(Base):
    __tablename__ = "optimization_jobs"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)  # Authenticated creator identity
    network_id = Column(String(64), nullable=False, index=True)
    scenario_id = Column(String(64), nullable=False, index=True)
    scenario_name = Column(String(256), default="")
    status = Column(String(32), default="PENDING", nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    objective_profile = Column(String(64), default="BALANCED_OPERATION", nullable=False)
    algorithm = Column(String(64), default="DIFFERENTIAL_EVOLUTION", nullable=False)
    weights_json = Column(Text, default="{}", nullable=False)
    constraints_json = Column(Text, default="{}", nullable=False)
    evaluation_count = Column(Integer, default=0, nullable=False)
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    best_candidate_id = Column(String(64), nullable=True)
    comparison_summary_json = Column(Text, default="{}", nullable=False)
    pareto_frontier_json = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(128), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OptimizationCandidateModel(Base):
    __tablename__ = "optimization_candidates"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("optimization_jobs.id"), nullable=False, index=True)
    rank = Column(Integer, default=1, nullable=False)
    is_pareto_optimal = Column(Boolean, default=False, nullable=False)
    decision_variables_json = Column(Text, default="{}", nullable=False)
    objective_score = Column(Float, nullable=False)
    water_loss_m3 = Column(Float, nullable=False)
    energy_kwh = Column(Float, nullable=False)
    pressure_penalty = Column(Float, default=0.0, nullable=False)
    demand_satisfaction_ratio = Column(Float, default=1.0, nullable=False)
    estimated_cost_usd = Column(Float, nullable=True)
    is_hydraulically_verified = Column(Boolean, default=True, nullable=False)
    constraint_violations_json = Column(Text, default="[]", nullable=False)
    rejection_reason = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(128), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OptimizationAuditEventModel(Base):
    __tablename__ = "optimization_audit_events"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # JOB_CREATED, JOB_STARTED, JOB_CANCELLED, JOB_COMPLETED, CANDIDATE_RECOMMENDED
    details_json = Column(Text, default="{}", nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

