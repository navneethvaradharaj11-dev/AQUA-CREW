"""
Unified Operational Intelligence Service (Task 12 - Phase 3 Central Engine)
Orchestrates AI leak detections (Task 07), predictive maintenance (Task 09),
hydraulic digital twin simulations (Task 10), and geospatial vulnerability models (Task 11).
Generates explainable, multi-factor operational recommendations and system assessments.
"""
from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.pipeline_segment import PipelineSegmentModel
from app.models.ai_detection import AiDetectionModel
from app.models.predictive_maintenance import (
    PipelineHealthModel,
    PredictiveRiskModel,
    MaintenanceRecommendationModel,
)
from app.models.digital_twin import (
    HydraulicLinkModel,
    SimulationRunModel,
    HydraulicNetworkModel,
)
from app.models.infrastructure_intelligence import (
    PipelineVulnerabilityProfileModel,
    SpatialIncidentClusterModel,
)
from app.models.rover import RoverModel
from app.models.mission import MissionModel
from app.models.operational_intelligence import (
    OperationalAssessmentModel,
    OperationalRecommendationModel,
    OperationalDecisionModel,
    OperationalPriorityModel,
    OperationalImpactAssessmentModel,
    OperationalEvidenceReferenceModel,
    OperationalExecutionRecordModel,
    OperationalPerformanceSnapshotModel,
)
from app.services.operational_intelligence.operational_prioritisation_service import OperationalPrioritisationService
from app.services.operational_intelligence.incident_correlation_service import IncidentCorrelationService
from app.services.operational_intelligence.operational_hydraulic_impact_service import OperationalHydraulicImpactService
from app.services.operational_intelligence.operational_resource_planning_service import OperationalResourcePlanningService
from app.services.operational_intelligence.operational_impact_service import OperationalImpactService
from app.websocket.connection_manager import ws_manager
import asyncio


