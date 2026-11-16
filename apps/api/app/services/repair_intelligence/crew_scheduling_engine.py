"""
AQUA CREW — Virtual Crew & Schedule Planning Engine (Task 16)
Evaluates virtual repair crew specializations, skills, travel distances, and schedule conflicts
to generate optimized virtual work orders and schedule items.
Strictly virtual simulation records; no real-world crew dispatch or physical actuation.
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import json
import uuid
import math

from app.models.repair_management import RepairCrewModel, RepairScheduleModel
from app.repositories.repair_repository import RepairRepository
from app.schemas.repair_management import (
    RepairMethodType,
    RepairScheduleItemSchema,
    RepairCrewSchema,
    RepairCrewMemberSchema,
)
from app.services.pipeline_routing_service import haversine_distance_m


class CrewSchedulingEngine:
    METHOD_TO_SPECIALIZATION = {
        "CLAMP_REPAIR": "PIPELINE_MECHANICAL",
        "JOINT_REPAIR_REPLACEMENT": "PIPELINE_MECHANICAL",
        "PIPE_SECTION_REPLACEMENT": "HEAVY_EXCAVATION",
        "INTERNAL_LINING_REHABILITATION": "TRENCHLESS_REHABILITATION",
        "CORROSION_PROTECTION": "PIPELINE_MECHANICAL",
        "VALVE_REPLACEMENT": "VALVE_AND_PRESSURE",
        "PRESSURE_MANAGEMENT": "VALVE_AND_PRESSURE",
        "FURTHER_INSPECTION_REQUIRED": "PIPELINE_MECHANICAL",
    }

    @classmethod
    def schedule_repair(
        cls,
        db: Session,
        repair_plan_id: str,
        selected_method: RepairMethodType,
        target_lat: float,
        target_lng: float,
        estimated_duration_hours: float = 6.0,
        preferred_crew_id: Optional[str] = None,
        desired_start_time: Optional[str] = None,
    ) -> RepairScheduleItemSchema:
        """
        Matches optimal virtual repair crew based on specialization, skills, and proximity,
        then calculates travel time and detects any calendar conflicts.
        """
        # Ensure default crews are seeded
        RepairRepository.seed_default_crews(db)
        crews = RepairRepository.list_crews(db)

        target_spec = cls.METHOD_TO_SPECIALIZATION.get(selected_method, "PIPELINE_MECHANICAL")

        # Filter by preferred or specialization
        candidate_crews = []
        if preferred_crew_id:
            candidate_crews = [c for c in crews if c.id == preferred_crew_id]
        if not candidate_crews:
            candidate_crews = [c for c in crews if c.specialization == target_spec and c.is_available]
        if not candidate_crews:
            # Fall back to any available crew
            candidate_crews = [c for c in crews if c.is_available] or crews

        # Rank candidates by proximity
        best_crew = None
        min_dist_km = float("inf")

        for crew in candidate_crews:
            dist_m = haversine_distance_m(
                [crew.base_location_lng, crew.base_location_lat],
                [target_lng, target_lat],
            )
            dist_km = dist_m / 1000.0
            if dist_km < min_dist_km:
                min_dist_km = dist_km
                best_crew = crew

        if not best_crew:
            best_crew = crews[0]
            min_dist_km = 5.2

        # Travel time: average urban utility speed of 35 km/h
        travel_hours = round(max(0.25, min_dist_km / 35.0), 2)

        # Scheduling window
        if desired_start_time:
            start_dt = datetime.fromisoformat(desired_start_time.replace("Z", "+00:00"))
        else:
            # Next morning 08:00 UTC
            now = datetime.now(timezone.utc)
            start_dt = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)

        end_dt = start_dt + timedelta(hours=estimated_duration_hours + travel_hours)

        # Detect schedule conflicts
        existing_schedules = db.query(RepairScheduleModel).filter(
            RepairScheduleModel.crew_id == best_crew.id,
            RepairScheduleModel.scheduled_end >= start_dt,
            RepairScheduleModel.scheduled_start <= end_dt,
        ).all()

        has_conflict = len(existing_schedules) > 0
        conflict_msg = None
        if has_conflict:
            conflict_msg = f"Virtual crew '{best_crew.crew_name}' already committed to Plan '{existing_schedules[0].repair_plan_id}' during this timeframe."

        schedule_id = f"SCH-{repair_plan_id.replace('PLAN-', '')}"

        return RepairScheduleItemSchema(
            schedule_id=schedule_id,
            repair_plan_id=repair_plan_id,
            crew_id=best_crew.id,
            crew_name=best_crew.crew_name,
            scheduled_start=start_dt.isoformat(),
            scheduled_end=end_dt.isoformat(),
            estimated_duration_hours=round(estimated_duration_hours, 1),
            travel_distance_km=round(min_dist_km, 1),
            travel_time_hours=travel_hours,
            has_schedule_conflicts=has_conflict,
            schedule_conflict_details=conflict_msg,
            scheduling_notes=f"Virtual crew schedule assigned to {best_crew.crew_name}. Travel distance {min_dist_km:.1f} km ({travel_hours:.1f} hrs transit).",
        )

