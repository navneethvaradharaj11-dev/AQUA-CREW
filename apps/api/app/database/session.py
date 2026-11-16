"""
SQLAlchemy 2.x Database Session and Connection Management
Supports SQLite for development & testing, and PostgreSQL + PostGIS for production.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
import os

from app.config import settings

# Engine configuration
connect_args = {}
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Production-grade PostgreSQL pooling configuration
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a thread-local database session.
    Automatically handles commit/rollback and closes on request completion.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_context() -> Session:
    """
    Helper to acquire a standalone database session that respects FastAPI test overrides if active.
    Caller is responsible for calling db.close().
    """
    try:
        from app.main import app
        override = app.dependency_overrides.get(get_db)
        if override:
            gen = override()
            return next(gen)
    except Exception:
        pass
    return SessionLocal()


def init_db() -> None:
    """
    Initializes database schema.
    Creates all registered tables if they do not exist.
    """
    from app.models import (
        RoverModel,
        MissionModel,
        TelemetryRecordModel,
        StateTransitionModel,
        AuditEventModel,
        PipelineSegmentModel,
        SimulationSessionModel,
        SensorReadingModel,
        AiDetectionModel,
        MissionRecommendationModel,
        PipelineHealthModel,
        PredictiveRiskModel,
        HistoricalTrendModel,
        MaintenanceRecommendationModel,
        HydraulicNetworkModel,
        HydraulicNodeModel,
        HydraulicLinkModel,
        SimulationScenarioModel,
        SimulationRunModel,
        ScenarioComparisonModel,
        PipelineVulnerabilityProfileModel,
        InfrastructureRiskAssessmentModel,
        SpatialIncidentClusterModel,
        GeographicRiskZoneModel,
        InspectionPriorityRecordModel,
        InfrastructureIntelligenceSnapshotModel,
        OperationalAssessmentModel,
        OperationalRecommendationModel,
        OperationalDecisionModel,
        OperationalPriorityModel,
        OperationalImpactAssessmentModel,
        OperationalEvidenceReferenceModel,
        OperationalExecutionRecordModel,
        OperationalPerformanceSnapshotModel,
        AIConversationModel,
        AIMessageModel,
        AIResponseEvidenceModel,
        AIInteractionAuditModel,
        UserModel,
        TokenRevocationModel,
        SecurityAuditEventModel,
        OptimizationJobModel,
        OptimizationCandidateModel,
        OptimizationAuditEventModel,
        InspectionRecommendationModel,
        InspectionPlanModel,
        InspectionExecutionModel,
        InspectionReportModel,
        InspectionEventModel,
        RepairAssessmentModel,
        RepairRecommendationModel,
        RepairPlanModel,
        RepairResourceModel,
        RepairCostEstimateModel,
        RepairCrewModel,
        RepairScheduleModel,
        RepairWorkflowEventModel,
        RepairVerificationModel,
        IoTDeviceModel,
        DeviceCredentialMetadataModel,
        SensorModel,
        SensorCalibrationModel,
        DeviceTelemetryModel,
        DeviceEventModel,
        DeviceConnectionModel,
        DeviceAuditLogModel,
        TelemetryProcessingResultModel,
        UnifiedIncidentModel,
        IncidentWorkflowEventModel,
        IncidentApprovalModel,
    )
    Base.metadata.create_all(bind=engine)

