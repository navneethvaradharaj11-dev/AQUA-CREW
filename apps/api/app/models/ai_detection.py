"""
SQLAlchemy AI Leak Detection Persistent Model
Stores diagnostic inferences, anomaly scores, risk ratings, and localization estimates.
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from datetime import datetime, timezone

from app.database.session import Base


class AiDetectionModel(Base):
    __tablename__ = "ai_detections"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    
    anomaly_score = Column(Float, nullable=False)  # 0.0 to 1.0
    classification = Column(String(32), nullable=False, index=True)  # NORMAL, LOW_LEAK_PROBABILITY, MEDIUM_LEAK_PROBABILITY, HIGH_LEAK_PROBABILITY
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    risk_level = Column(String(32), nullable=False, index=True)  # LOW, MODERATE, HIGH, CRITICAL
    
    estimated_loss_lph = Column(Float, default=0.0)  # Litres per hour
    estimated_latitude = Column(Float, nullable=True)
    estimated_longitude = Column(Float, nullable=True)
    localization_uncertainty_m = Column(Float, nullable=True)  # Confidence radius in meters
    localization_quality = Column(String(32), default="INSUFFICIENT_DATA")  # HIGH, MODERATE, POOR, INSUFFICIENT_DATA
    
    status = Column(String(32), default="PENDING_REVIEW", index=True)  # PENDING_REVIEW, VERIFIED_BY_OPERATOR, REJECTED, INSPECTION_DISPATCHED
    contributing_features = Column(Text, nullable=True)  # JSON-encoded feature attributions
    risk_explanation = Column(Text, nullable=True)
    model_version = Column(String(64), default="v1.2.0-rf-isoforest", nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)
