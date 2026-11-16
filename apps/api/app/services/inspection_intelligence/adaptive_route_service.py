"""
AQUA CREW — Intelligent Inspection Route Planning Service (Task 15)
Builds upon GIS topological graph and Dijkstra engine to generate multi-target inspection routes
following actual connected underground pipe geometry with return-to-base battery validation.
"""
from typing import Dict, Any, List, Optional, Tuple
import json
from sqlalchemy.orm import Session

from app.models.rover import RoverModel
from app.models.pipeline_segment import PipelineSegmentModel
from app.schemas.inspection_intelligence import (
    MultiRoverAllocationItemSchema,
    InspectionPlanTargetSchema,
)
from app.repositories.pipeline_repository import PipelineRepository
from app.services.pipeline_routing_service import (
    PipelineRoutingService,
    haversine_distance_m,
    coord_to_key,
)


class AdaptiveRouteService:
    BATTERY_PCT_PER_KM = 1.8
    INSPECT_PCT_PER_HR = 4.0

    @classmethod
    def plan_multi_target_route(
        cls,
        db: Session,
        rover: RoverModel,
        targets: List[InspectionPlanTargetSchema],
        safety_reserve_pct: float = 20.0,
    ) -> MultiRoverAllocationItemSchema:
        """
        Computes complete connected route visiting assigned targets in priority sequence
        and returning to initial rover station coordinates.
        """
        all_pipelines = PipelineRepository.get_all(db)
        base_coord = [rover.longitude, rover.latitude]

        if not targets:
            return MultiRoverAllocationItemSchema(
                rover_id=rover.id,
                rover_name=rover.name,
                assigned_targets=[],
                route_waypoints=[base_coord],
                segments_traversed=[],
                total_route_distance_m=0.0,
                estimated_mission_duration_s=0.0,
                estimated_battery_drain_pct=0.0,
                projected_reserve_after_return_pct=rover.battery_percentage,
                return_to_base_feasible=True,
                route_selection_reason="No targets assigned to rover.",
            )

        # Build complete waypoint trajectory across all legs:
        # Rover Base -> Target 1 -> Target 2 -> ... -> Rover Base
        full_waypoints: List[List[float]] = []
        all_segments: List[str] = []
        total_dist_m = 0.0
        total_travel_time_s = 0.0
        total_inspect_time_s = 0.0

        current_pos = base_coord

        for idx, target in enumerate(targets):
            t_coord = target.target_coordinates
            leg_route = PipelineRoutingService.calculate_route(
                start_coord=current_pos,
                target_coord=t_coord,
                pipeline_records=all_pipelines,
                target_segment_id=target.pipeline_segment_id,
                rover_speed_mps=rover.velocity_mps or 0.55,
            )

            # Append waypoints (avoid duplicate intermediate junction point)
            if leg_route.waypoints:
                if full_waypoints and leg_route.waypoints:
                    full_waypoints.extend(leg_route.waypoints[1:])
                else:
                    full_waypoints.extend(leg_route.waypoints)
            else:
                full_waypoints.append(t_coord)

            for seg_id in leg_route.segments_traversed:
                if seg_id not in all_segments:
                    all_segments.append(seg_id)

            total_dist_m += leg_route.total_distance_m
            total_travel_time_s += leg_route.estimated_travel_time_s
            total_inspect_time_s += (target.estimated_duration_minutes * 60.0)

            current_pos = t_coord

        # Return-to-base leg
        return_route = PipelineRoutingService.calculate_route(
            start_coord=current_pos,
            target_coord=base_coord,
            pipeline_records=all_pipelines,
            rover_speed_mps=rover.velocity_mps or 0.55,
        )

        if return_route.waypoints:
            if full_waypoints:
                full_waypoints.extend(return_route.waypoints[1:])
            else:
                full_waypoints.extend(return_route.waypoints)
        else:
            full_waypoints.append(base_coord)

        for seg_id in return_route.segments_traversed:
            if seg_id not in all_segments:
                all_segments.append(seg_id)

        total_dist_m += return_route.total_distance_m
        total_travel_time_s += return_route.estimated_travel_time_s

        total_mission_s = total_travel_time_s + total_inspect_time_s

        # Battery consumption calculation
        travel_km = total_dist_m / 1000.0
        travel_drain = travel_km * cls.BATTERY_PCT_PER_KM
        inspect_hours = total_inspect_time_s / 3600.0
        inspect_drain = inspect_hours * cls.INSPECT_PCT_PER_HR
        total_drain = round(travel_drain + inspect_drain, 1)

        projected_reserve = round(rover.battery_percentage - total_drain, 1)
        return_feasible = projected_reserve >= safety_reserve_pct

        target_names = ", ".join(t.pipeline_segment_id for t in targets)
        reason = (
            f"Optimized shortest connected pipeline path visiting [{target_names}] "
            f"covering {total_dist_m:.0f}m across {len(all_segments)} underground pipe segments "
            f"with safe return-to-base reserve of {projected_reserve:.1f}% (Required: {safety_reserve_pct:.1f}%)."
        )

        return MultiRoverAllocationItemSchema(
            rover_id=rover.id,
            rover_name=rover.name,
            assigned_targets=targets,
            route_waypoints=full_waypoints,
            segments_traversed=all_segments,
            total_route_distance_m=round(total_dist_m, 1),
            estimated_mission_duration_s=round(total_mission_s, 1),
            estimated_battery_drain_pct=total_drain,
            projected_reserve_after_return_pct=projected_reserve,
            return_to_base_feasible=return_feasible,
            route_selection_reason=reason,
        )

    @classmethod
    def check_reachability(
        cls,
        db: Session,
        target_coordinates: List[float],
        all_pipelines: List[Any],
        tolerance_m: float = 300.0,
    ) -> bool:
        """
        Validates whether target coordinate snaps to connected pipeline topology within tolerance.
        """
        adj, nodes = PipelineRoutingService.build_network_graph(all_pipelines)
        if not nodes:
            return False

        nearest_key, dist = PipelineRoutingService.find_nearest_node(target_coordinates, nodes)
        return nearest_key is not None and dist <= tolerance_m

