"""
SQLAlchemy Models for Predictive Maintenance & Infrastructure Health Intelligence (Task 09)
Persists pipeline health assessments, predictive failure risk estimates,
temporal trend analysis, and explainable maintenance recommendations.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text
from datetime import datetime, timezone
import uuid

from app.database.session import Base


class PipelineHealthModel(Base):
    __tablename__ = "pipeline_health_assessments"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    health_score = Column(Float, nullable=False)  # 0.0 to 100.0
    health_category = Column(String(32), nullable=False, index=True)  # EXCELLENT, GOOD, FAIR, POOR, CRITICAL

    acoustic_stability_score = Column(Float, default=100.0)
    pressure_stability_score = Column(Float, default=100.0)
    flow_stability_score = Column(Float, default=100.0)
    moisture_anomaly_score = Column(Float, default=100.0)
    data_coverage_pct = Column(Float, default=100.0)
    confidence = Column(Float, default=0.90)

    contributing_factors = Column(Text, nullable=True)  # JSON-encoded dictionary
    positive_indicators = Column(Text, nullable=True)   # JSON-encoded list
    explanation = Column(Text, nullable=True)

    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class PredictiveRiskModel(Base):
    __tablename__ = "predictive_risk_assessments"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)

    # Multi-horizon failure probabilities (0.0 to 1.0)
    failure_prob_24h = Column(Float, default=0.01)
    failure_prob_7d = Column(Float, default=0.05)
    failure_prob_30d = Column(Float, default=0.10)

    overall_risk_level = Column(String(32), nullable=False, index=True)  # LOW, MODERATE, HIGH, CRITICAL
    leak_probability = Column(Float, default=0.05)
    burst_rupture_risk = Column(Float, default=0.02)
    model_version = Column(String(64), default="v1.0.0-rf-gradient-predictive", nullable=False)
    confidence = Column(Float, default=0.85)
    uncertainty_margin = Column(Float, default=0.08)

    contributing_factors = Column(Text, nullable=True)  # JSON-encoded dictionary
    risk_explanation = Column(Text, nullable=True)

    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class HistoricalTrendModel(Base):
    __tablename__ = "pipeline_historical_trends"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)

    trend_direction = Column(String(32), nullable=False, index=True)  # IMPROVING, STABLE, DETERIORATING, RAPIDLY_DETERIORATING, INSUFFICIENT_DATA
    health_slope_per_day = Column(Float, default=0.0)  # Change in health index per day
    pressure_variance = Column(Float, default=0.0)
    flow_anomaly_rate = Column(Float, default=0.0)
    acoustic_emission_count = Column(Integer, default=0)
    historical_leak_count = Column(Integer, default=0)
    window_days = Column(Integer, default=30)
    time_series_points_json = Column(Text, nullable=True)  # JSON list of {timestamp, pressure, flow, acoustic_spl, health}

    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class MaintenanceRecommendationModel(Base):
    __tablename__ = "maintenance_recommendations"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)

    health_score = Column(Float, default=75.0)
    predicted_risk = Column(String(32), default="LOW")
    urgency = Column(String(32), default="ROUTINE", index=True)  # ROUTINE, MEDIUM, HIGH, CRITICAL
    recommended_action = Column(String(64), nullable=False, index=True)
    timeframe_days = Column(Integer, default=14)
    status = Column(String(32), default="PENDING_REVIEW", index=True)  # PENDING_REVIEW, ACKNOWLEDGED, DISMISSED, DISPATCHED

    explanation = Column(Text, nullable=True)
    sensor_evidence = Column(Text, nullable=True)  # JSON dictionary of key metrics
    operator_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(128), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    dispatched_mission_id = Column(String(64), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)

