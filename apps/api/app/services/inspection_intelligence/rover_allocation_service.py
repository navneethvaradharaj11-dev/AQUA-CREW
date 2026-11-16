"""
AQUA CREW — Adaptive Rover Allocation & Fleet Coordination Service (Task 15)
Evaluates virtual rover fleet suitability, checks battery safety reserves, validates sensor payload matches,
and executes conflict-free multi-rover target allocation with load balancing.
"""
from typing import Dict, Any, List, Optional, Tuple
import math
from sqlalchemy.orm import Session

from app.models.rover import RoverModel
from app.models.pipeline_segment import PipelineSegmentModel
from app.schemas.inspection_intelligence import (
    RoverSuitabilitySchema,
    InspectionPlanTargetSchema,
    InspectionMethod,
)
from app.repositories.rover_repository import RoverRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.services.pipeline_routing_service import haversine_distance_m


# Known payload capabilities for virtual rover models
ROVER_PAYLOAD_MAP: Dict[str, List[str]] = {
    "ROV-AQUA-01": ["pipe_navigation", "hydrophone_acoustic", "high_res_optical"],
    "ROV-AQUA-02": ["pipe_navigation", "hydrophone_acoustic", "thermal_infrared", "ultrasonic_thickness"],
    "ROV-AQUA-03": ["pipe_navigation", "high_res_optical", "thermal_infrared", "crawler_traction"],
    "ROV-AQUA-04": ["pipe_navigation", "hydrophone_acoustic", "high_res_optical", "ultrasonic_thickness"],
}

DEFAULT_CAPABILITIES = ["pipe_navigation", "hydrophone_acoustic", "high_res_optical"]


