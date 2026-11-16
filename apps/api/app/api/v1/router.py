"""
API Version 1 Router Aggregator
Mounts endpoints for Health, Rovers, Missions, Telemetry, Simulation, Events, and WebSocket.
"""
from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.rovers import router as rovers_router
from app.api.v1.endpoints.missions import router as missions_router
from app.api.v1.endpoints.telemetry import router as telemetry_router
from app.api.v1.endpoints.simulation import router as simulation_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.ws import router as ws_router
from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.dispatch import router as dispatch_router
from app.api.v1.endpoints.maintenance import router as maintenance_router
from app.api.v1.endpoints.digital_twin import router as digital_twin_router
from app.api.v1.endpoints.infrastructure_intelligence import router as infrastructure_intelligence_router
from app.api.v1.endpoints.operational_intelligence import router as operational_intelligence_router
from app.api.v1.endpoints.advanced_ai import router as advanced_ai_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.optimization import router as optimization_router
from app.api.v1.endpoints.inspection_intelligence import router as inspection_intelligence_router
from app.api.v1.endpoints.repair_management import router as repair_management_router
from app.api.v1.endpoints.metrics import router as metrics_router
from app.api.v1.endpoints.iot import router as iot_router
from app.api.v1.endpoints.incidents import router as incidents_router

api_v1_router = APIRouter()

# Mount endpoints
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Identity & Access Management"])
api_v1_router.include_router(health_router, tags=["Health & System"])
api_v1_router.include_router(metrics_router, tags=["Metrics & Observability"])
api_v1_router.include_router(rovers_router, prefix="/rovers", tags=["Rovers & Commands"])
api_v1_router.include_router(missions_router, prefix="/missions", tags=["Missions"])
api_v1_router.include_router(dispatch_router, prefix="/dispatch", tags=["Dispatch & Fleet Suitability"])
api_v1_router.include_router(telemetry_router, prefix="/telemetry", tags=["Telemetry"])
api_v1_router.include_router(simulation_router, prefix="/simulation", tags=["Simulation Controls"])
api_v1_router.include_router(events_router, prefix="/events", tags=["Audit & Events"])
api_v1_router.include_router(ws_router, prefix="/ws", tags=["Real-Time WebSocket"])
api_v1_router.include_router(ai_router, prefix="/ai", tags=["AI Leak Detection & Acoustic Intelligence"])
api_v1_router.include_router(maintenance_router, prefix="/maintenance", tags=["Predictive Maintenance & Health Intelligence"])
api_v1_router.include_router(digital_twin_router, prefix="/digital-twin", tags=["Digital Twin & Hydraulic Simulation"])
api_v1_router.include_router(infrastructure_intelligence_router, prefix="/infrastructure-intelligence", tags=["Infrastructure Intelligence & Geospatial Risk Prediction"])
api_v1_router.include_router(operational_intelligence_router, prefix="/operational-intelligence", tags=["Unified Operational Intelligence & Decision Support"])
api_v1_router.include_router(advanced_ai_router, prefix="/advanced-ai", tags=["Advanced AI & Evidence-Grounded Decision Intelligence"])
api_v1_router.include_router(optimization_router, prefix="/optimization", tags=["Intelligent Water Network Optimization & Hydraulic Decision Engine"])
api_v1_router.include_router(inspection_intelligence_router, prefix="/inspection-intelligence", tags=["Autonomous Inspection Intelligence & Adaptive Rover Fleet Orchestration"])
api_v1_router.include_router(repair_management_router, prefix="/repair-management", tags=["Intelligent Repair Planning & Management System"])
api_v1_router.include_router(iot_router, prefix="/iot", tags=["IoT & Hardware Gateway"])
api_v1_router.include_router(incidents_router, prefix="/incidents", tags=["Unified Incident Intelligence & Lifecycle Orchestration"])
