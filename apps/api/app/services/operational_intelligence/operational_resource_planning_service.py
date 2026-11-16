"""
Operational Resource & Maintenance Planning Service (Task 12 - Phase 7)
Evaluates virtual rover fleet readiness, battery reserves, thermal safety constraints,
and traversal feasibility for candidate inspection targets.
Strict Safety Rule: Enforces battery >= 20.0% and motor temp < 65°C safety gates.
Clearly flags workforce and physical inventory as NOT AVAILABLE (Simulation Mode).
Never automatically dispatches; all missions require human operator approval.
"""
from typing import Dict, Any, List, Optional
import math
from sqlalchemy.orm import Session

from app.models.rover import RoverModel
from app.models.pipeline_segment import PipelineSegmentModel
from app.services.operational_intelligence.incident_correlation_service import IncidentCorrelationService


class OperationalResourcePlanningService:
    MIN_BATTERY_PCT = 20.0
    MAX_MOTOR_TEMP_C = 65.0

    @classmethod
    def evaluate_resources_for_target(
        cls,
        db: Session,
        pipeline_segment_id: str,
        segment_name: str,
        target_lat: float = 40.7128,
        target_lng: float = -74.0060,
        estimated_segment_length_m: float = 500.0,
    ) -> Dict[str, Any]:
        """
        Evaluates the virtual rover fleet for dispatch suitability to the target segment.
        """
        rovers = db.query(RoverModel).all()
        suitability_list = []
        eligible_rovers = []

        for r in rovers:
            rover_id = str(r.id)
            battery = float(r.battery_percentage)
            temp = float(r.motor_temp_c)
            state = str(r.operating_state).upper()
            status = str(r.status).upper()

            # Geodesic distance from rover current station/location to target
            dist_m = IncidentCorrelationService.haversine_distance(
                float(r.latitude), float(r.longitude), target_lat, target_lng
            )

            is_eligible = True
            rejection_reasons = []

            # 1. Hard Safety Gate: Battery Check
            if battery < cls.MIN_BATTERY_PCT:
                is_eligible = False
                rejection_reasons.append(f"BATTERY_INSUFFICIENT: Current charge {battery:.1f}% is below safety limit ({cls.MIN_BATTERY_PCT}%)")

            # 2. Hard Safety Gate: Motor Temperature
            if temp >= cls.MAX_MOTOR_TEMP_C:
                is_eligible = False
                rejection_reasons.append(f"MOTOR_OVERHEATED: Motor temperature {temp:.1f}°C exceeds threshold ({cls.MAX_MOTOR_TEMP_C}°C)")

            # 3. Operational State Check
            if state in ["BUSY", "IN_MISSION", "MAINTENANCE", "OFFLINE"]:
                is_eligible = False
                rejection_reasons.append(f"ROVER_UNAVAILABLE: Operating state is {state}")

            # 4. Suitability Score Calculation (0.0 to 100.0)
            if is_eligible:
                # Proximity factor: 100 at 0m, 0 at 5000m
                dist_factor = max(0.0, 100.0 - (dist_m / 50.0))
                # Thermal margin: 100 at 25°C, 0 at 65°C
                thermal_factor = max(0.0, (cls.MAX_MOTOR_TEMP_C - temp) / (cls.MAX_MOTOR_TEMP_C - 20.0) * 100.0)
                
                score = round(
                    0.40 * battery +
                    0.35 * dist_factor +
                    0.15 * thermal_factor +
                    0.10 * 100.0,  # Readiness baseline
                    1
                )
                eligible_rovers.append((score, r))
            else:
                score = round(max(0.0, 0.20 * battery), 1)

            suitability_list.append({
                "rover_id": rover_id,
                "rover_name": str(r.name),
                "status": status,
                "operating_state": state,
                "battery_percentage": round(battery, 1),
                "motor_temp_c": round(temp, 1),
                "distance_to_target_m": round(dist_m, 1),
                "suitability_score": score,
                "is_eligible": is_eligible,
                "rejection_reasons": rejection_reasons,
            })

        # Sort rovers by suitability score descending
        suitability_list.sort(key=lambda x: x["suitability_score"], reverse=True)

        best_rover_id = None
        best_rover_name = None
        if eligible_rovers:
            eligible_rovers.sort(key=lambda x: x[0], reverse=True)
            best_r = eligible_rovers[0][1]
            best_rover_id = str(best_r.id)
            best_rover_name = str(best_r.name)
            dispatch_feasibility = "READY_FOR_DISPATCH"
        else:
            if any(r["battery_percentage"] < cls.MIN_BATTERY_PCT for r in suitability_list):
                dispatch_feasibility = "LOW_BATTERY_WARNING"
            else:
                dispatch_feasibility = "NO_ROVER_AVAILABLE"

        # Estimated inspection requirements
        est_distance = round(estimated_segment_length_m, 1)
        est_energy = round(est_distance * 0.008, 1)  # ~0.8% battery per 100m
        est_duration = round(est_distance / 0.5 / 60.0, 1)  # Crawl speed 0.5 m/s

        return {
            "recommendation_id": f"REC-RES-{pipeline_segment_id}",
            "pipeline_segment_id": pipeline_segment_id,
            "segment_name": segment_name,
            "required_capability": "Subterranean acoustic crawling inspection & pressure mapping",
            "estimated_distance_m": est_distance,
            "estimated_energy_pct": est_energy,
            "estimated_duration_min": est_duration,
            "suitable_rovers": suitability_list,
            "best_rover_id": best_rover_id,
            "best_rover_name": best_rover_name,
            "dispatch_feasibility": dispatch_feasibility,
            "workforce_status": "NOT_AVAILABLE (Software Simulation Mode)",
            "inventory_status": "NOT_AVAILABLE (Software Simulation Mode)",
            "approval_required": True,
            "human_in_the_loop_mandatory": True,
        }

