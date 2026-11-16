"""
AQUA CREW — Master Repair Intelligence Orchestration Service (Task 16)
Coordinates damage assessments, repair recommendations, resource planning, cost models,
prioritization, virtual crew scheduling, digital twin simulation, and WebSocket telemetry broadcasts.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
import uuid
import asyncio

from app.models.repair_management import (
    RepairAssessmentModel,
    RepairPlanModel,
    RepairRecommendationModel,
    RepairCostEstimateModel,
    RepairScheduleModel,
    RepairVerificationModel,
)
from app.repositories.repair_repository import RepairRepository
from app.repositories.pipeline_repository import PipelineRepository, DEFAULT_PIPELINES
from app.schemas.repair_management import (
    DamageAssessmentSchema,
    RepairRecommendationSchema,
    RepairPlanSchema,
    RepairCostEstimateSchema,
    RepairScheduleItemSchema,
    ResourcePlanSchema,
    RepairMethodType,
    RepairWorkflowStatus,
    RepairOverviewSummarySchema,
    DigitalTwinRepairScenarioSchema,
    DigitalTwinRepairComparisonSchema,
)
from app.services.repair_intelligence.damage_assessment_engine import DamageAssessmentEngine
from app.services.repair_intelligence.repair_method_engine import RepairMethodEngine
from app.services.repair_intelligence.resource_planning_engine import ResourcePlanningEngine
from app.services.repair_intelligence.cost_estimation_engine import CostEstimationEngine
from app.services.repair_intelligence.repair_prioritization_engine import RepairPrioritizationEngine
from app.services.repair_intelligence.crew_scheduling_engine import CrewSchedulingEngine
from app.services.repair_intelligence.digital_twin_repair_simulator import DigitalTwinRepairSimulator
from app.websocket.connection_manager import ws_manager
from app.core.exceptions import AquaCrewException


class RepairIntelligenceService:
    @staticmethod
    def _broadcast_event(payload: Dict[str, Any]) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast(payload))
        except Exception:
            pass

    @classmethod
    def generate_full_repair_plan(
        cls,
        db: Session,
        pipeline_segment_id: str,
        plan_name: Optional[str] = None,
        selected_method_override: Optional[RepairMethodType] = None,
        operator_notes: Optional[str] = None,
        user_id: str = "ENGINEER_SYSTEM",
    ) -> RepairPlanSchema:
        """
        Orchestrates an end-to-end evidence-grounded repair plan for a pipeline segment.
        """
        # Ensure default pipelines and crews exist
        segments = PipelineRepository.get_all(db)
        if not segments:
            for p in DEFAULT_PIPELINES:
                PipelineRepository.create(db, p)
            segments = PipelineRepository.get_all(db)

        seg = PipelineRepository.get_by_id(db, pipeline_segment_id)
        if not seg:
            seg = segments[0]
            pipeline_segment_id = seg.id

        if not plan_name:
            plan_name = f"Intelligent Repair Plan: {seg.name}" if seg else f"Intelligent Repair Plan: {pipeline_segment_id}"

        # 1. Damage Assessment
        assessment = DamageAssessmentEngine.assess_damage(
            db=db,
            pipeline_segment_id=pipeline_segment_id,
            operator_notes=operator_notes,
        )
        RepairRepository.save_assessment(db, assessment)

        # 2. Repair Method Evaluation
        recommendation = RepairMethodEngine.evaluate_repair_methods(assessment)
        RepairRepository.save_recommendation(db, recommendation)

        chosen_method = selected_method_override or recommendation.primary_recommended_method

        # 3. Repair Prioritization
        priority = RepairPrioritizationEngine.calculate_priority(db, assessment)

        # 4. Plan ID
        plan_id = f"PLAN-REP-{uuid.uuid4().hex[:6].upper()}"

        # 5. Resource Planning
        resource_plan = ResourcePlanningEngine.plan_resources(
            assessment=assessment,
            selected_method=chosen_method,
            plan_id=plan_id,
        )

        # 6. Cost & Impact Estimation
        # Duration based on chosen method
        opt = next((o for o in recommendation.all_evaluated_options if o.method == chosen_method), None)
        est_duration = opt.estimated_duration_hours if opt else 6.0

        cost_est = CostEstimationEngine.estimate_costs(
            assessment=assessment,
            selected_method=chosen_method,
            resource_plan=resource_plan,
            duration_hours=est_duration,
        )
        RepairRepository.save_cost_estimate(db, cost_est)

        # 7. Virtual Crew Scheduling
        schedule = CrewSchedulingEngine.schedule_repair(
            db=db,
            repair_plan_id=plan_id,
            selected_method=chosen_method,
            target_lat=seg.latitude if hasattr(seg, "latitude") and seg.latitude else 40.7128,
            target_lng=seg.longitude if hasattr(seg, "longitude") and seg.longitude else -74.0060,
            estimated_duration_hours=est_duration,
        )
        RepairRepository.save_schedule(db, schedule)

        # 8. Digital Twin Simulation
        dt_scenario, dt_comp = DigitalTwinRepairSimulator.simulate_repair_impact(
            db=db,
            repair_plan_id=plan_id,
            pipeline_segment_id=pipeline_segment_id,
            pre_repair_leak_lph=assessment.estimated_water_loss_lph,
        )

        # 9. Formulate Master Plan Schema
        plan_schema = RepairPlanSchema(
            id=plan_id,
            plan_name=plan_name,
            pipeline_segment_id=pipeline_segment_id,
            segment_name=seg.name,
            damage_assessment_id=assessment.id,
            repair_recommendation_id=recommendation.id,
            selected_method=chosen_method,
            workflow_status="ENGINEERING_REVIEW_PENDING",
            priority=priority,
            resources=resource_plan,
            cost_estimate=cost_est,
            schedule=schedule,
            approved_by=None,
            approved_at=None,
            rejection_reason=None,
            operator_notes=operator_notes,
            digital_twin_scenario_id=dt_scenario.scenario_id,
            created_by=user_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            is_simulated=True,
        )

        RepairRepository.save_plan(db, plan_schema)

        # Broadcast WebSocket event safely
        cls._broadcast_event({
            "type": "REPAIR_PLAN_CREATED",
            "plan_id": plan_id,
            "pipeline_segment_id": pipeline_segment_id,
            "selected_method": chosen_method,
            "priority": priority.priority_category,
            "estimated_cost_usd": cost_est.total_estimated_cost_usd,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return plan_schema

    @classmethod
    def get_plan_details(cls, db: Session, plan_id: str) -> Optional[RepairPlanSchema]:
        """
        Reconstructs full RepairPlanSchema including nested resources, cost estimate, and schedule.
        """
        plan_model = RepairRepository.get_plan(db, plan_id)
        if not plan_model:
            return None

        # Reconstruct Priority
        factors = {}
        if plan_model.priority_factors_json:
            try:
                factors = json.loads(plan_model.priority_factors_json)
            except Exception:
                factors = {}

        assessment_model = RepairRepository.get_assessment(db, plan_model.damage_assessment_id)
        if assessment_model:
            assessment_schema = DamageAssessmentEngine.assess_damage(db, plan_model.pipeline_segment_id)
            priority = RepairPrioritizationEngine.calculate_priority(db, assessment_schema)
        else:
            from app.schemas.repair_management import RepairPrioritySchema
            priority = RepairPrioritySchema(
                pipeline_segment_id=plan_model.pipeline_segment_id,
                repair_priority_score=plan_model.repair_priority_score,
                priority_category=plan_model.priority_category,
                contributing_factors=factors,
                uncertainty_margin=5.0,
                recommended_response_time_hours=24 if plan_model.priority_category == "CRITICAL" else 72,
                escalation_requirements=[],
            )

        # Reconstruct Resources
        resource_plan = None
        if assessment_model:
            resource_plan = ResourcePlanningEngine.plan_resources(
                assessment=assessment_schema,
                selected_method=plan_model.selected_method,
                plan_id=plan_model.id,
            )

        # Reconstruct Cost Estimate
        cost_model = RepairRepository.get_cost_estimate_by_assessment(db, plan_model.damage_assessment_id)
        cost_schema = None
        if cost_model and assessment_model:
            cost_schema = CostEstimationEngine.estimate_costs(
                assessment=assessment_schema,
                selected_method=plan_model.selected_method,
                resource_plan=resource_plan,
            )

        # Reconstruct Schedule
        sched_model = RepairRepository.get_schedule_by_plan(db, plan_id)
        sched_schema = None
        if sched_model:
            sched_schema = RepairScheduleItemSchema(
                schedule_id=sched_model.id,
                repair_plan_id=sched_model.repair_plan_id,
                crew_id=sched_model.crew_id,
                crew_name=sched_model.crew_name,
                scheduled_start=sched_model.scheduled_start.isoformat(),
                scheduled_end=sched_model.scheduled_end.isoformat(),
                estimated_duration_hours=sched_model.estimated_duration_hours,
                travel_distance_km=sched_model.travel_distance_km,
                travel_time_hours=sched_model.travel_time_hours,
                has_schedule_conflicts=sched_model.has_schedule_conflicts,
                schedule_conflict_details=sched_model.schedule_conflict_details,
                scheduling_notes=sched_model.scheduling_notes or "",
            )

        return RepairPlanSchema(
            id=plan_model.id,
            plan_name=plan_model.plan_name,
            pipeline_segment_id=plan_model.pipeline_segment_id,
            segment_name=plan_model.segment_name,
            damage_assessment_id=plan_model.damage_assessment_id,
            repair_recommendation_id=plan_model.repair_recommendation_id,
            selected_method=plan_model.selected_method,
            workflow_status=plan_model.workflow_status,
            priority=priority,
            resources=resource_plan,
            cost_estimate=cost_schema,
            schedule=sched_schema,
            approved_by=plan_model.approved_by,
            approved_at=plan_model.approved_at.isoformat() if plan_model.approved_at else None,
            rejection_reason=plan_model.rejection_reason,
            operator_notes=plan_model.operator_notes,
            digital_twin_scenario_id=plan_model.digital_twin_scenario_id,
            created_by=plan_model.created_by,
            created_at=plan_model.created_at.isoformat(),
            updated_at=plan_model.updated_at.isoformat() if plan_model.updated_at else plan_model.created_at.isoformat(),
            is_simulated=plan_model.is_simulated,
        )

    @classmethod
    def get_overview(cls, db: Session) -> RepairOverviewSummarySchema:
        """
        Aggregates system-wide repair planning KPI metrics.
        """
        assessments_count = db.query(RepairAssessmentModel).count()
        pending_count = db.query(RepairPlanModel).filter(
            RepairPlanModel.workflow_status == "ENGINEERING_REVIEW_PENDING"
        ).count()
        approved_count = db.query(RepairPlanModel).filter(
            RepairPlanModel.workflow_status.in_(["APPROVED", "RESOURCE_PLANNED"])
        ).count()
        scheduled_count = db.query(RepairPlanModel).filter(
            RepairPlanModel.workflow_status == "SCHEDULED"
        ).count()
        in_progress_count = db.query(RepairPlanModel).filter(
            RepairPlanModel.workflow_status == "REPAIR_IN_PROGRESS"
        ).count()
        verified_count = db.query(RepairVerificationModel).count()

        # Calculate saved water loss from verified repairs
        verifs = db.query(RepairVerificationModel).all()
        saved_m3 = sum(
            max(0.0, (v.pre_repair_leakage_lph - v.post_repair_leakage_lph) * 24.0 * 30.0 / 1000.0)
            for v in verifs
        )

        costs = db.query(RepairCostEstimateModel).all()
        total_exp = sum(c.total_estimated_cost_usd for c in costs)

        return RepairOverviewSummarySchema(
            system_status="ONLINE",
            active_assessments_count=assessments_count,
            pending_engineering_reviews_count=pending_count,
            approved_plans_count=approved_count,
            scheduled_repairs_count=scheduled_count,
            in_progress_repairs_count=in_progress_count,
            completed_verifications_count=verified_count,
            total_water_loss_prevented_m3=round(saved_m3, 1),
            total_repair_expenditure_usd=round(total_exp, 2),
            supported_damage_categories=[
                "PIPE_LEAK", "PIPE_BURST", "JOINT_FAILURE", "CORROSION",
                "STRUCTURAL_CRACK", "PRESSURE_DAMAGE", "VALVE_FAILURE", "UNKNOWN_DAMAGE"
            ],
            supported_repair_methods=[
                "CLAMP_REPAIR", "JOINT_REPAIR_REPLACEMENT", "PIPE_SECTION_REPLACEMENT",
                "INTERNAL_LINING_REHABILITATION", "CORROSION_PROTECTION", "VALVE_REPLACEMENT",
                "PRESSURE_MANAGEMENT", "FURTHER_INSPECTION_REQUIRED"
            ],
            is_simulated=True,
        )
