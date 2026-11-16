"""
Pydantic Schemas for Mission Lifecycle & Assignment
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone


class MissionCreateRequest(BaseModel):
    id: str = Field(..., description="Unique Mission Identifier (e.g. MSN-2026-050)")
    mission_type: str = Field(..., description="Mission type name")
    target_segment_id: str = Field(..., description="Pipeline target segment ID")
    waypoint_count: int = Field(default=15, ge=1)
    assigned_rover_id: Optional[str] = None


class MissionAssignRequest(BaseModel):
    rover_id: str = Field(..., description="Rover ID to assign to mission")


class MissionResponse(BaseModel):
    is_simulated: bool = Field(alias="isSimulated", default=True)
    source: str = "VIRTUAL_SIMULATION_ENGINE"
    simulated_at: datetime = Field(alias="simulatedAt")
    id: str
    assigned_rover_id: Optional[str] = Field(alias="assignedRoverId", default="")
    assigned_rover_name: Optional[str] = Field(alias="assignedRoverName", default="")
    mission_type: str = Field(alias="missionType")
    progress_percentage: int = Field(alias="progressPercentage")
    status: str
    start_time: str = Field(alias="startTime")
    estimated_completion_time: str = Field(alias="estimatedCompletionTime")
    target_segment_id: str = Field(alias="targetSegmentId")
    waypoint_count: int = Field(alias="waypointCount")
    completed_waypoints: int = Field(alias="completedWaypoints")

    model_config = {"populate_by_name": True}


class MissionListResponse(BaseModel):
    success: bool = True
    total: int
    missions: List[MissionResponse]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
