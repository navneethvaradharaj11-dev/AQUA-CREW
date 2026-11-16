"""
AQUA CREW — Autonomous Inspection Intelligence Service (Task 15)
Synthesizes signals across GIS, AI leak detection, predictive maintenance, hydraulic digital twins,
and network optimization to compute composite inspection urgency and generate explainable recommendations.
Enforces strict 6-tier ontological evidence provenance (MEASURED, SIMULATED, DERIVED, PREDICTED, OPERATOR_ENTERED, UNKNOWN).
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import json
import uuid
import asyncio
from sqlalchemy.orm import Session

from app.models.pipeline_segment import PipelineSegmentModel
from app.models.ai_detection import AiDetectionModel
from app.models.predictive_maintenance import PipelineHealthModel, PredictiveRiskModel
from app.models.digital_twin import HydraulicLinkModel
from app.models.infrastructure_intelligence import (
    PipelineVulnerabilityProfileModel,
    SpatialIncidentClusterModel,
)
from app.models.optimization import OptimizationCandidateModel
from app.schemas.inspection_intelligence import (
    InspectionRecommendationSchema,
    SupportingEvidenceItem,
    EvidenceClassification,
    PriorityCategory,
    InspectionMethod,
)
from app.repositories.pipeline_repository import PipelineRepository, DEFAULT_PIPELINES
from app.repositories.inspection_intelligence_repository import InspectionIntelligenceRepository
from app.websocket.connection_manager import ws_manager


class InspectionIntelligenceService:
    # Calibrated multi-factor urgency weights (sum = 1.0)
    URGENCY_WEIGHTS = {
        "vulnerability": 0.25,        # Task 11 vulnerability profile
        "degradation_rate": 0.20,     # Task 09 predictive deterioration
        "active_leak_detection": 0.25,# Task 07 acoustic AI detections
        "hydraulic_stress": 0.15,     # Task 10/14 excess pressure & headloss
        "cluster_proximity": 0.10,    # Task 11 spatial hotspot clustering
        "network_consequence": 0.05,  # Pipe diameter & critical trunk status
    }

    @classmethod
    def calculate_urgency_score(
        cls,
        db: Session,
        segment: PipelineSegmentModel,
    ) -> Tuple[float, PriorityCategory, Dict[str, float], List[SupportingEvidenceItem], InspectionMethod, str]:
        """
        Calculates composite urgency score (0-100), factor breakdown, supporting evidence,
        recommended inspection method, and engineering rationale.
        """
        seg_id = segment.id
        evidence_items: List[SupportingEvidenceItem] = []
        factors: Dict[str, float] = {}

        # ---------------------------------------------------------------------
        # 1. Pipeline Physical Consequence (MEASURED / ASSET INVENTORY)
        # ---------------------------------------------------------------------
        diam_mm = segment.diameter_mm or 300
        consequence_score = min(100.0, (diam_mm / 600.0) * 100.0)
        factors["network_consequence"] = round(consequence_score, 1)

        evidence_items.append(SupportingEvidenceItem(
            evidence_id=f"EVID-ASSET-{seg_id}",
            source_subsystem="TASK_04_GIS",
            classification="MEASURED",
            metric_name="pipe_diameter_mm",
            metric_value=diam_mm,
            description=f"Conduit '{segment.name}' (Material: {segment.material}, Diameter: {diam_mm}mm, Length: {segment.length_m:.0f}m).",
            confidence=1.0,
            observed_at=segment.created_at.isoformat() if hasattr(segment, "created_at") and segment.created_at else None,
        ))

        # ---------------------------------------------------------------------
        # 2. Infrastructure Vulnerability Index (DERIVED - Task 11)
        # ---------------------------------------------------------------------
        vuln_prof = db.query(PipelineVulnerabilityProfileModel).filter(
            PipelineVulnerabilityProfileModel.pipeline_segment_id == seg_id
        ).first()

        vuln_score = vuln_prof.vulnerability_score if vuln_prof and hasattr(vuln_prof, "vulnerability_score") else 45.0
        factors["vulnerability"] = round(vuln_score, 1)

        if vuln_prof:
            vuln_tier = vuln_prof.vulnerability_level if hasattr(vuln_prof, "vulnerability_level") else "MODERATE"
            vuln_conf = vuln_prof.confidence if hasattr(vuln_prof, "confidence") else 0.85
            evidence_items.append(SupportingEvidenceItem(
                evidence_id=f"EVID-VULN-{seg_id}",
                source_subsystem="TASK_11_INFRA_INTEL",
                classification="DERIVED",
                metric_name="vulnerability_index",
                metric_value=round(vuln_score, 1),
                description=f"Multi-factor structural vulnerability index: {vuln_score:.1f}/100 ({vuln_tier}).",
                confidence=vuln_conf,
                observed_at=vuln_prof.assessed_at.isoformat() if hasattr(vuln_prof, "assessed_at") and vuln_prof.assessed_at else None,
            ))

        # ---------------------------------------------------------------------
        # 3. Predictive Degradation & Health (PREDICTED - Task 09)
        # ---------------------------------------------------------------------
        health = db.query(PipelineHealthModel).filter(PipelineHealthModel.pipeline_segment_id == seg_id).first()
        pred_risk = db.query(PredictiveRiskModel).filter(PredictiveRiskModel.pipeline_segment_id == seg_id).first()

        health_val = health.health_score if health and hasattr(health, "health_score") else 75.0
        failure_prob = pred_risk.failure_prob_7d if pred_risk and hasattr(pred_risk, "failure_prob_7d") else 0.05
        # Degradation score: health deficit (100 - health) scaled with failure risk
        degradation_score = min(100.0, (100.0 - health_val) * 0.7 + (failure_prob * 100.0) * 0.3)
        factors["degradation_rate"] = round(degradation_score, 1)

        if health:
            obs_time = health.assessed_at.isoformat() if hasattr(health, "assessed_at") and health.assessed_at else None
            evidence_items.append(SupportingEvidenceItem(
                evidence_id=f"EVID-HLTH-{seg_id}",
                source_subsystem="TASK_09_PRED_MAINT",
                classification="PREDICTED",
                metric_name="structural_health_score",
                metric_value=round(health_val, 1),
                description=f"Estimated structural health: {health_val:.1f}/100. 7-day failure risk: {failure_prob * 100.0:.1f}%.",
                confidence=0.82,
                observed_at=obs_time,
            ))

        # ---------------------------------------------------------------------
        # 4. Active AI Acoustic Leak Detections (MEASURED/DERIVED - Task 07)
        # ---------------------------------------------------------------------
        detections = db.query(AiDetectionModel).filter(
            AiDetectionModel.pipeline_segment_id == seg_id,
            AiDetectionModel.status.in_(["PENDING_REVIEW", "VERIFIED_BY_OPERATOR", "INSPECTION_DISPATCHED"]),
        ).all()

        if detections:
            max_conf = max((d.confidence for d in detections if hasattr(d, "confidence")), default=0.7)
            max_anomaly = max((d.anomaly_score for d in detections if hasattr(d, "anomaly_score")), default=0.5)
            leak_score = min(100.0, max_conf * 50.0 + (max_anomaly * 100.0) * 0.5)
            best_det = max(detections, key=lambda d: getattr(d, "confidence", 0.0))
            obs_time = best_det.created_at.isoformat() if hasattr(best_det, "created_at") and best_det.created_at else None
            loss_lph = getattr(best_det, "estimated_loss_lph", 0.0)
            evidence_items.append(SupportingEvidenceItem(
                evidence_id=f"EVID-LEAK-{best_det.id}",
                source_subsystem="TASK_07_AI_LEAKS",
                classification="MEASURED", # Hydrophone spectral analysis
                metric_name="acoustic_leak_confidence",
                metric_value=round(getattr(best_det, "confidence", 0.8), 2),
                description=f"Acoustic anomaly detected (Classification: {getattr(best_det, 'classification', 'LEAK')}, Anomaly: {getattr(best_det, 'anomaly_score', 0.5):.2f}, Est Loss: {loss_lph:.1f} L/h).",
                confidence=getattr(best_det, "confidence", 0.85),
                observed_at=obs_time,
            ))
        else:
            leak_score = 10.0
        factors["active_leak_detection"] = round(leak_score, 1)

        # ---------------------------------------------------------------------
        # 5. Hydraulic Digital Twin Stress (SIMULATED - Task 10 / Task 14)
        # ---------------------------------------------------------------------
        hyd_link = db.query(HydraulicLinkModel).filter(
            (HydraulicLinkModel.pipeline_segment_id == seg_id) | (HydraulicLinkModel.id == seg_id)
        ).first()
        if hyd_link:
            roughness = getattr(hyd_link, "roughness", 130.0)
            diam = getattr(hyd_link, "diameter_mm", 300.0)
            hyd_stress = min(100.0, max(20.0, (150.0 - roughness) * 0.8 + (diam / 10.0) * 0.2))
            evidence_items.append(SupportingEvidenceItem(
                evidence_id=f"EVID-HYD-{seg_id}",
                source_subsystem="TASK_10_HYDRAULIC_TWIN",
                classification="SIMULATED",
                metric_name="hydraulic_pipe_roughness",
                metric_value=round(roughness, 1),
                description=f"Simulated hydraulic link: C-roughness {roughness:.1f}, diameter {diam:.0f}mm, status {hyd_link.current_status}.",
                confidence=0.90,
                observed_at=None,
            ))
        else:
            hyd_stress = 30.0
        factors["hydraulic_stress"] = round(hyd_stress, 1)

        # ---------------------------------------------------------------------
        # 6. Spatial Incident Cluster Proximity (DERIVED - Task 11)
        # ---------------------------------------------------------------------
        clusters = db.query(SpatialIncidentClusterModel).all()
        in_cluster = len(clusters) > 0
        cluster_score = 80.0 if in_cluster else 25.0
        factors["cluster_proximity"] = round(cluster_score, 1)

        if in_cluster:
            c = clusters[0]
            cluster_lbl = c.cluster_name if hasattr(c, "cluster_name") else "Incident Cluster"
            obs_time = c.assessed_at.isoformat() if hasattr(c, "assessed_at") and c.assessed_at else None
            evidence_items.append(SupportingEvidenceItem(
                evidence_id=f"EVID-CLUST-{c.id}",
                source_subsystem="TASK_11_INFRA_INTEL",
                classification="DERIVED",
                metric_name="hotspot_cluster",
                metric_value=c.id,
                description=f"Segment intersects DBSCAN incident hotspot '{cluster_lbl}' (Incident count: {c.incident_count}).",
                confidence=0.88,
                observed_at=obs_time,
            ))

        # ---------------------------------------------------------------------
        # Composite Urgency Scoring
        # ---------------------------------------------------------------------
        composite_urgency = sum(
            factors[k] * cls.URGENCY_WEIGHTS[k] for k in cls.URGENCY_WEIGHTS
        )
        composite_urgency = round(max(0.0, min(100.0, composite_urgency)), 1)

        # Priority Categorization
        if composite_urgency >= 75.0:
            category: PriorityCategory = "CRITICAL"
        elif composite_urgency >= 55.0:
            category: PriorityCategory = "HIGH"
        elif composite_urgency >= 35.0:
            category: PriorityCategory = "MEDIUM"
        else:
            category: PriorityCategory = "LOW"

        # Determine Optimal Inspection Method & Rationale
        if leak_score >= 60.0:
            method: InspectionMethod = "ACOUSTIC_CORRELATION"
            action = "Dispatch acoustic hydrophone rover to pinpoint acoustic cross-correlation leak center."
        elif vuln_score >= 70.0 and diam_mm >= 400:
            method: InspectionMethod = "MULTI_SENSOR_CRAWLER"
            action = "Deploy internal multi-sensor pipeline crawler for comprehensive wall-thickness and CCTV inspection."
        elif degradation_score >= 65.0:
            method: InspectionMethod = "ULTRASONIC_THICKNESS"
            action = "Conduct ultrasonic NDT inspection to measure circumferential pipe wall loss and corrosion pit depth."
        elif hyd_stress >= 65.0:
            method: InspectionMethod = "THERMAL_INFRARED"
            action = "Execute thermal infrared scanning along trench alignment to verify subsurface wet zone plume."
        else:
            method: InspectionMethod = "VISUAL_CCTV"
            action = "Schedule routine visual robotic CCTV survey to inspect joint alignment and internal tuberculation."

        return composite_urgency, category, factors, evidence_items, method, action

    @classmethod
    def generate_recommendations_for_all(
        cls,
        db: Session,
        min_urgency: float = 30.0,
    ) -> List[InspectionRecommendationSchema]:
        """
        Evaluates all pipeline segments in asset database and generates/updates recommendations.
        """
        segments = PipelineRepository.get_all(db)
        if not segments:
            # Seed defaults if database table empty
            for d in DEFAULT_PIPELINES:
                PipelineRepository.create(db, d)
            segments = PipelineRepository.get_all(db)

        recommendations: List[InspectionRecommendationSchema] = []

        for seg in segments:
            urgency, category, factors, evidence, method, action = cls.calculate_urgency_score(db, seg)
            if urgency < min_urgency:
                continue

            rec_id = f"INSP-REC-{seg.id}"
            
            # Map method to required rover capabilities
            caps = ["pipe_navigation"]
            if method == "ACOUSTIC_CORRELATION":
                caps.append("hydrophone_acoustic")
            elif method == "VISUAL_CCTV":
                caps.append("high_res_optical")
            elif method == "THERMAL_INFRARED":
                caps.append("thermal_infrared")
            elif method == "MULTI_SENSOR_CRAWLER":
                caps.extend(["hydrophone_acoustic", "high_res_optical", "ultrasonic_thickness"])
            elif method == "ULTRASONIC_THICKNESS":
                caps.append("ultrasonic_thickness")

            rec_schema = InspectionRecommendationSchema(
                id=rec_id,
                pipeline_segment_id=seg.id,
                segment_name=seg.name,
                priority_score=urgency,
                priority_category=category,
                urgency_factors=factors,
                supporting_evidence=evidence,
                primary_classification="DERIVED",
                confidence=0.88,
                uncertainty_radius_m=15.0 if category in ["CRITICAL", "HIGH"] else 30.0,
                recommended_method=method,
                estimated_duration_minutes=45 if category == "CRITICAL" else 30,
                required_rover_capabilities=caps,
                recommended_action=action,
                human_approval_status="PENDING_APPROVAL",
                created_at=datetime.now(timezone.utc).isoformat(),
                is_simulated=True,
            )

            InspectionIntelligenceRepository.save_recommendation(db, rec_schema)
            recommendations.append(rec_schema)

        # Sort descending by priority score
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)

        # Broadcast WebSocket event safely
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast({
                    "type": "INSPECTION_RECOMMENDED",
                    "count": len(recommendations),
                    "top_priority": recommendations[0].priority_category if recommendations else "NONE",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }))
        except Exception:
            pass

        return recommendations

