"""
AQUA CREW — Intelligent Rover Selection Engine
Scores eligible autonomous rovers using battery consumption models,
operating state, proximity, sensor payload, and thermal diagnostics.
"""
from typing import List, Dict, Any, Tuple, Optional
import math

from app.models.rover import RoverModel
from app.schemas.dispatch import RoverSuitability
from app.services.pipeline_routing_service import haversine_distance_m


class RoverSelectionService:
    BATTERY_SAFETY_RESERVE_PCT = 20.0
    ENERGY_TRAVEL_PCT_PER_KM = 1.8
    ENERGY_INSPECT_PCT_PER_HR = 4.0

    @classmethod
    def evaluate_rover(
        cls,
        rover: RoverModel,
        target_lat: float,
        target_lng: float,
        target_pipe_meta: Optional[Dict[str, Any]] = None,
    ) -> RoverSuitability:
        # Distance calculation
        rover_coord = [rover.longitude, rover.latitude]
        target_coord = [target_lng, target_lat]
        dist_m = haversine_distance_m(rover_coord, target_coord)
        dist_km = dist_m / 1000.0

        # Energy consumption estimate
        # Travel out + 30 min inspection + Travel back
        travel_out_pct = dist_km * cls.ENERGY_TRAVEL_PCT_PER_KM
        inspect_pct = 0.5 * cls.ENERGY_INSPECT_PCT_PER_HR  # 30 min default inspection
        return_pct = dist_km * cls.ENERGY_TRAVEL_PCT_PER_KM
        total_energy_pct = round(travel_out_pct + inspect_pct + return_pct, 1)

        reserve_after_pct = round(rover.battery_percentage - total_energy_pct, 1)

        # Disqualification checks
        is_eligible = True
        disqual_reason = None

        if rover.connection_status != "ONLINE":
            is_eligible = False
            disqual_reason = f"Rover connection status is {rover.connection_status} (must be ONLINE)."
        elif rover.operating_state != "IDLE":
            is_eligible = False
            disqual_reason = f"Rover operating state is {rover.operating_state} (must be IDLE)."
        elif rover.battery_percentage < (total_energy_pct + cls.BATTERY_SAFETY_RESERVE_PCT):
            is_eligible = False
            disqual_reason = (
                f"Insufficient battery: {rover.battery_percentage:.1f}% available, "
                f"mission requires {total_energy_pct:.1f}% with {cls.BATTERY_SAFETY_RESERVE_PCT}% safety reserve."
            )
        elif rover.motor_temp_c >= 50.0:
            is_eligible = False
            disqual_reason = f"Elevated motor temperature ({rover.motor_temp_c}°C >= 50°C safety threshold)."

        # Suitability Scoring (0–100)
        suitability_score = 0.0

        # 1. Proximity Score (Max 40 pts)
        # Closer than 500m -> 40 pts, decays up to 3000m
        proximity_score = max(5.0, 40.0 * math.exp(-dist_m / 1200.0))
        suitability_score += proximity_score

        # 2. Battery Reserve Score (Max 30 pts)
        battery_surplus = max(0.0, reserve_after_pct - cls.BATTERY_SAFETY_RESERVE_PCT)
        battery_score = min(30.0, (battery_surplus / 50.0) * 30.0)
        suitability_score += battery_score

        # 3. Sensor & Model Match (Max 20 pts)
        sensor_score = 15.0
        model_name = (rover.model or "").lower()
        if "crawler" in model_name or "acoustic" in model_name:
            sensor_score = 20.0
        elif "drone" in model_name:
            sensor_score = 10.0
        suitability_score += sensor_score

        # 4. Diagnostics & Thermal Status (Max 10 pts)
        temp = rover.motor_temp_c or 25.0
        thermal_score = max(2.0, 10.0 - max(0.0, (temp - 30.0) * 0.4))
        suitability_score += thermal_score

        final_suitability = round(min(100.0, max(0.0, suitability_score)), 1)
        if not is_eligible:
            final_suitability = 0.0

        explanation = (
            f"Suitability {final_suitability}/100: Proximity {proximity_score:.0f} pts ({dist_m:.0f}m away), "
            f"Battery Reserve {battery_score:.0f} pts ({reserve_after_pct:.1f}% remaining after mission), "
            f"Payload compatibility {sensor_score:.0f} pts."
        )
        if not is_eligible:
            explanation = f"INELIGIBLE: {disqual_reason}"

        return RoverSuitability(
            rover_id=rover.id,
            rover_name=rover.name,
            operating_state=rover.operating_state,
            battery_percentage=rover.battery_percentage,
            is_eligible=is_eligible,
            disqualification_reason=disqual_reason,
            distance_to_target_m=round(dist_m, 1),
            estimated_energy_consumption_pct=total_energy_pct,
            battery_reserve_after_pct=reserve_after_pct,
            suitability_score=final_suitability,
            suitability_explanation=explanation,
        )

    @classmethod
    def rank_rovers_for_target(
        cls,
        rovers: List[RoverModel],
        target_lat: float,
        target_lng: float,
        target_pipe_meta: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[RoverSuitability], List[RoverSuitability]]:
        eligible: List[RoverSuitability] = []
        ineligible: List[RoverSuitability] = []

        for r in rovers:
            suit = cls.evaluate_rover(r, target_lat, target_lng, target_pipe_meta)
            if suit.is_eligible:
                eligible.append(suit)
            else:
                ineligible.append(suit)

        # Sort eligible descending by suitability score
        eligible.sort(key=lambda s: s.suitability_score, reverse=True)
        return eligible, ineligible