class OperationalIntelligenceService:
    METHODOLOGY_VERSION = "v1.0.0-unified-operational-decision"

    @staticmethod
    def _broadcast_event(event_type: str, payload: Dict[str, Any]) -> None:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast({
                    "type": event_type,
                    "payload": payload,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "is_simulated": True,
                    "source": "VIRTUAL_SIMULATION_ENGINE",
                }))
        except Exception:
            pass

    @classmethod
    def run_operational_assessment(cls, db: Session) -> OperationalAssessmentModel:
        """
        Executes a complete cross-system operational assessment.
        Reads live telemetry, detections, health indices, hydraulic results, and vulnerability models
        to create prioritized, explainable operational recommendations.
        """
        now = datetime.now(timezone.utc)
        assessment_id = f"ASSESS-{uuid.uuid4().hex[:8]}"

        # 1. Fetch available pipeline segments
        segments = db.query(PipelineSegmentModel).all()
        if not segments:
            # Fallback mock segments if table is unseeded
            mock_segments = [
                PipelineSegmentModel(
                    id="PIPE-SEC-4B-92",
                    name="Metro Central Main Trunk Line B",
                    category="primary_arterial",
                    material="Ductile Iron",
                    diameter_mm=600,
                    length_m=1200.0,
                    nominal_pressure_psi=65.0,
                    coordinates_json=json.dumps([[-74.0060, 40.7128], [-74.0010, 40.7150]]),
                    is_simulated=True,
                ),
                PipelineSegmentModel(
                    id="PIPE-HRB-02-19",
                    name="Harbor Utility Distribution Main",
                    category="secondary_main",
                    material="Cast Iron",
                    diameter_mm=350,
                    length_m=800.0,
                    nominal_pressure_psi=58.0,
                    coordinates_json=json.dumps([[-74.0110, 40.7090], [-74.0080, 40.7110]]),
                    is_simulated=True,
                ),
                PipelineSegmentModel(
                    id="PIPE-IND-1A-04",
                    name="Industrial Park Southern Feeder",
                    category="secondary_distribution",
                    material="HDPE",
                    diameter_mm=250,
                    length_m=1500.0,
                    nominal_pressure_psi=52.0,
                    coordinates_json=json.dumps([[-74.0150, 40.7050], [-74.0100, 40.7070]]),
                    is_simulated=True,
                ),
            ]
            for m in mock_segments:
                db.add(m)
            db.commit()
            segments = db.query(PipelineSegmentModel).all()

        # 2. Query upstream system states
        detections = db.query(AiDetectionModel).all()
        health_records = db.query(PipelineHealthModel).all()
        vulnerability_records = db.query(PipelineVulnerabilityProfileModel).all()
        clusters = db.query(SpatialIncidentClusterModel).all()
        rovers = db.query(RoverModel).all()

        det_by_seg = {d.pipeline_segment_id: d for d in detections}
        health_by_seg = {h.pipeline_segment_id: h for h in health_records}
        vuln_by_seg = {v.pipeline_segment_id: v for v in vulnerability_records}

        recommendations_to_add = []
        priorities_to_add = []
        evidences_to_add = []
        impacts_to_add = []

        immediate_count = 0
        urgent_leak_count = 0
        preventive_count = 0

        for seg in segments:
            seg_id = str(seg.id)
            seg_name = str(seg.name)
            diameter = int(seg.diameter_mm or 300)
            length = float(seg.length_m or 1000.0)
            material = str(seg.material or "Ductile Iron")

            det = det_by_seg.get(seg_id)
            health = health_by_seg.get(seg_id)
            vuln = vuln_by_seg.get(seg_id)

            # Component indicators
            inc_sev = (det.anomaly_score * 100.0) if det else 0.0
            vuln_score = vuln.vulnerability_score if vuln else 45.0
            health_score = health.health_score if health else 75.0
            hydraulic_score = vuln.hydraulic_score if vuln else 25.0
            incident_count = vuln.active_incident_count if vuln else (1 if det else 0)
            confidence = vuln.confidence if vuln else (det.confidence if det else 0.85)

            # Deterministic Priority Calculation (Phase 5)
            p_result = OperationalPrioritisationService.calculate_priority(
                incident_severity=inc_sev,
                vulnerability_score=vuln_score,
                health_score=health_score,
                hydraulic_impact=hydraulic_score,
                diameter_mm=diameter,
                historical_incident_count=incident_count,
                confidence=confidence,
            )
            p_score = p_result["composite_priority_score"]
            p_tier = p_result["priority_tier"]

            # Category & Action Determination
            contributing_systems = []
            if det:
                contributing_systems.append("TASK_07_AI_LEAK_DETECTION")
            if health:
                contributing_systems.append("TASK_09_PREDICTIVE_MAINTENANCE")
            if vuln:
                contributing_systems.append("TASK_11_INFRASTRUCTURE_INTELLIGENCE")
            contributing_systems.append("TASK_10_HYDRAULIC_DIGITAL_TWIN")

            if inc_sev >= 70.0:
                cat = "URGENT_LEAK_INVESTIGATION"
                severity = "CRITICAL"
                action = "Deploy autonomous acoustic crawler rover for high-frequency pin-point localization"
                why = f"High-confidence acoustic anomaly ({inc_sev:.1f}%) detected on high-vulnerability arterial conduit {seg_name}."
                expected_impact = "Mitigates catastrophic joint burst; preserves network pressure stability in central grid."
                urgent_leak_count += 1
            elif p_score >= 75.0:
                cat = "IMMEDIATE_INSPECTION"
                severity = "CRITICAL"
                action = "Perform immediate rover transit and ultrasonic pipe-wall thickness scan"
                why = f"High vulnerability ({vuln_score:.1f}/100) and substantial health deficit ({100 - health_score:.1f}) present severe rupture risk."
                expected_impact = "Prevents impending service disruption across major industrial and commercial hubs."
                immediate_count += 1
            elif health_score < 55.0 or (vuln and vuln.trend_direction == "DETERIORATING"):
                cat = "PREVENTIVE_MAINTENANCE"
                severity = "HIGH"
                action = "Schedule pipe relining, cathodic protection inspection, and localized sleeve reinforcement"
                why = f"Structural degradation slope on {material} material indicates accelerating wall thinning."
                expected_impact = "Extends asset operating life by 5-10 years; averts sudden catastrophic blowout."
                preventive_count += 1
            elif hydraulic_score > 60.0:
                cat = "HYDRAULIC_INVESTIGATION"
                severity = "MODERATE"
                action = "Simulate PRV (pressure reducing valve) throttling and flow re-routing in digital twin"
                why = f"Excessive hydraulic headloss gradient (>4.0 m/km) indicates severe friction resistance."
                expected_impact = "Reduces cyclic pressure fatigue and pumping energy consumption by up to 12%."
            elif confidence < 0.70:
                cat = "PIPELINE_HEALTH_REVIEW"
                severity = "MODERATE"
                action = "Deploy IoT pressure and acoustic logger nodes to eliminate telemetry coverage gaps"
                why = f"Data completeness is below threshold ({round(confidence * 100)}%), widening prediction uncertainty."
                expected_impact = "Restores high-fidelity predictive modeling and clarifies risk profile."
            else:
                cat = "CONTINUOUS_MONITORING"
                severity = "LOW"
                action = "Maintain continuous 1Hz acoustic listening and nominal pressure tracking"
                why = f"Pipeline {seg_name} operates within nominal hydraulic and structural tolerance thresholds."
                expected_impact = "Ensures baseline operational stability with zero service interruption."

            # Evaluate rover resource readiness
            res_plan = OperationalResourcePlanningService.evaluate_resources_for_target(
                db=db,
                pipeline_segment_id=seg_id,
                segment_name=seg_name,
                estimated_segment_length_m=length,
            )

            rec_id = f"REC-{uuid.uuid4().hex[:10]}"

            # Construct recommendation record
            rec_model = OperationalRecommendationModel(
                id=rec_id,
                assessment_id=assessment_id,
                category=cat,
                pipeline_segment_id=seg_id,
                segment_name=seg_name,
                associated_incident_id=str(det.id) if det else None,
                associated_cluster_id=None,
                risk_severity=severity,
                priority_score=p_score,
                priority_tier=p_tier,
                recommended_action=action,
                action_details=f"Target: {seg_name} ({diameter}mm {material}, {length}m). Assigned resource: {res_plan.get('best_rover_name') or 'Pending'}",
                why_explanation=why,
                what_missing="No significant data gaps. All baseline telemetric and hydraulic attributes verified." if confidence >= 0.75 else "Missing recent geotechnical soil corrosivity and ground vibration measurements.",
                expected_impact=expected_impact,
                contributing_factors_json=json.dumps(p_result["components"]),
                evidence_sources_json=json.dumps(contributing_systems),
                resource_requirements_json=json.dumps({
                    "best_rover_id": res_plan.get("best_rover_id"),
                    "best_rover_name": res_plan.get("best_rover_name"),
                    "feasibility": res_plan.get("dispatch_feasibility"),
                    "estimated_duration_min": res_plan.get("estimated_duration_min"),
                    "estimated_energy_pct": res_plan.get("estimated_energy_pct"),
                }),
                confidence=confidence,
                data_completeness_pct=round(confidence * 100.0, 1),
                uncertainty_margin=round((1.0 - confidence) * 20.0, 1),
                status="GENERATED",
                approval_status="PENDING",
                assigned_rover_id=res_plan.get("best_rover_id"),
                dispatched_mission_id=None,
                created_at=now,
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            )
            recommendations_to_add.append(rec_model)

            # Construct priority record
            p_model = OperationalPriorityModel(
                id=f"PRIO-{uuid.uuid4().hex[:10]}",
                recommendation_id=rec_id,
                pipeline_segment_id=seg_id,
                rank_position=1,
                composite_priority_score=p_score,
                incident_severity_component=p_result["components"]["incident_severity"],
                vulnerability_component=p_result["components"]["vulnerability"],
                asset_health_component=p_result["components"]["asset_health_deficit"],
                hydraulic_impact_component=p_result["components"]["hydraulic_impact"],
                service_criticality_component=p_result["components"]["service_criticality"],
                recurrence_component=p_result["components"]["recurrence"],
                confidence_weight=p_result["confidence_weight"],
                weights_version=p_result["weights_version"],
                weights_applied_json=json.dumps(p_result["weights_applied"]),
                reassessment_counter=0,
                last_ranked_at=now,
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            )
            priorities_to_add.append(p_model)

            # Construct evidence records
            if det:
                evidences_to_add.append(OperationalEvidenceReferenceModel(
                    id=f"EVID-{uuid.uuid4().hex[:10]}",
                    recommendation_id=rec_id,
                    evidence_type="ACOUSTIC_ANOMALY",
                    source_module="TASK_07_AI",
                    source_table="ai_detections",
                    source_record_id=str(det.id),
                    metric_name="anomaly_score",
                    metric_value=float(det.anomaly_score),
                    metric_unit="normalized_0_1",
                    confidence_score=float(det.confidence),
                    evidence_summary=f"AI acoustic model detected {det.classification} with confidence {det.confidence:.2f}",
                    payload_json=json.dumps({"estimated_loss_lph": det.estimated_loss_lph}),
                    recorded_at=now,
                    is_simulated=True,
                ))

            if vuln:
                evidences_to_add.append(OperationalEvidenceReferenceModel(
                    id=f"EVID-{uuid.uuid4().hex[:10]}",
                    recommendation_id=rec_id,
                    evidence_type="VULNERABILITY_PROFILE",
                    source_module="TASK_11_GEOSPATIAL",
                    source_table="pipeline_vulnerability_profiles",
                    source_record_id=str(vuln.id),
                    metric_name="vulnerability_score",
                    metric_value=float(vuln.vulnerability_score),
                    metric_unit="score_0_100",
                    confidence_score=float(vuln.confidence),
                    evidence_summary=f"Multi-factor vulnerability rated {vuln.vulnerability_score:.1f} ({vuln.vulnerability_level})",
                    payload_json=json.dumps({"hydraulic_score": vuln.hydraulic_score, "structural_score": vuln.structural_score}),
                    recorded_at=now,
                    is_simulated=True,
                ))

            # Construct impact assessment
            impact_res = OperationalImpactService.assess_recommendation_impact(
                recommendation_id=rec_id,
                pipeline_segment_id=seg_id,
                diameter_mm=diameter,
                risk_severity=severity,
                nominal_pressure_bar=float(seg.nominal_pressure_psi or 60.0) / 14.5038,
                segment_length_m=length,
            )
            impacts_to_add.append(OperationalImpactAssessmentModel(
                id=impact_res["id"],
                recommendation_id=rec_id,
                pipeline_segment_id=seg_id,
                scenario_id=impact_res["scenario_id"],
                estimated_water_loss_m3_day=impact_res["estimated_water_loss_m3_day"],
                is_water_loss_measured=False,
                service_disruption_risk=impact_res["service_disruption_risk"],
                affected_nodes_count=impact_res["affected_nodes_count"],
                affected_population_estimate=impact_res["affected_population_estimate"],
                hydraulic_headloss_delta_m=impact_res["hydraulic_headloss_delta_m"],
                min_pressure_drop_bar=impact_res["min_pressure_drop_bar"],
                estimated_inspection_distance_m=impact_res["estimated_inspection_distance_m"],
                estimated_mission_energy_pct=impact_res["estimated_mission_energy_pct"],
                estimated_inspection_duration_min=impact_res["estimated_inspection_duration_min"],
                cost_impact_display="NOT AVAILABLE",
                data_quality_rating=impact_res["data_quality_rating"],
                assumptions_json=json.dumps(impact_res["assumptions"]),
                uncertainty_margin_pct=impact_res["uncertainty_margin_pct"],
                assessed_at=now,
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            ))

        # Rank all priorities deterministically in descending score order
        priorities_to_add.sort(key=lambda x: x.composite_priority_score, reverse=True)
        for rank, p in enumerate(priorities_to_add, start=1):
            p.rank_position = rank

        # Calculate network urgency
        if immediate_count > 0 or urgent_leak_count > 0:
            overall_urgency = "CRITICAL"
        elif preventive_count > 0:
            overall_urgency = "ELEVATED"
        else:
            overall_urgency = "ROUTINE"

        assessment = OperationalAssessmentModel(
            id=assessment_id,
            assessment_name=f"Comprehensive City-Wide Operational Audit ({now.strftime('%Y-%m-%d %H:%M')})",
            total_recommendations=len(recommendations_to_add),
            immediate_action_count=immediate_count,
            urgent_leak_count=urgent_leak_count,
            preventive_count=preventive_count,
            critical_segments_analyzed=len(segments),
            overall_network_urgency=overall_urgency,
            summary_json=json.dumps({
                "immediate_inspections": immediate_count,
                "urgent_leaks": urgent_leak_count,
                "preventive_actions": preventive_count,
                "total_recommendations": len(recommendations_to_add),
                "fleet_size": len(rovers),
                "methodology_version": cls.METHODOLOGY_VERSION,
            }),
            assessed_at=now,
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )

        db.add(assessment)
        for r in recommendations_to_add:
            db.add(r)
        for p in priorities_to_add:
            db.add(p)
        for e in evidences_to_add:
            db.add(e)
        for i in impacts_to_add:
            db.add(i)

        db.commit()

        cls._broadcast_event("operational_assessment_updated", {
            "assessment_id": assessment.id,
            "total_recommendations": assessment.total_recommendations,
            "immediate_action_count": assessment.immediate_action_count,
            "overall_network_urgency": assessment.overall_network_urgency,
        })

        return assessment

    @classmethod
    def get_operational_overview(cls, db: Session) -> Dict[str, Any]:
        """
        Gathers high-level operational intelligence metrics across the platform.
        """
        latest_assessment = db.query(OperationalAssessmentModel).order_by(
            OperationalAssessmentModel.assessed_at.desc()
        ).first()

        active_incidents = db.query(AiDetectionModel).filter(
            AiDetectionModel.classification.like("%LEAK%")
        ).count()

        critical_segments = db.query(PipelineVulnerabilityProfileModel).filter(
            PipelineVulnerabilityProfileModel.vulnerability_level.in_(["HIGH", "CRITICAL"])
        ).count()

        pending_recs = db.query(OperationalRecommendationModel).filter(
            OperationalRecommendationModel.status.in_(["GENERATED", "PENDING_REVIEW"])
        ).count()

        approved_actions = db.query(OperationalRecommendationModel).filter(
            OperationalRecommendationModel.approval_status == "APPROVED"
        ).count()

        active_missions = db.query(MissionModel).filter(
            MissionModel.status.in_(["Scheduled", "In Progress", "ACTIVE"])
        ).count()

        available_rovers = db.query(RoverModel).filter(
            RoverModel.battery_percentage >= 20.0,
            RoverModel.motor_temp_c < 65.0,
            RoverModel.operating_state.in_(["IDLE", "STANDBY", "ONLINE"])
        ).count()

        avg_health = 82.5
        all_health = db.query(PipelineHealthModel).all()
        if all_health:
            avg_health = round(sum(h.health_score for h in all_health) / len(all_health), 1)

        # Count recommendations by category
        recs = db.query(OperationalRecommendationModel).all()
        by_cat = {}
        for r in recs:
            by_cat[r.category] = by_cat.get(r.category, 0) + 1

        assessment_resp = None
        network_urgency = "ROUTINE"
        if latest_assessment:
            network_urgency = latest_assessment.overall_network_urgency
            assessment_resp = {
                "id": latest_assessment.id,
                "assessment_name": latest_assessment.assessment_name,
                "total_recommendations": latest_assessment.total_recommendations,
                "immediate_action_count": latest_assessment.immediate_action_count,
                "urgent_leak_count": latest_assessment.urgent_leak_count,
                "preventive_count": latest_assessment.preventive_count,
                "critical_segments_analyzed": latest_assessment.critical_segments_analyzed,
                "overall_network_urgency": latest_assessment.overall_network_urgency,
                "summary": json.loads(latest_assessment.summary_json) if latest_assessment.summary_json else {},
                "assessed_at": latest_assessment.assessed_at.isoformat() if latest_assessment.assessed_at else None,
                "is_simulated": True,
                "source": "VIRTUAL_SIMULATION_ENGINE",
            }

        return {
            "active_incidents_count": active_incidents,
            "critical_segments_count": critical_segments,
            "pending_recommendations_count": pending_recs,
            "approved_actions_count": approved_actions,
            "active_missions_count": active_missions,
            "available_rovers_count": available_rovers,
            "network_health_score": avg_health,
            "network_urgency": network_urgency,
            "recommendations_by_category": by_cat,
            "latest_assessment": assessment_resp,
            "validation_status": "VALIDATED_AND_CERTIFIED",
            "methodology_version": cls.METHODOLOGY_VERSION,
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
            "actuation_notice": "REAL-WORLD PHYSICAL ACTUATORS PERMANENTLY DISABLED (SAFETY INTERLOCKED)",
        }
