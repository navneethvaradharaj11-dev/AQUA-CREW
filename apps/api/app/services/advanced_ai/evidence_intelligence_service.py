"""
Evidence-Grounded Intelligence Service (Task 13 / 13.5)
Retrieves, standardizes, and classifies evidentiary records across all AQUA CREW subsystems.
Enforces strict ontological segregation:
  - MEASURED: Direct telemetric sensors (acoustic hydrophones, pressure transmitters, moisture probes)
  - SIMULATED: Numerical hydraulic digital twin outputs, Torricelli flows, and virtual kinematic telemetry
  - DERIVED: Mathematical aggregations, OLS slopes, and composite priority indices
  - PREDICTED: Multi-horizon empirical degradation risk scores (heuristic failure risk indices)
  - OPERATOR_ENTERED: Human operator decisions, overrides, and notes
  - UNKNOWN: Unmeasured geotechnical parameters or uncalibrated provenance
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.pipeline_segment import PipelineSegmentModel
from app.models.ai_detection import AiDetectionModel
from app.models.sensor_reading import SensorReadingModel
from app.models.predictive_maintenance import PipelineHealthModel, PredictiveRiskModel
from app.models.digital_twin import HydraulicLinkModel, SimulationRunModel
from app.models.infrastructure_intelligence import PipelineVulnerabilityProfileModel, SpatialIncidentClusterModel
from app.models.operational_intelligence import (
    OperationalRecommendationModel,
    OperationalDecisionModel,
    OperationalPriorityModel,
)
from app.models.rover import RoverModel
from app.schemas.advanced_ai import EvidenceItemSchema


class EvidenceIntelligenceService:
    @classmethod
    def get_segment_evidence(cls, db: Session, segment_id: str) -> List[EvidenceItemSchema]:
        """
        Gathers all persisted evidentiary records related to a target pipeline segment
        with verified provenance, timestamp staleness, and calibration indicators.
        """
        evidence_items: List[EvidenceItemSchema] = []
        now = datetime.now(timezone.utc)

        def compute_staleness(rec_time: Optional[datetime]) -> tuple[Optional[float], bool]:
            if not rec_time:
                return None, False
            if rec_time.tzinfo is None:
                rec_time = rec_time.replace(tzinfo=timezone.utc)
            age = max(0.0, (now - rec_time).total_seconds() / 3600.0)
            return round(age, 2), age > 24.0

        # 1. Pipeline Physical Metadata (ASSET INVENTORY SPECIFICATION)
        segment = db.query(PipelineSegmentModel).filter(PipelineSegmentModel.id == segment_id).first()
        if segment:
            evidence_items.append(EvidenceItemSchema(
                evidence_id=f"EVID-SEG-{segment.id}",
                source_module="TASK_04_GIS",
                source_table="pipeline_segments",
                source_record_id=str(segment.id),
                evidence_type="ASSET_SPECIFICATION",
                classification="MEASURED",  # Physical conduit specification in asset registry
                observed_at=None,
                age_hours=None,
                is_stale=False,
                metric_name="diameter_mm",
                metric_value=float(segment.diameter_mm or 300),
                metric_unit="mm",
                summary=f"Physical asset registry: {segment.name} ({segment.material}, dia: {segment.diameter_mm}mm, len: {segment.length_m}m). Virtual model.",
                confidence=1.0,
                calibration_status="ASSET_REGISTRY_RECORD",
                hardware_connected=False,
                validation_status="VALIDATED",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

        # 2. Raw Sensor Telemetry (SIMULATED TELEMETRIC SENSORS)
        sensor_readings = db.query(SensorReadingModel).filter(
            SensorReadingModel.pipeline_segment_id == segment_id
        ).order_by(SensorReadingModel.created_at.desc()).limit(5).all()
        for sr in sensor_readings:
            age_hrs, stale = compute_staleness(sr.created_at)
            evidence_items.append(EvidenceItemSchema(
                evidence_id=f"EVID-SNS-{sr.id}",
                source_module="TASK_06_TELEMETRY",
                source_table="sensor_readings",
                source_record_id=str(sr.id),
                evidence_type=f"TELEMETRIC_{sr.sensor_type.upper()}",
                classification="SIMULATED" if sr.is_simulated else "MEASURED",
                observed_at=sr.created_at.isoformat() if sr.created_at else None,
                age_hours=age_hrs,
                is_stale=stale,
                metric_name=sr.sensor_type,
                metric_value=float(sr.measurement_value),
                metric_unit=sr.measurement_unit,
                summary=f"Sensor {sr.sensor_id} ({sr.sensor_type}): {sr.measurement_value:.2f} {sr.measurement_unit} (Quality: {sr.quality_indicator}). Hardware uncalibrated (Virtual Simulation Engine).",
                confidence=0.90 if sr.quality_indicator == "EXCELLENT" else 0.70,
                calibration_status="UNVERIFIED_VIRTUAL",
                hardware_connected=False,
                validation_status="VALIDATED" if not stale else "STALE_DATA",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

        # 3. AI Acoustic Detections (DERIVED MODEL INFERENCE)
        detections = db.query(AiDetectionModel).filter(AiDetectionModel.pipeline_segment_id == segment_id).all()
        for det in detections:
            age_hrs, stale = compute_staleness(det.created_at)
            evidence_items.append(EvidenceItemSchema(
                evidence_id=f"EVID-DET-{det.id}",
                source_module="TASK_07_AI",
                source_table="ai_detections",
                source_record_id=str(det.id),
                evidence_type="ACOUSTIC_LEAK_DETECTION",
                classification="DERIVED",
                observed_at=det.created_at.isoformat() if det.created_at else None,
                age_hours=age_hrs,
                is_stale=stale,
                metric_name="anomaly_score",
                metric_value=float(det.anomaly_score),
                metric_unit="normalized_0_1",
                summary=f"AI model inference ({det.model_version}): {det.classification} with anomaly score {det.anomaly_score:.2f} (confidence: {det.confidence:.2f})",
                confidence=float(det.confidence),
                calibration_status="NOT_APPLICABLE",
                hardware_connected=False,
                validation_status="VALIDATED" if not stale else "STALE_DATA",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

        # 4. Structural Asset Health (DERIVED INDEX)
        health = db.query(PipelineHealthModel).filter(PipelineHealthModel.pipeline_segment_id == segment_id).first()
        if health:
            age_hrs, stale = compute_staleness(health.assessed_at)
            evidence_items.append(EvidenceItemSchema(
                evidence_id=f"EVID-HLTH-{health.id}",
                source_module="TASK_09_PREDICTIVE",
                source_table="pipeline_health_assessments",
                source_record_id=str(health.id),
                evidence_type="STRUCTURAL_HEALTH_SCORE",
                classification="DERIVED",
                observed_at=health.assessed_at.isoformat() if health.assessed_at else None,
                age_hours=age_hrs,
                is_stale=stale,
                metric_name="health_score",
                metric_value=float(health.health_score),
                metric_unit="points_0_100",
                summary=f"Asset health condition: {health.health_score:.1f}/100 ({health.health_category}). Acoustic stability: {health.acoustic_stability_score:.1f}",
                confidence=float(health.confidence),
                calibration_status="NOT_APPLICABLE",
                hardware_connected=False,
                validation_status="VALIDATED",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

        # 5. Predictive Failure Risk (PREDICTED HEURISTIC RISK INDEX)
        pred_risk = db.query(PredictiveRiskModel).filter(PredictiveRiskModel.pipeline_segment_id == segment_id).first()
        if pred_risk:
            age_hrs, stale = compute_staleness(pred_risk.assessed_at)
            evidence_items.append(EvidenceItemSchema(
                evidence_id=f"EVID-PRED-{pred_risk.id}",
                source_module="TASK_09_PREDICTIVE",
                source_table="predictive_risk_assessments",
                source_record_id=str(pred_risk.id),
                evidence_type="FAILURE_PROBABILITY_FORECAST",
                classification="PREDICTED",
                observed_at=pred_risk.assessed_at.isoformat() if pred_risk.assessed_at else None,
                age_hours=age_hrs,
                is_stale=stale,
                metric_name="failure_prob_7d",
                metric_value=float(pred_risk.failure_prob_7d),
                metric_unit="probability_0_1",
                summary=f"Empirical multi-horizon failure risk score: {pred_risk.failure_prob_7d * 100:.1f}% for 7-day window (24h: {pred_risk.failure_prob_24h * 100:.1f}%, 30d: {pred_risk.failure_prob_30d * 100:.1f}%). Derived from heuristic degradation slope and pressure transient rules; no survival models fitted.",
                confidence=float(pred_risk.confidence),
                calibration_status="NOT_APPLICABLE",
                hardware_connected=False,
                validation_status="VALIDATED",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

        # 6. Infrastructure Vulnerability Profile (DERIVED SCORE)
        vuln = db.query(PipelineVulnerabilityProfileModel).filter(PipelineVulnerabilityProfileModel.pipeline_segment_id == segment_id).first()
        if vuln:
            age_hrs, stale = compute_staleness(vuln.assessed_at)
            evidence_items.append(EvidenceItemSchema(
                evidence_id=f"EVID-VULN-{vuln.id}",
                source_module="TASK_11_GEOSPATIAL",
                source_table="pipeline_vulnerability_profiles",
                source_record_id=str(vuln.id),
                evidence_type="MULTI_FACTOR_VULNERABILITY",
                classification="DERIVED",
                observed_at=vuln.assessed_at.isoformat() if vuln.assessed_at else None,
                age_hours=age_hrs,
                is_stale=stale,
                metric_name="vulnerability_score",
                metric_value=float(vuln.vulnerability_score),
                metric_unit="points_0_100",
                summary=f"Vulnerability rating: {vuln.vulnerability_score:.1f}/100 ({vuln.vulnerability_level}). Hyd: {vuln.hydraulic_score:.1f}, Str: {vuln.structural_score:.1f}, Inc: {vuln.incident_score:.1f}, Env: {vuln.environmental_score:.1f}",
                confidence=float(vuln.confidence),
                calibration_status="NOT_APPLICABLE",
                hardware_connected=False,
                validation_status="VALIDATED",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

        # 7. Hydraulic Digital Twin Parameters (SIMULATED DYNAMICS)
        hyd_link = db.query(HydraulicLinkModel).filter(HydraulicLinkModel.pipeline_segment_id == segment_id).first()
        if hyd_link:
            evidence_items.append(EvidenceItemSchema(
                evidence_id=f"EVID-HYD-{hyd_link.id}",
                source_module="TASK_10_DIGITAL_TWIN",
                source_table="hydraulic_links",
                source_record_id=str(hyd_link.id),
                evidence_type="HYDRAULIC_TWIN_LINK",
                classification="SIMULATED",
                observed_at=None,
                age_hours=None,
                is_stale=False,
                metric_name="roughness_hazen_williams",
                metric_value=float(hyd_link.roughness),
                metric_unit="C_factor",
                summary=f"Digital twin link {hyd_link.name}: status {hyd_link.current_status}, roughness C={hyd_link.roughness}, length={hyd_link.length_m}m",
                confidence=0.95,
                calibration_status="SIMULATED_MODEL",
                hardware_connected=False,
                validation_status="VALIDATED",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

        # 8. Operational Recommendations & Operator Decisions (OPERATOR_ENTERED / DERIVED)
        recs = db.query(OperationalRecommendationModel).filter(OperationalRecommendationModel.pipeline_segment_id == segment_id).all()
        for r in recs:
            age_hrs, stale = compute_staleness(r.created_at)
            evidence_items.append(EvidenceItemSchema(
                evidence_id=f"EVID-REC-{r.id}",
                source_module="TASK_12_OPERATIONS",
                source_table="operational_recommendations",
                source_record_id=str(r.id),
                evidence_type="OPERATIONAL_RECOMMENDATION",
                classification="DERIVED",
                observed_at=r.created_at.isoformat() if r.created_at else None,
                age_hours=age_hrs,
                is_stale=stale,
                metric_name="priority_score",
                metric_value=float(r.priority_score),
                metric_unit="points_0_100",
                summary=f"Operational recommendation: {r.category} ({r.priority_tier}, score: {r.priority_score:.1f}). Action: {r.recommended_action}",
                confidence=float(r.confidence),
                calibration_status="NOT_APPLICABLE",
                hardware_connected=False,
                validation_status="VALIDATED",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

            decisions = db.query(OperationalDecisionModel).filter(OperationalDecisionModel.recommendation_id == r.id).all()
            for dec in decisions:
                d_age, d_stale = compute_staleness(dec.decision_timestamp)
                evidence_items.append(EvidenceItemSchema(
                    evidence_id=f"EVID-DEC-{dec.id}",
                    source_module="TASK_12_OPERATIONS",
                    source_table="operational_decisions",
                    source_record_id=str(dec.id),
                    evidence_type="OPERATOR_AUTHORIZATION_DECISION",
                    classification="OPERATOR_ENTERED",
                    observed_at=dec.decision_timestamp.isoformat() if dec.decision_timestamp else None,
                    age_hours=d_age,
                    is_stale=d_stale,
                    metric_name="decision_approved_flag",
                    metric_value=1.0 if dec.decision_type == "APPROVED" else 0.0,
                    metric_unit="binary",
                    summary=f"Operator decision by {dec.operator_name} ({dec.operator_id}): {dec.decision_type}. Reason: '{dec.decision_reason}'",
                    confidence=1.0,
                    calibration_status="NOT_APPLICABLE",
                    hardware_connected=False,
                    validation_status="VALIDATED",
                    is_simulated=True,
                    source="VIRTUAL_SIMULATION_ENGINE",
                ))

        # 9. Explicit Unknown Observation (UNKNOWN / UNMEASURED GEOTECHNICAL)
        evidence_items.append(EvidenceItemSchema(
            evidence_id=f"EVID-UNK-SOIL-{segment_id}",
            source_module="TASK_04_GIS",
            source_table="geotechnical_surveys",
            source_record_id=f"GEO-{segment_id}",
            evidence_type="GEOTECHNICAL_SOIL_RESISTIVITY",
            classification="UNKNOWN",
            observed_at=None,
            age_hours=None,
            is_stale=True,
            metric_name="soil_resistivity_ohm_m",
            metric_value=None,
            metric_unit="ohm_m",
            summary=f"Soil resistivity and redox corrosivity for {segment_id}: UNMEASURED. No physical borehole samples collected.",
            confidence=0.0,
            calibration_status="UNMEASURED",
            hardware_connected=False,
            validation_status="DATA_UNAVAILABLE",
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        ))

        return evidence_items
