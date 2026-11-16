"""
AQUA CREW — Centralized Mission Planning Service
Orchestrates mission priority evaluation, pipeline graph routing, intelligent rover selection,
and human-in-the-loop operator approval workflows.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import uuid
import asyncio

from sqlalchemy.orm import Session
from app.models.mission_recommendation import MissionRecommendationModel
from app.models.ai_detection import AiDetectionModel
from app.models.rover import RoverModel
from app.models.mission import MissionModel
from app.repositories.pipeline_repository import PipelineRepository, DEFAULT_PIPELINES
from app.repositories.rover_repository import RoverRepository
from app.repositories.mission_repository import MissionRepository
from app.repositories.event_repository import EventRepository
from app.services.mission_priority_service import MissionPriorityService
from app.services.pipeline_routing_service import PipelineRoutingService
from app.services.rover_selection_service import RoverSelectionService
from app.services.rover_service import RoverService
from app.websocket.connection_manager import ws_manager
from app.core.exceptions import AquaCrewException


class MissionPlanningService:
    @staticmethod
    def _get_pipe_meta(db: Session, segment_id: str) -> Dict[str, Any]:
        seg = PipelineRepository.get_by_id(db, segment_id)
        if seg:
            return {
                "id": seg.id,
                "name": seg.name,
                "category": seg.category,
                "material": seg.material,
                "coordinates": seg.coordinates_json,
                "length_m": seg.length_m,
            }
        for d in DEFAULT_PIPELINES:
            if d["id"] == segment_id:
                return d
        return {
            "id": segment_id,
            "name": f"Segment {segment_id}",
            "category": "secondary",
            "material": "ductile_iron",
            "coordinates": [[-74.0060, 40.7128], [-74.0010, 40.7140]],
            "length_m": 1000.0,
        }

    @classmethod
    def plan_mission_for_detection(
        cls,
        db: Session,
        detection_id: str,
        preferred_rover_id: Optional[str] = None,
        priority_override: Optional[str] = None,
    ) -> MissionRecommendationModel:
        detection = db.query(AiDetectionModel).filter(AiDetectionModel.id == detection_id).first()
        if not detection:
            raise AquaCrewException(
                status_code=404,
                code="DETECTION_NOT_FOUND",
                message=f"AI Detection '{detection_id}' not found.",
            )

        # Duplicate protection: check if an active (non-rejected) recommendation already exists
        existing_rec = db.query(MissionRecommendationModel).filter(
            MissionRecommendationModel.detection_id == detection_id,
            MissionRecommendationModel.status.in_(["PENDING_APPROVAL", "APPROVED"])
        ).first()

        if existing_rec:
            return existing_rec

        pipe_meta = cls._get_pipe_meta(db, detection.pipeline_segment_id)

        # 1. Mission Priority Evaluation
        priority_assessment = MissionPriorityService.calculate_priority(detection, pipe_meta)
        if priority_override:
            priority_assessment.priority_category = priority_override.upper()

        # 2. Target Coordinates Resolution
        target_lat = detection.estimated_latitude
        target_lng = detection.estimated_longitude
        uncertainty_m = detection.localization_uncertainty_m or 20.0

        if target_lat is None or target_lng is None:
            # Fallback to pipeline segment midpoint
            raw_c = pipe_meta.get("coordinates", [])
            coords = json.loads(raw_c) if isinstance(raw_c, str) else raw_c
            mid = coords[len(coords) // 2] if coords else [-74.0060, 40.7128]
            target_lng, target_lat = mid[0], mid[1]
            uncertainty_m = 45.0  # Coarse segment search

        # 3. Intelligent Rover Selection
        rovers = RoverRepository.get_all(db)
        eligible, ineligible = RoverSelectionService.rank_rovers_for_target(
            rovers, target_lat, target_lng, pipe_meta
        )

        chosen_rover_id: Optional[str] = None
        chosen_rover_name = ""
        chosen_suitability = 50.0

        if preferred_rover_id:
            # Verify if preferred rover exists
            target_rover = next((r for r in rovers if r.id == preferred_rover_id), None)
            if target_rover:
                chosen_rover_id = target_rover.id
                chosen_rover_name = target_rover.name
                suit = RoverSelectionService.evaluate_rover(target_rover, target_lat, target_lng, pipe_meta)
                chosen_suitability = suit.suitability_score
        elif eligible:
            chosen_rover_id = eligible[0].rover_id
            chosen_rover_name = eligible[0].rover_name
            chosen_suitability = eligible[0].suitability_score
        else:
            # If no rover is strictly eligible, select the best candidate from rovers and flag for operator review
            best_candidate = rovers[0] if rovers else None
            if best_candidate:
                chosen_rover_id = best_candidate.id
                chosen_rover_name = best_candidate.name
                chosen_suitability = 10.0

        if not chosen_rover_id:
            raise AquaCrewException(
                status_code=400,
                code="NO_ROVERS_CONFIGURED",
                message="No rovers registered in fleet database.",
            )

        # 4. Pipeline Routing (Dijkstra Shortest Path)
        chosen_rover = next((r for r in rovers if r.id == chosen_rover_id), rovers[0])
        start_coord = [chosen_rover.longitude, chosen_rover.latitude]
        target_coord = [target_lng, target_lat]

        all_pipelines = PipelineRepository.get_all(db)
        route = PipelineRoutingService.calculate_route(
            start_coord=start_coord,
            target_coord=target_coord,
            pipeline_records=all_pipelines,
            target_segment_id=detection.pipeline_segment_id,
            rover_speed_mps=chosen_rover.velocity_mps or 0.55,
            uncertainty_radius_m=uncertainty_m,
        )

        # 5. Energy and Duration Metrics
        dist_km = route.total_distance_m / 1000.0
        energy_pct = round(dist_km * 3.6 + 2.0, 1)  # out + return + inspection
        reserve_after_pct = round(max(0.0, chosen_rover.battery_percentage - energy_pct), 1)

        # 6. Recommendation Construction & Persistence
        rec_id = f"REC-2026-{uuid.uuid4().hex[:6].upper()}"
        explanation = (
            f"Recommended {chosen_rover_name} ({chosen_rover_id}) with suitability score {chosen_suitability:.0f}/100. "
            f"Mission Priority: {priority_assessment.priority_category} ({priority_assessment.priority_score:.0f}/100). "
            f"Planned pipeline distance: {route.total_distance_m:.0f}m ({route.estimated_travel_time_s / 60:.1f} min). "
            f"Estimated energy: {energy_pct:.1f}% (Projected reserve: {reserve_after_pct:.1f}%)."
        )

        rec = MissionRecommendationModel(
            id=rec_id,
            detection_id=detection.id,
            pipeline_segment_id=detection.pipeline_segment_id,
            recommended_rover_id=chosen_rover_id,
            recommended_rover_name=chosen_rover_name,
            priority_score=priority_assessment.priority_score,
            priority_category=priority_assessment.priority_category,
            status="PENDING_APPROVAL",
            route_distance_m=route.total_distance_m,
            estimated_duration_s=route.estimated_travel_time_s,
            estimated_energy_pct=energy_pct,
            battery_reserve_after_pct=reserve_after_pct,
            destination_lat=target_lat,
            destination_lng=target_lng,
            localization_uncertainty_m=uncertainty_m,
            route_waypoints_json=json.dumps(route.waypoints),
            route_segments_json=json.dumps(route.segments_traversed),
            contributing_factors=json.dumps(priority_assessment.contributing_factors),
            explanation=explanation,
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        # 7. WebSocket Event Broadcast
        cls._broadcast_recommendation_event("MISSION_RECOMMENDATION_CREATED", rec)
        return rec

    @classmethod
    async def approve_recommendation(
        cls,
        db: Session,
        recommendation_id: str,
        operator_id: str = "OPERATOR_CHIEF",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Atomically check and update recommendation status to 'APPROVING'
        # to prevent concurrent double-approval race condition
        rows_updated = db.query(MissionRecommendationModel).filter(
            MissionRecommendationModel.id == recommendation_id,
            MissionRecommendationModel.status == "PENDING_APPROVAL"
        ).update({"status": "APPROVING", "updated_at": datetime.now(timezone.utc)})
        db.flush()

        if rows_updated == 0:
            existing = db.query(MissionRecommendationModel).filter(
                MissionRecommendationModel.id == recommendation_id
            ).first()
            if not existing:
                raise AquaCrewException(
                    status_code=404,
                    code="RECOMMENDATION_NOT_FOUND",
                    message=f"Recommendation '{recommendation_id}' not found.",
                )
            raise AquaCrewException(
                status_code=400,
                code="INVALID_RECOMMENDATION_STATE",
                message=f"Recommendation is in status '{existing.status}' (must be PENDING_APPROVAL).",
            )

        rec = db.query(MissionRecommendationModel).filter(
            MissionRecommendationModel.id == recommendation_id
        ).first()

        rover = RoverRepository.get_by_id(db, rec.recommended_rover_id)
        if not rover:
            # Revert rec status
            db.query(MissionRecommendationModel).filter(
                MissionRecommendationModel.id == recommendation_id
            ).update({"status": "PENDING_APPROVAL"})
            db.commit()
            raise AquaCrewException(status_code=404, code="ROVER_NOT_FOUND", message="Recommended rover not found.")

        # Guard: Rover must be in IDLE state for dispatch
        if rover.operating_state != "IDLE":
            db.query(MissionRecommendationModel).filter(
                MissionRecommendationModel.id == recommendation_id
            ).update({"status": "PENDING_APPROVAL"})
            db.commit()
            raise AquaCrewException(
                status_code=400,
                code="ROVER_NOT_IDLE",
                message=f"Rover {rover.id} cannot be dispatched: current state is {rover.operating_state}.",
            )

        # Guard: Check minimum battery safety reserve
        if rover.battery_percentage < (rec.estimated_energy_pct + 15.0):
            db.query(MissionRecommendationModel).filter(
                MissionRecommendationModel.id == recommendation_id
            ).update({"status": "PENDING_APPROVAL"})
            db.commit()
            raise AquaCrewException(
                status_code=400,
                code="INSUFFICIENT_BATTERY",
                message=f"Rover {rover.id} battery is {rover.battery_percentage:.1f}%, mission requires {rec.estimated_energy_pct:.1f}% + 15% safety reserve.",
            )

        # Atomically claim rover if operating_state == 'IDLE' and not assigned
        rover_claimed = db.query(RoverModel).filter(
            RoverModel.id == rover.id,
            RoverModel.operating_state == "IDLE",
            (RoverModel.assigned_mission_id.is_(None) | (RoverModel.assigned_mission_id == ""))
        ).update({
            "operating_state": "INSPECTING",
            "current_mission": f"Autonomous Inspection: {rec.pipeline_segment_id}",
            "pipe_segment_id": rec.pipeline_segment_id,
            "route_progress_pct": 0,
        })
        db.flush()

        if rover_claimed == 0:
            db.query(MissionRecommendationModel).filter(
                MissionRecommendationModel.id == recommendation_id
            ).update({"status": "PENDING_APPROVAL"})
            db.commit()
            raise AquaCrewException(
                status_code=409,
                code="ROVER_ALREADY_ASSIGNED",
                message=f"Rover {rover.id} is concurrently assigned or no longer idle.",
            )

        # Create Formal Mission
        mission_id = f"MSN-2026-{uuid.uuid4().hex[:6].upper()}"
        mission = MissionModel(
            id=mission_id,
            assigned_rover_id=rover.id,
            assigned_rover_name=rover.name,
            mission_type=f"Autonomous Leak Inspection ({rec.priority_category})",
            progress_percentage=0,
            status="In Progress",
            start_time=f"{datetime.now(timezone.utc).strftime('%H:%M')} UTC (Dispatched)",
            estimated_completion_time=f"{(rec.estimated_duration_s / 60.0):.0f} min",
            target_segment_id=rec.pipeline_segment_id,
            waypoint_count=len(json.loads(rec.route_waypoints_json)),
            completed_waypoints=0,
            recommendation_id=rec.id,
            source_detection_id=rec.detection_id,
            priority_category=rec.priority_category,
            route_distance_m=rec.route_distance_m,
            inspected_distance_m=0.0,
            route_waypoints_json=rec.route_waypoints_json,
            is_simulated=True,
        )
        db.add(mission)

        # Update Rover state and mission reference
        rover.assigned_mission_id = mission.id

        # Update Recommendation
        rec.status = "APPROVED"
        rec.assigned_mission_id = mission.id
        rec.approved_by = operator_id
        rec.operator_notes = notes
        rec.approved_at = datetime.now(timezone.utc)
        rec.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(mission)
        db.refresh(rec)

        # Transition rover state to INSPECTING
        await RoverService.execute_command(
            db,
            rover_id=rover.id,
            command="SET_STATE",
            target_state="INSPECTING",
            reason=f"Dispatched by operator {operator_id} for mission {mission.id}",
            triggered_by=operator_id,
        )

        # Audit event
        EventRepository.log_audit_event(
            db,
            event_type="MISSION_APPROVED_AND_DISPATCHED",
            details=f"Operator {operator_id} approved recommendation {rec.id}. Dispatched rover {rover.id} for mission {mission.id}.",
            rover_id=rover.id,
            mission_id=mission.id,
        )

        # Broadcast WebSocket events
        cls._broadcast_recommendation_event("MISSION_RECOMMENDATION_APPROVED", rec)
        cls._broadcast_rover_dispatched_event(rover, mission, rec)

        return {
            "success": True,
            "message": f"Mission {mission.id} successfully created and rover {rover.id} dispatched.",
            "recommendation_id": rec.id,
            "mission_id": mission.id,
            "rover_id": rover.id,
            "status": "APPROVED",
        }

    @classmethod
    def reject_recommendation(
        cls,
        db: Session,
        recommendation_id: str,
        reason: str,
        operator_notes: Optional[str] = None,
    ) -> MissionRecommendationModel:
        rec = db.query(MissionRecommendationModel).filter(
            MissionRecommendationModel.id == recommendation_id
        ).first()

        if not rec:
            raise AquaCrewException(
                status_code=404,
                code="RECOMMENDATION_NOT_FOUND",
                message=f"Recommendation '{recommendation_id}' not found.",
            )

        if rec.status != "PENDING_APPROVAL":
            raise AquaCrewException(
                status_code=400,
                code="INVALID_RECOMMENDATION_STATE",
                message=f"Recommendation is in status '{rec.status}' (must be PENDING_APPROVAL to reject).",
            )

        rec.status = "REJECTED"
        rec.rejection_reason = reason
        rec.operator_notes = operator_notes
        rec.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)

        EventRepository.log_audit_event(
            db,
            event_type="MISSION_RECOMMENDATION_REJECTED",
            details=f"Recommendation {rec.id} rejected. Reason: {reason}",
            rover_id=rec.recommended_rover_id,
        )

        cls._broadcast_recommendation_event("MISSION_RECOMMENDATION_REJECTED", rec)
        return rec

    @classmethod
    def list_recommendations(
        cls,
        db: Session,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
    ) -> List[MissionRecommendationModel]:
        q = db.query(MissionRecommendationModel)
        if status:
            q = q.filter(MissionRecommendationModel.status == status.upper())
        if priority:
            q = q.filter(MissionRecommendationModel.priority_category == priority.upper())
        return q.order_by(MissionRecommendationModel.created_at.desc()).limit(limit).all()

    @classmethod
    def get_recommendation_by_id(cls, db: Session, rec_id: str) -> Optional[MissionRecommendationModel]:
        return db.query(MissionRecommendationModel).filter(MissionRecommendationModel.id == rec_id).first()

    @classmethod
    def recalculate_recommendation(
        cls,
        db: Session,
        recommendation_id: str,
    ) -> MissionRecommendationModel:
        rec = db.query(MissionRecommendationModel).filter(
            MissionRecommendationModel.id == recommendation_id
        ).first()

        if not rec:
            raise AquaCrewException(
                status_code=404,
                code="RECOMMENDATION_NOT_FOUND",
                message=f"Recommendation '{recommendation_id}' not found.",
            )

        if rec.status != "PENDING_APPROVAL":
            raise AquaCrewException(
                status_code=400,
                code="INVALID_RECOMMENDATION_STATE",
                message=f"Recommendation is in status '{rec.status}' (must be PENDING_APPROVAL to reject).",
            )

        if rec.status != "PENDING_APPROVAL":
            raise AquaCrewException(
                status_code=400,
                code="INVALID_RECOMMENDATION_STATE",
                message=f"Only PENDING_APPROVAL recommendations can be recalculated (current: {rec.status}).",
            )

        detection = db.query(AiDetectionModel).filter(AiDetectionModel.id == rec.detection_id).first()
        if not detection:
            raise AquaCrewException(
                status_code=404,
                code="DETECTION_NOT_FOUND",
                message=f"Underlying detection '{rec.detection_id}' not found.",
            )

        pipe_meta = cls._get_pipe_meta(db, detection.pipeline_segment_id)

        # 1. Mission Priority Evaluation
        priority_assessment = MissionPriorityService.calculate_priority(detection, pipe_meta)

        # 2. Target Coordinates Resolution
        target_lat = detection.estimated_latitude
        target_lng = detection.estimated_longitude
        uncertainty_m = detection.localization_uncertainty_m or 20.0

        if target_lat is None or target_lng is None:
            raw_c = pipe_meta.get("coordinates", [])
            coords = json.loads(raw_c) if isinstance(raw_c, str) else raw_c
            mid = coords[len(coords) // 2] if coords else [-74.0060, 40.7128]
            target_lng, target_lat = mid[0], mid[1]
            uncertainty_m = 45.0

        # 3. Intelligent Rover Selection
        rovers = RoverRepository.get_all(db)
        eligible, ineligible = RoverSelectionService.rank_rovers_for_target(
            rovers, target_lat, target_lng, pipe_meta
        )

        chosen_rover_id: Optional[str] = None
        chosen_rover_name = ""
        chosen_suitability = 50.0

        if eligible:
            chosen_rover_id = eligible[0].rover_id
            chosen_rover_name = eligible[0].rover_name
            chosen_suitability = eligible[0].suitability_score
        else:
            best_candidate = rovers[0] if rovers else None
            if best_candidate:
                chosen_rover_id = best_candidate.id
                chosen_rover_name = best_candidate.name
                chosen_suitability = 10.0

        if not chosen_rover_id:
            raise AquaCrewException(
                status_code=400,
                code="NO_ROVERS_CONFIGURED",
                message="No rovers registered in fleet database.",
            )

        # 4. Pipeline Routing (Dijkstra Shortest Path)
        chosen_rover = next((r for r in rovers if r.id == chosen_rover_id), rovers[0])
        start_coord = [chosen_rover.longitude, chosen_rover.latitude]
        target_coord = [target_lng, target_lat]

        all_pipelines = PipelineRepository.get_all(db)
        route = PipelineRoutingService.calculate_route(
            start_coord=start_coord,
            target_coord=target_coord,
            pipeline_records=all_pipelines,
            target_segment_id=detection.pipeline_segment_id,
            rover_speed_mps=chosen_rover.velocity_mps or 0.55,
            uncertainty_radius_m=uncertainty_m,
        )

        # 5. Energy and Duration Metrics
        dist_km = route.total_distance_m / 1000.0
        energy_pct = round(dist_km * 3.6 + 2.0, 1)
        reserve_after_pct = round(max(0.0, chosen_rover.battery_percentage - energy_pct), 1)

        # 6. Update Recommendation
        explanation = (
            f"Recalculated: Recommended {chosen_rover_name} ({chosen_rover_id}) with suitability {chosen_suitability:.0f}/100. "
            f"Mission Priority: {priority_assessment.priority_category} ({priority_assessment.priority_score:.0f}/100). "
            f"Planned pipeline distance: {route.total_distance_m:.0f}m ({route.estimated_travel_time_s / 60:.1f} min). "
            f"Estimated energy: {energy_pct:.1f}% (Projected reserve: {reserve_after_pct:.1f}%)."
        )

        rec.recommended_rover_id = chosen_rover_id
        rec.recommended_rover_name = chosen_rover_name
        rec.priority_score = priority_assessment.priority_score
        rec.priority_category = priority_assessment.priority_category
        rec.route_distance_m = route.total_distance_m
        rec.estimated_duration_s = route.estimated_travel_time_s
        rec.estimated_energy_pct = energy_pct
        rec.battery_reserve_after_pct = reserve_after_pct
        rec.destination_lat = target_lat
        rec.destination_lng = target_lng
        rec.localization_uncertainty_m = uncertainty_m
        rec.route_waypoints_json = json.dumps(route.waypoints)
        rec.route_segments_json = json.dumps(route.segments_traversed)
        rec.contributing_factors = json.dumps(priority_assessment.contributing_factors)
        rec.explanation = explanation
        rec.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(rec)

        cls._broadcast_recommendation_event("MISSION_RECOMMENDATION_UPDATED", rec)
        return rec

    @staticmethod
    def _broadcast_recommendation_event(event_type: str, rec: MissionRecommendationModel):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                ws_manager.broadcast({
                    "type": event_type,
                    "recommendation_id": rec.id,
                    "detection_id": rec.detection_id,
                    "pipeline_segment_id": rec.pipeline_segment_id,
                    "recommended_rover_id": rec.recommended_rover_id,
                    "priority_category": rec.priority_category,
                    "priority_score": rec.priority_score,
                    "status": rec.status,
                    "route_distance_m": rec.route_distance_m,
                    "timestamp": rec.updated_at.isoformat(),
                    "is_simulated": True,
                })
            )
        except RuntimeError:
            pass

    @staticmethod
    def _broadcast_rover_dispatched_event(rover: RoverModel, mission: MissionModel, rec: MissionRecommendationModel):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                ws_manager.broadcast({
                    "type": "ROVER_DISPATCHED",
                    "rover_id": rover.id,
                    "mission_id": mission.id,
                    "recommendation_id": rec.id,
                    "target_segment_id": mission.target_segment_id,
                    "destination": {
                        "latitude": rec.destination_lat,
                        "longitude": rec.destination_lng,
                        "uncertainty_m": rec.localization_uncertainty_m,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "is_simulated": True,
                })
            )
        except RuntimeError:
            pass