class RoverAllocationService:
    BATTERY_SAFETY_RESERVE_PCT: float = 20.0
    ENERGY_TRAVEL_PCT_PER_KM: float = 1.8
    ENERGY_INSPECT_PCT_PER_HR: float = 4.0

    @classmethod
    def get_rover_capabilities(cls, rover_id: str) -> List[str]:
        return ROVER_PAYLOAD_MAP.get(rover_id, DEFAULT_CAPABILITIES)

    @classmethod
    def evaluate_rover_suitability(
        cls,
        rover: RoverModel,
        target_lat: float,
        target_lng: float,
        required_method: InspectionMethod = "ACOUSTIC_CORRELATION",
        inspection_duration_minutes: int = 30,
        safety_reserve_pct: float = 20.0,
    ) -> RoverSuitabilitySchema:
        """
        Evaluates a single virtual rover's eligibility and suitability score for a target.
        """
        rover_coord = [rover.longitude, rover.latitude]
        target_coord = [target_lng, target_lat]
        dist_m = haversine_distance_m(rover_coord, target_coord)
        dist_km = dist_m / 1000.0

        # Energy consumption estimate:
        # Travel out + inspection duration + Travel return
        travel_out_pct = dist_km * cls.ENERGY_TRAVEL_PCT_PER_KM
        inspect_pct = (inspection_duration_minutes / 60.0) * cls.ENERGY_INSPECT_PCT_PER_HR
        return_pct = dist_km * cls.ENERGY_TRAVEL_PCT_PER_KM
        total_drain_pct = round(travel_out_pct + inspect_pct + return_pct, 1)

        projected_reserve_pct = round(rover.battery_percentage - total_drain_pct, 1)
        has_safe_reserve = projected_reserve_pct >= safety_reserve_pct

        # Check payload capability match
        caps = cls.get_rover_capabilities(rover.id)
        capability_match = True
        if required_method == "ACOUSTIC_CORRELATION" and "hydrophone_acoustic" not in caps:
            capability_match = False
        elif required_method == "THERMAL_INFRARED" and "thermal_infrared" not in caps:
            capability_match = False
        elif required_method == "ULTRASONIC_THICKNESS" and "ultrasonic_thickness" not in caps:
            capability_match = False
        elif required_method == "MULTI_SENSOR_CRAWLER" and not ("hydrophone_acoustic" in caps and "high_res_optical" in caps):
            capability_match = False

        # Disqualification checks
        is_eligible = True
        disqual_reasons: List[str] = []

        if rover.connection_status != "ONLINE":
            is_eligible = False
            disqual_reasons.append(f"Rover connection status is '{rover.connection_status}' (must be ONLINE).")

        if rover.operating_state != "IDLE":
            is_eligible = False
            disqual_reasons.append(f"Rover operating state is '{rover.operating_state}' (must be IDLE).")

        if rover.battery_percentage < (total_drain_pct + safety_reserve_pct):
            is_eligible = False
            disqual_reasons.append(
                f"Insufficient battery: {rover.battery_percentage:.1f}% available, "
                f"mission requires {total_drain_pct:.1f}% + {safety_reserve_pct:.1f}% reserve."
            )

        if rover.motor_temp_c >= 50.0:
            is_eligible = False
            disqual_reasons.append(f"Elevated motor temperature ({rover.motor_temp_c:.1f}°C >= 50.0°C safety threshold).")

        if not capability_match:
            is_eligible = False
            disqual_reasons.append(f"Sensor payload does not support required inspection method '{required_method}'.")

        # Suitability Score Formulation (0-100)
        # Factors: Proximity (40%), Battery Surplus (35%), Motor Health (15%), Sensor Fit (10%)
        if not is_eligible:
            suitability_score = 0.0
        else:
            prox_score = max(0.0, 100.0 - (dist_km * 15.0))
            batt_score = min(100.0, max(0.0, projected_reserve_pct))
            temp_score = max(0.0, (50.0 - rover.motor_temp_c) * 4.0)
            suitability_score = round(
                0.40 * prox_score + 0.35 * batt_score + 0.15 * temp_score + 0.10 * 100.0, 1
            )

        travel_time_s = (dist_m / max(0.3, rover.velocity_mps or 0.55))

        return RoverSuitabilitySchema(
            rover_id=rover.id,
            rover_name=rover.name,
            is_eligible=is_eligible,
            suitability_score=suitability_score,
            battery_percentage=round(rover.battery_percentage, 1),
            projected_battery_drain_pct=total_drain_pct,
            projected_battery_reserve_pct=projected_reserve_pct,
            has_safe_return_reserve=has_safe_reserve,
            motor_temperature_c=round(rover.motor_temp_c, 1),
            sensor_capabilities=caps,
            capability_match=capability_match,
            operating_state=rover.operating_state,
            connection_status=rover.connection_status,
            distance_to_target_m=round(dist_m, 1),
            estimated_travel_time_s=round(travel_time_s, 1),
            disqualification_reasons=disqual_reasons,
        )

    @classmethod
    def rank_fleet_for_target(
        cls,
        rovers: List[RoverModel],
        target_lat: float,
        target_lng: float,
        required_method: InspectionMethod = "ACOUSTIC_CORRELATION",
        inspection_duration_minutes: int = 30,
        safety_reserve_pct: float = 20.0,
    ) -> Tuple[List[RoverSuitabilitySchema], List[RoverSuitabilitySchema]]:
        """
        Ranks fleet into (eligible_sorted, ineligible).
        """
        eligible: List[RoverSuitabilitySchema] = []
        ineligible: List[RoverSuitabilitySchema] = []

        for r in rovers:
            suit = cls.evaluate_rover_suitability(
                rover=r,
                target_lat=target_lat,
                target_lng=target_lng,
                required_method=required_method,
                inspection_duration_minutes=inspection_duration_minutes,
                safety_reserve_pct=safety_reserve_pct,
            )
            if suit.is_eligible:
                eligible.append(suit)
            else:
                ineligible.append(suit)

        eligible.sort(key=lambda s: s.suitability_score, reverse=True)
        return eligible, ineligible

    @classmethod
    def allocate_multi_rover_targets(
        cls,
        db: Session,
        targets: List[InspectionPlanTargetSchema],
        preferred_rover_ids: Optional[List[str]] = None,
        max_targets_per_rover: int = 3,
        safety_reserve_pct: float = 20.0,
    ) -> Tuple[Dict[str, List[InspectionPlanTargetSchema]], List[str]]:
        """
        Multi-rover coordinated allocation.
        Distributes targets across available fleet without duplicate assignments.
        Returns (rover_target_mapping, unallocated_target_ids).
        """
        all_rovers = RoverRepository.get_all(db)
        if preferred_rover_ids:
            all_rovers = [r for r in all_rovers if r.id in preferred_rover_ids]

        # Filter strictly idle and online rovers
        available_rovers = [r for r in all_rovers if r.operating_state == "IDLE" and r.connection_status == "ONLINE"]

        allocation_map: Dict[str, List[InspectionPlanTargetSchema]] = {r.id: [] for r in available_rovers}
        unallocated_target_ids: List[str] = []

        # Sort targets descending by priority score
        sorted_targets = sorted(targets, key=lambda t: t.priority_score, reverse=True)

        for target in sorted_targets:
            t_lng, t_lat = target.target_coordinates[0], target.target_coordinates[1]

            # Find best candidate rover that hasn't exceeded max_targets_per_rover
            best_rover_id = None
            best_score = -1.0

            for rover in available_rovers:
                if len(allocation_map[rover.id]) >= max_targets_per_rover:
                    continue

                suit = cls.evaluate_rover_suitability(
                    rover=rover,
                    target_lat=t_lat,
                    target_lng=t_lng,
                    required_method=target.inspection_method,
                    inspection_duration_minutes=target.estimated_duration_minutes,
                    safety_reserve_pct=safety_reserve_pct,
                )

                if suit.is_eligible and suit.suitability_score > best_score:
                    best_score = suit.suitability_score
                    best_rover_id = rover.id

            if best_rover_id:
                allocation_map[best_rover_id].append(target)
            else:
                unallocated_target_ids.append(target.target_id)

        # Filter out rovers with zero assignments
        active_allocations = {r_id: tgts for r_id, tgts in allocation_map.items() if len(tgts) > 0}
        return active_allocations, unallocated_target_ids

