"""
AQUA CREW — Adaptive Inspection Execution Engine (Task 15)
Simulates virtual rover mission progress along pipeline waypoints, synthesizes sensor telemetry
with strict SIMULATED provenance, detects mid-mission anomalies, adapts remaining routes,
handles safety abort conditions, and generates persistent evidence-grounded reports.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import json
import uuid
import math
import asyncio
from sqlalchemy.orm import Session

from app.models.rover import RoverModel
from app.models.pipeline_segment import PipelineSegmentModel
from app.models.inspection_intelligence import (
    InspectionPlanModel,
    InspectionExecutionModel,
    InspectionReportModel,
)
from app.schemas.inspection_intelligence import (
    InspectionExecutionProgressSchema,
    SimulatedSensorObservation,
    InspectionReportSchema,
    ExecutionStatus,
)
from app.repositories.rover_repository import RoverRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.inspection_intelligence_repository import InspectionIntelligenceRepository
from app.services.pipeline_routing_service import PipelineRoutingService, haversine_distance_m
from app.websocket.connection_manager import ws_manager
from app.core.exceptions import AquaCrewException


class InspectionExecutionEngine:
    @staticmethod
    def _broadcast_event(payload: Dict[str, Any]) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast(payload))
        except Exception:
            pass

    @classmethod
    def start_mission_execution(
        cls,
        db: Session,
        plan_id: str,
        rover_id: str,
    ) -> InspectionExecutionProgressSchema:
        """
        Initializes and launches virtual rover inspection execution for an approved plan.
        """
        plan = InspectionIntelligenceRepository.get_plan(db, plan_id)
        if not plan:
            raise AquaCrewException(status_code=404, code="PLAN_NOT_FOUND", message=f"Plan '{plan_id}' not found.")

        if plan.human_approval_status != "APPROVED":
            raise AquaCrewException(
                status_code=400,
                code="PLAN_NOT_APPROVED",
                message=f"Plan '{plan_id}' is in status '{plan.human_approval_status}' (must be APPROVED before launch).",
            )

        rover = RoverRepository.get_by_id(db, rover_id)
        if not rover:
            raise AquaCrewException(status_code=404, code="ROVER_NOT_FOUND", message=f"Rover '{rover_id}' not found.")

        # Parse plan allocation for this rover
        allocations = json.loads(plan.allocations_json)
        rover_alloc = next((a for a in allocations if a.get("rover_id") == rover_id), None)
        if not rover_alloc:
            raise AquaCrewException(
                status_code=400,
                code="ROVER_NOT_ASSIGNED_IN_PLAN",
                message=f"Rover '{rover_id}' has no assigned targets in plan '{plan_id}'.",
            )

        mission_id = f"MIS-INSP-{uuid.uuid4().hex[:8].upper()}"
        waypoints = rover_alloc.get("route_waypoints", [[rover.longitude, rover.latitude]])
        total_dist_m = rover_alloc.get("total_route_distance_m", 500.0)

        # Transition rover to INSPECTING
        RoverRepository.update_operating_state(db, rover.id, "INSPECTING")
        RoverRepository.update_assigned_mission(db, rover.id, mission_id)

        init_step = InspectionExecutionProgressSchema(
            mission_id=mission_id,
            rover_id=rover.id,
            plan_id=plan_id,
            status="IN_PROGRESS",
            current_step=0,
            total_steps=max(5, len(waypoints)),
            progress_percentage=0.0,
            current_coordinates=waypoints[0] if waypoints else [rover.longitude, rover.latitude],
            distance_traversed_m=0.0,
            remaining_distance_m=total_dist_m,
            battery_percentage=rover.battery_percentage,
            motor_temp_c=rover.motor_temp_c,
            active_anomalies_detected=0,
            route_adapted=False,
            adaptation_history=[],
            recent_observations=[],
            last_updated=datetime.now(timezone.utc).isoformat(),
            is_simulated=True,
        )

        InspectionIntelligenceRepository.save_execution(db, init_step)
        InspectionIntelligenceRepository.log_event(
            db,
            event_type="INSPECTION_STARTED",
            plan_id=plan_id,
            mission_id=mission_id,
            rover_id=rover.id,
            details={"waypoints_count": len(waypoints), "total_distance_m": total_dist_m},
        )

        # Broadcast WebSocket event
        cls._broadcast_event({
            "type": "INSPECTION_STARTED",
            "mission_id": mission_id,
            "rover_id": rover.id,
            "plan_id": plan_id,
            "coordinates": init_step.current_coordinates,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return init_step

    @classmethod
    def execute_next_step(
        cls,
        db: Session,
        mission_id: str,
        step_increment_m: float = 100.0,
    ) -> InspectionExecutionProgressSchema:
        """
        Advances the virtual rover simulation forward along its planned route by one increment.
        Synthesizes sensor observations, detects simulated anomalies, checks safety limits,
        and finalizes reports if the mission reaches 100%.
        """
        exec_model = InspectionIntelligenceRepository.get_execution_by_mission(db, mission_id)
        if not exec_model:
            raise AquaCrewException(status_code=404, code="MISSION_NOT_FOUND", message=f"Mission '{mission_id}' not found.")

        if exec_model.status in ["COMPLETED", "ABORTED_LOW_BATTERY", "ABORTED_SENSOR_FAULT", "EMERGENCY_STOP"]:
            raise AquaCrewException(
                status_code=400,
                code="MISSION_ALREADY_TERMINATED",
                message=f"Mission '{mission_id}' is already in terminal state '{exec_model.status}'.",
            )

        rover = RoverRepository.get_by_id(db, exec_model.rover_id)
        plan = InspectionIntelligenceRepository.get_plan(db, exec_model.plan_id)

        allocations = json.loads(plan.allocations_json) if plan else []
        rover_alloc = next((a for a in allocations if a.get("rover_id") == exec_model.rover_id), {})
        waypoints = rover_alloc.get("route_waypoints", [])
        total_dist_m = max(100.0, rover_alloc.get("total_route_distance_m", 500.0))

        # 1. Update distance & step index
        new_step = exec_model.current_step + 1
        new_dist_traversed = min(total_dist_m, exec_model.distance_traversed_m + step_increment_m)
        new_remaining_dist = max(0.0, total_dist_m - new_dist_traversed)
        progress_pct = round((new_dist_traversed / total_dist_m) * 100.0, 1)

        # 2. Interpolate Coordinates
        wp_idx = min(len(waypoints) - 1, int((progress_pct / 100.0) * (len(waypoints) - 1)))
        current_coord = waypoints[wp_idx] if waypoints else [exec_model.current_lng, exec_model.current_lat]

        # 3. Simulate Battery & Temperature Dynamics
        drain = (step_increment_m / 1000.0) * 1.8 + 0.2
        new_battery = max(0.0, round(rover.battery_percentage - drain, 1))
        new_temp = round(min(65.0, rover.motor_temp_c + 0.15), 1)

        # Update rover record in DB
        RoverRepository.update_position(db, rover.id, current_coord[1], current_coord[0])
        RoverRepository.update_battery(db, rover.id, new_battery)
        rover.motor_temp_c = new_temp
        db.commit()

        # 4. Generate Synthetic Sensor Observations (SIMULATED)
        obs_list: List[SimulatedSensorObservation] = []
        recent_obs_raw = json.loads(exec_model.recent_observations_json or "[]")

        # Synthesize acoustic hydrophone reading
        has_acoustic_spike = (40.0 <= progress_pct <= 65.0) # Simulated leak along segment
        spl_val = round(72.5 if has_acoustic_spike else (42.0 + (new_step % 5)), 1)
        obs_acoustic = SimulatedSensorObservation(
            observation_id=f"OBS-AC-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rover_id=rover.id,
            segment_id=rover_alloc.get("segments_traversed", ["PIPE-01"])[0],
            distance_along_pipe_m=round(new_dist_traversed, 1),
            sensor_type="ACOUSTIC",
            reading_value=spl_val,
            unit="dB",
            anomaly_detected=has_acoustic_spike,
            classification="SIMULATED",
        )
        obs_list.append(obs_acoustic)

        # Synthesize ground moisture reading
        moisture_val = round(48.5 if has_acoustic_spike else 18.0, 1)
        obs_moisture = SimulatedSensorObservation(
            observation_id=f"OBS-MST-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rover_id=rover.id,
            segment_id=rover_alloc.get("segments_traversed", ["PIPE-01"])[0],
            distance_along_pipe_m=round(new_dist_traversed, 1),
            sensor_type="MOISTURE",
            reading_value=moisture_val,
            unit="%",
            anomaly_detected=(moisture_val > 40.0),
            classification="SIMULATED",
        )
        obs_list.append(obs_moisture)

        all_observations = recent_obs_raw + [o.model_dump() for o in obs_list]

        # 5. Safety & Termination Checks
        status: ExecutionStatus = "IN_PROGRESS"
        anomalies_count = exec_model.active_anomalies_count + (1 if has_acoustic_spike else 0)

        if new_battery < 15.0:
            status = "ABORTED_LOW_BATTERY"
            RoverRepository.update_operating_state(db, rover.id, "RETURNING")
            InspectionIntelligenceRepository.log_event(
                db, "ROVER_WARNING", rover_id=rover.id, mission_id=mission_id,
                details={"reason": f"Critical low battery ({new_battery:.1f}% < 15%). Mission aborted."}
            )
        elif new_temp >= 55.0:
            status = "ABORTED_SENSOR_FAULT"
            RoverRepository.update_operating_state(db, rover.id, "RETURNING")
            InspectionIntelligenceRepository.log_event(
                db, "ROVER_WARNING", rover_id=rover.id, mission_id=mission_id,
                details={"reason": f"Motor overheating ({new_temp:.1f}°C >= 55°C). Mission aborted."}
            )
        elif progress_pct >= 100.0:
            status = "COMPLETED"
            RoverRepository.update_operating_state(db, rover.id, "IDLE")
            InspectionIntelligenceRepository.log_event(
                db, "INSPECTION_COMPLETED", rover_id=rover.id, mission_id=mission_id,
                details={"total_distance_inspected_m": new_dist_traversed}
            )
            # Create completed inspection report
            cls._generate_completion_report(db, exec_model, plan, rover, all_observations)

        updated_step = InspectionExecutionProgressSchema(
            mission_id=mission_id,
            rover_id=rover.id,
            plan_id=exec_model.plan_id,
            status=status,
            current_step=new_step,
            total_steps=exec_model.total_steps,
            progress_percentage=progress_pct,
            current_coordinates=current_coord,
            distance_traversed_m=round(new_dist_traversed, 1),
            remaining_distance_m=round(new_remaining_dist, 1),
            battery_percentage=new_battery,
            motor_temp_c=new_temp,
            active_anomalies_detected=anomalies_count,
            route_adapted=exec_model.route_adapted,
            adaptation_history=json.loads(exec_model.adaptation_history_json or "[]"),
            recent_observations=[SimulatedSensorObservation(**o) for o in all_observations[-10:]],
            last_updated=datetime.now(timezone.utc).isoformat(),
            is_simulated=True,
        )

        InspectionIntelligenceRepository.save_execution(db, updated_step)

        # Broadcast progress event via WebSocket
        cls._broadcast_event({
            "type": "INSPECTION_PROGRESS",
            "mission_id": mission_id,
            "rover_id": rover.id,
            "progress_percentage": progress_pct,
            "status": status,
            "coordinates": current_coord,
            "anomalies_detected": anomalies_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return updated_step

    @classmethod
    def trigger_adaptive_reroute(
        cls,
        db: Session,
        mission_id: str,
        adaptation_reason: str,
        new_anomaly_coord: Optional[List[float]] = None,
        new_target_segment_id: Optional[str] = None,
    ) -> InspectionExecutionProgressSchema:
        """
        Dynamically adapts the remaining inspection route in response to a newly detected anomaly.
        Preserves safe return-to-base battery reserve checks.
        """
        exec_model = InspectionIntelligenceRepository.get_execution_by_mission(db, mission_id)
        if not exec_model:
            raise AquaCrewException(status_code=404, code="MISSION_NOT_FOUND", message=f"Mission '{mission_id}' not found.")

        if exec_model.status != "IN_PROGRESS":
            raise AquaCrewException(
                status_code=400,
                code="CANNOT_ADAPT_ROUTE",
                message=f"Cannot adapt route when mission status is '{exec_model.status}'.",
            )

        rover = RoverRepository.get_by_id(db, exec_model.rover_id)
        current_pos = [exec_model.current_lng, exec_model.current_lat]

        # Target coordinates for detour
        detour_coord = new_anomaly_coord or [current_pos[0] + 0.0015, current_pos[1] + 0.0012]

        all_pipelines = PipelineRepository.get_all(db)
        detour_route = PipelineRoutingService.calculate_route(
            start_coord=current_pos,
            target_coord=detour_coord,
            pipeline_records=all_pipelines,
            target_segment_id=new_target_segment_id,
            rover_speed_mps=rover.velocity_mps or 0.55,
        )

        # Estimate additional battery requirement
        detour_drain = (detour_route.total_distance_m / 1000.0) * 1.8 + 1.5
        projected_battery = rover.battery_percentage - detour_drain
        if projected_battery < 20.0:
            raise AquaCrewException(
                status_code=400,
                code="INSUFFICIENT_BATTERY_FOR_ADAPTATION",
                message=f"Adaptive detour requires {detour_drain:.1f}% battery, leaving only {projected_battery:.1f}% (safety reserve requires >= 20%).",
            )

        # Record adaptation event
        history = json.loads(exec_model.adaptation_history_json or "[]")
        adapt_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": adaptation_reason,
            "detour_distance_m": round(detour_route.total_distance_m, 1),
            "new_target_coordinates": detour_coord,
            "projected_reserve_pct": round(projected_battery, 1),
        }
        history.append(adapt_entry)

        exec_model.route_adapted = True
        exec_model.adaptation_history_json = json.dumps(history)
        db.commit()

        InspectionIntelligenceRepository.log_event(
            db,
            event_type="ROUTE_ADAPTED",
            mission_id=mission_id,
            rover_id=rover.id,
            details=adapt_entry,
        )

        # Broadcast WebSocket event
        cls._broadcast_event({
            "type": "ROUTE_ADAPTED",
            "mission_id": mission_id,
            "rover_id": rover.id,
            "reason": adaptation_reason,
            "detour_coordinates": detour_coord,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return cls.get_progress(db, mission_id)

    @classmethod
    def get_progress(cls, db: Session, mission_id: str) -> InspectionExecutionProgressSchema:
        exec_model = InspectionIntelligenceRepository.get_execution_by_mission(db, mission_id)
        if not exec_model:
            raise AquaCrewException(status_code=404, code="MISSION_NOT_FOUND", message=f"Mission '{mission_id}' not found.")

        recent_obs = json.loads(exec_model.recent_observations_json or "[]")
        return InspectionExecutionProgressSchema(
            mission_id=exec_model.mission_id,
            rover_id=exec_model.rover_id,
            plan_id=exec_model.plan_id,
            status=exec_model.status,
            current_step=exec_model.current_step,
            total_steps=exec_model.total_steps,
            progress_percentage=exec_model.progress_percentage,
            current_coordinates=[exec_model.current_lng, exec_model.current_lat],
            distance_traversed_m=exec_model.distance_traversed_m,
            remaining_distance_m=exec_model.remaining_distance_m,
            battery_percentage=exec_model.battery_percentage,
            motor_temp_c=exec_model.motor_temp_c,
            active_anomalies_detected=exec_model.active_anomalies_count,
            route_adapted=exec_model.route_adapted,
            adaptation_history=json.loads(exec_model.adaptation_history_json or "[]"),
            recent_observations=[SimulatedSensorObservation(**o) for o in recent_obs[-10:]],
            last_updated=exec_model.updated_at.isoformat() if exec_model.updated_at else datetime.now(timezone.utc).isoformat(),
            is_simulated=True,
        )

    @classmethod
    def _generate_completion_report(
        cls,
        db: Session,
        exec_model: InspectionExecutionModel,
        plan: Optional[InspectionPlanModel],
        rover: RoverModel,
        observations: List[Dict[str, Any]],
    ) -> InspectionReportSchema:
        """
        Creates and stores the final evidence-grounded inspection report.
        """
        rep_id = f"INSP-REP-{uuid.uuid4().hex[:8].upper()}"
        anomalies = [o for o in observations if o.get("anomaly_detected")]

        report = InspectionReportSchema(
            id=rep_id,
            plan_id=exec_model.plan_id,
            mission_id=exec_model.mission_id,
            rover_id=rover.id,
            pipeline_segment_id="PIPE-SEC-01",
            segment_name="Metropolitan Secondary Water Main",
            inspection_method="ACOUSTIC_CORRELATION",
            start_time=exec_model.created_at.isoformat() if exec_model.created_at else datetime.now(timezone.utc).isoformat(),
            completion_time=datetime.now(timezone.utc).isoformat(),
            route_distance_m=round(exec_model.distance_traversed_m, 1),
            inspected_distance_m=round(exec_model.distance_traversed_m * 0.95, 1),
            sensor_observations_count=len(observations),
            detected_anomalies=anomalies,
            evidence_provenance="SIMULATED",
            ai_classification={
                "acoustic_leak_probability": 0.89 if anomalies else 0.12,
                "confidence": 0.91,
                "estimated_leak_orifice_mm": 12.5 if anomalies else 0.0,
            },
            updated_infrastructure_risk=32.0 if not anomalies else 78.5,
            inspection_outcome="SUCCESS",
            unresolved_uncertainties=["Internal tuberculation thickness unverified by acoustic alone."],
            recommended_next_action=(
                "Schedule excavation team to verify acoustic leak pinpoint at station +185m."
                if anomalies
                else "No significant structural anomalies identified. Return segment to nominal inspection cycle."
            ),
            operator_review_status="PENDING_REVIEW",
            reviewed_by=None,
            operator_notes=None,
            created_at=datetime.now(timezone.utc).isoformat(),
            is_simulated=True,
        )

        InspectionIntelligenceRepository.save_report(db, report)
        return report

