"""
AQUA CREW — Master Infrastructure Intelligence Service (Task 11)
Orchestrates multi-factor vulnerability scoring, geospatial clustering, zone aggregation,
temporal deterioration trends, predictive forecasting, and inspection dispatch queues.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import uuid
from sqlalchemy.orm import Session

from app.models.pipeline_segment import PipelineSegmentModel
from app.models.ai_detection import AiDetectionModel
from app.models.predictive_maintenance import PipelineHealthModel, PredictiveRiskModel, HistoricalTrendModel
from app.models.digital_twin import HydraulicLinkModel
from app.models.infrastructure_intelligence import (
    PipelineVulnerabilityProfileModel,
    InfrastructureRiskAssessmentModel,
    SpatialIncidentClusterModel,
    GeographicRiskZoneModel,
    InspectionPriorityRecordModel,
    InfrastructureIntelligenceSnapshotModel,
)
from app.repositories.pipeline_repository import PipelineRepository
from app.services.infrastructure_intelligence.vulnerability_scoring_service import VulnerabilityScoringService
from app.services.infrastructure_intelligence.geospatial_clustering_service import GeospatialClusteringService
from app.services.infrastructure_intelligence.spatial_analysis_service import SpatialAnalysisService
from app.services.infrastructure_intelligence.risk_trend_service import RiskTrendService
from app.services.infrastructure_intelligence.infrastructure_prediction_service import InfrastructurePredictionService
from app.services.infrastructure_intelligence.inspection_priority_service import InspectionPriorityService
from app.core.exceptions import AquaCrewException


class InfrastructureIntelligenceService:
    @classmethod
    def run_assessment(cls, db: Session) -> Dict[str, Any]:
        """
        Executes end-to-end infrastructure intelligence pipeline across all pipelines,
        updating profiles, clusters, zones, predictions, and inspection queue.
        """
        # Ensure default pipeline segments are seeded if database is empty
        PipelineRepository.seed_defaults(db)
        segments = PipelineRepository.get_all(db)
        if not segments:
            return {"status": "NO_SEGMENTS_AVAILABLE"}

        # Gather supporting datasets
        ai_detections = db.query(AiDetectionModel).all()
        health_records = {h.pipeline_segment_id: h for h in db.query(PipelineHealthModel).all()}
        predictive_records = {p.pipeline_segment_id: p for p in db.query(PredictiveRiskModel).all()}
        trend_db_records = {t.pipeline_segment_id: t for t in db.query(HistoricalTrendModel).all()}
        digital_twin_links = db.query(HydraulicLinkModel).all()

        # 1. Geospatial Clustering on AI leak detections and high-risk nodes
        incident_points = []
        for d in ai_detections:
            if d.estimated_latitude is not None and d.estimated_longitude is not None:
                incident_points.append({
                    "id": d.id,
                    "latitude": d.estimated_latitude,
                    "longitude": d.estimated_longitude,
                    "segment_id": d.pipeline_segment_id,
                    "severity": d.anomaly_score or 0.60,
                    "material": "Ductile Iron",
                })

        # If sparse detections, seed representative incident points from pipeline segments
        if len(incident_points) < 2:
            for s in segments:
                mid = SpatialAnalysisService.get_segment_midpoint(s)
                if mid and ("Trunk Line B" in s.name or "Harbor" in s.name):
                    incident_points.append({
                        "id": f"INC-SEED-{s.id}",
                        "latitude": mid[0],
                        "longitude": mid[1],
                        "segment_id": s.id,
                        "severity": 0.75 if "Trunk Line B" in s.name else 0.55,
                        "material": s.material,
                    })

        raw_clusters = GeospatialClusteringService.cluster_incidents(incident_points)

        # Clear and persist clusters
        db.query(SpatialIncidentClusterModel).delete()
        for c in raw_clusters:
            cluster_model = SpatialIncidentClusterModel(
                id=c["id"],
                cluster_name=c["cluster_name"],
                zone_id=c["zone_id"],
                centroid_lat=c["centroid_lat"],
                centroid_lng=c["centroid_lng"],
                radius_m=c["radius_m"],
                incident_count=c["incident_count"],
                dominant_material=c["dominant_material"],
                average_severity=c["average_severity"],
                cluster_risk_level=c["cluster_risk_level"],
                affected_segment_ids=json.dumps(c["affected_segment_ids"]),
                hotspot_intensity=c["hotspot_intensity"],
                is_active=True,
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            )
            db.add(cluster_model)
        db.flush()

        # 2. Compute Segment Proximities to nearest cluster
        cluster_distances = {}
        for s in segments:
            cluster_distances[s.id] = SpatialAnalysisService.calculate_distance_to_nearest_cluster(s, raw_clusters)

        # 3. Multi-Factor Vulnerability Scoring & Temporal Trends
        vulnerability_profiles_dict = {}
        temporal_trends_dict = {}
        predictions_dict = {}

        for s in segments:
            dist_c = cluster_distances[s.id]
            h_rec = health_records.get(s.id)
            p_rec = predictive_records.get(s.id)
            t_rec = trend_db_records.get(s.id)

            # Score
            prof = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
                segment=s,
                health_rec=h_rec,
                predictive_rec=p_rec,
                ai_detections=ai_detections,
                digital_twin_links=digital_twin_links,
                distance_to_cluster_m=dist_c,
            )
            vulnerability_profiles_dict[s.id] = prof

            # Trend
            v_score = prof["vulnerability_score"]
            trend = RiskTrendService.calculate_temporal_trends(
                segment=s,
                current_vulnerability=v_score,
                trend_rec=t_rec,
                health_rec=h_rec,
                recent_detections=[d for d in ai_detections if d.pipeline_segment_id == s.id],
            )
            temporal_trends_dict[s.id] = trend

            # Prediction
            pred = InfrastructurePredictionService.forecast_risk(
                segment=s,
                current_vulnerability=v_score,
                trend_info=trend,
                contributing_factors=prof["contributing_factors"],
                cluster_proximity_m=dist_c,
            )
            predictions_dict[s.id] = pred

            # Persist or update PipelineVulnerabilityProfileModel
            existing_prof = db.query(PipelineVulnerabilityProfileModel).filter(
                PipelineVulnerabilityProfileModel.pipeline_segment_id == s.id
            ).first()

            if not existing_prof:
                existing_prof = PipelineVulnerabilityProfileModel(
                    id=f"vuln_{s.id}",
                    pipeline_segment_id=s.id,
                    segment_name=s.name,
                    material=s.material,
                    diameter_mm=s.diameter_mm,
                    length_m=s.length_m,
                    pressure_zone_id=s.pressure_zone_id,
                    category=s.category,
                )
                db.add(existing_prof)

            existing_prof.vulnerability_score = prof["vulnerability_score"]
            existing_prof.vulnerability_level = prof["vulnerability_level"]
            existing_prof.hydraulic_score = prof["hydraulic_score"]
            existing_prof.structural_score = prof["structural_score"]
            existing_prof.incident_score = prof["incident_score"]
            existing_prof.environmental_score = prof["environmental_score"]
            existing_prof.contributing_factors = json.dumps(prof["contributing_factors"])
            existing_prof.confidence = prof["confidence"]
            existing_prof.data_completeness_pct = prof["data_completeness_pct"]
            existing_prof.uncertainty_margin = prof["uncertainty_margin"]
            existing_prof.deterioration_rate_per_day = trend["deterioration_rate_per_day"]
            existing_prof.trend_direction = trend["trend_direction"]
            existing_prof.active_incident_count = prof["active_incident_count"]
            existing_prof.midpoint_lat = prof["midpoint_lat"]
            existing_prof.midpoint_lng = prof["midpoint_lng"]
            existing_prof.assessed_at = datetime.now(timezone.utc)

            # Persist or update InfrastructureRiskAssessmentModel
            existing_risk = db.query(InfrastructureRiskAssessmentModel).filter(
                InfrastructureRiskAssessmentModel.pipeline_segment_id == s.id
            ).first()

            if not existing_risk:
                existing_risk = InfrastructureRiskAssessmentModel(
                    id=f"risk_{s.id}",
                    pipeline_segment_id=s.id,
                )
                db.add(existing_risk)

            existing_risk.vulnerability_score = prof["vulnerability_score"]
            existing_risk.risk_level = prof["vulnerability_level"]
            existing_risk.risk_category = "HYDRAULIC_SURGE_STRUCTURAL" if prof["hydraulic_score"] > 50 else "CORROSION_FATIGUE"
            existing_risk.projected_risk_24h = pred["projected_risk_24h"]
            existing_risk.projected_risk_7d = pred["projected_risk_7d"]
            existing_risk.projected_risk_30d = pred["projected_risk_30d"]
            existing_risk.trend_24h_delta = trend["trend_24h_delta"]
            existing_risk.trend_7d_delta = trend["trend_7d_delta"]
            existing_risk.trend_30d_delta = trend["trend_30d_delta"]
            existing_risk.risk_drivers = json.dumps(pred["primary_risk_drivers"])
            existing_risk.mitigation_urgency = pred["mitigation_urgency"]
            existing_risk.hydraulic_deficit_flag = prof["hydraulic_score"] > 60.0
            existing_risk.cluster_proximity_m = dist_c
            existing_risk.assessed_at = datetime.now(timezone.utc)

        db.flush()

        # 4. Geographic Risk Zones Aggregation
        zone_data = SpatialAnalysisService.aggregate_zones(segments, vulnerability_profiles_dict, raw_clusters)
        db.query(GeographicRiskZoneModel).delete()
        for z in zone_data:
            zone_model = GeographicRiskZoneModel(
                id=z["id"],
                zone_code=z["zone_code"],
                zone_name=z["zone_name"],
                description=z["description"],
                total_segments=z["total_segments"],
                total_length_km=z["total_length_km"],
                avg_vulnerability_score=z["avg_vulnerability_score"],
                dominant_risk_level=z["dominant_risk_level"],
                critical_segment_count=z["critical_segment_count"],
                active_clusters_count=z["active_clusters_count"],
                avg_pressure_psi=z["avg_pressure_psi"],
                bounds_json=z["bounds_json"],
                updated_at=datetime.now(timezone.utc),
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            )
            db.add(zone_model)
        db.flush()

        # 5. Synchronize Inspection Queue
        InspectionPriorityService.sync_inspection_queue(
            db=db,
            segments=segments,
            vulnerability_profiles=vulnerability_profiles_dict,
            trend_records=temporal_trends_dict,
            cluster_distances=cluster_distances,
        )

        # 6. Generate and Persist Snapshot Metrics
        all_profs = list(vulnerability_profiles_dict.values())
        total_segs = len(all_profs)
        crit_segs = sum(1 for p in all_profs if p["vulnerability_level"] == "CRITICAL")
        high_segs = sum(1 for p in all_profs if p["vulnerability_level"] == "HIGH")
        mod_segs = sum(1 for p in all_profs if p["vulnerability_level"] == "MODERATE")
        low_segs = sum(1 for p in all_profs if p["vulnerability_level"] in ["LOW", "VERY_LOW"])
        avg_vuln = round(sum(p["vulnerability_score"] for p in all_profs) / total_segs, 1) if total_segs else 0.0
        avg_det_rate = round(sum(t["deterioration_rate_per_day"] for t in temporal_trends_dict.values()) / total_segs, 2) if total_segs else 0.0

        pending_inspections = db.query(InspectionPriorityRecordModel).filter(
            InspectionPriorityRecordModel.status.in_(["PENDING", "ACKNOWLEDGED"])
        ).count()

        snap_id = f"SNAP-{uuid.uuid4().hex[:6].upper()}"
        snapshot = InfrastructureIntelligenceSnapshotModel(
            id=snap_id,
            total_segments_analyzed=total_segs,
            critical_segments_count=crit_segs,
            high_risk_segments_count=high_segs,
            moderate_risk_segments_count=mod_segs,
            low_risk_segments_count=low_segs,
            average_network_vulnerability=avg_vuln,
            active_clusters_count=len(raw_clusters),
            pending_inspections_count=pending_inspections,
            network_deterioration_rate=avg_det_rate,
            summary_json=json.dumps({
                "critical_segments": crit_segs,
                "high_risk_segments": high_segs,
                "moderate_risk_segments": mod_segs,
                "low_risk_segments": low_segs,
                "avg_vulnerability": avg_vuln,
            }),
            created_at=datetime.now(timezone.utc),
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
        db.add(snapshot)
        db.commit()

        return {
            "status": "ASSESSMENT_COMPLETED",
            "snapshot_id": snap_id,
            "total_segments": total_segs,
            "critical_count": crit_segs,
            "high_risk_count": high_segs,
            "active_clusters": len(raw_clusters),
            "pending_inspections": pending_inspections,
        }

    @classmethod
    def get_overview(cls, db: Session) -> Dict[str, Any]:
        """
        Returns high-level executive intelligence summary for dashboard metric cards.
        """
        # Ensure assessments are present
        if db.query(PipelineVulnerabilityProfileModel).count() == 0:
            cls.run_assessment(db)

        profiles = db.query(PipelineVulnerabilityProfileModel).all()
        clusters = db.query(SpatialIncidentClusterModel).all()
        zones = db.query(GeographicRiskZoneModel).all()
        inspections = db.query(InspectionPriorityRecordModel).all()

        total = len(profiles)
        critical = sum(1 for p in profiles if p.vulnerability_level == "CRITICAL")
        high = sum(1 for p in profiles if p.vulnerability_level == "HIGH")
        moderate = sum(1 for p in profiles if p.vulnerability_level == "MODERATE")
        low = sum(1 for p in profiles if p.vulnerability_level in ["LOW", "VERY_LOW"])

        avg_score = round(sum(p.vulnerability_score for p in profiles) / total, 1) if total else 0.0
        avg_det_rate = round(sum(p.deterioration_rate_per_day for p in profiles) / total, 2) if total else 0.0

        # Rapid deteriorating count
        deteriorating_count = sum(1 for p in profiles if p.trend_direction == "DETERIORATING")
        pending_insp_count = sum(1 for i in inspections if i.status in ["PENDING", "ACKNOWLEDGED"])

        # Highest risk segment and zone
        highest_seg = max(profiles, key=lambda p: p.vulnerability_score) if profiles else None
        highest_zone = max(zones, key=lambda z: z.avg_vulnerability_score) if zones else None

        return {
            "total_segments_analyzed": total,
            "critical_segments_count": critical,
            "high_risk_segments_count": high,
            "moderate_risk_segments_count": moderate,
            "low_risk_segments_count": low,
            "average_network_vulnerability": avg_score,
            "network_deterioration_rate": avg_det_rate,
            "deteriorating_segments_count": deteriorating_count,
            "active_clusters_count": len(clusters),
            "pending_inspections_count": pending_insp_count,
            "highest_risk_segment": {
                "id": highest_seg.pipeline_segment_id,
                "name": highest_seg.segment_name,
                "score": highest_seg.vulnerability_score,
                "level": highest_seg.vulnerability_level,
                "material": highest_seg.material,
            } if highest_seg else None,
            "highest_risk_zone": {
                "code": highest_zone.zone_code,
                "name": highest_zone.zone_name,
                "avg_score": highest_zone.avg_vulnerability_score,
                "critical_count": highest_zone.critical_segment_count,
            } if highest_zone else None,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
        }

    @classmethod
    def get_segments(
        cls,
        db: Session,
        risk_level: Optional[str] = None,
        zone: Optional[str] = None,
        trend: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Lists pipeline vulnerability profiles with filtering and pagination.
        """
        if db.query(PipelineVulnerabilityProfileModel).count() == 0:
            cls.run_assessment(db)

        query = db.query(PipelineVulnerabilityProfileModel)
        if risk_level:
            query = query.filter(PipelineVulnerabilityProfileModel.vulnerability_level == risk_level.upper())
        if zone:
            query = query.filter(PipelineVulnerabilityProfileModel.pressure_zone_id == zone)
        if trend:
            query = query.filter(PipelineVulnerabilityProfileModel.trend_direction == trend.upper())

        total = query.count()
        profiles = query.order_by(PipelineVulnerabilityProfileModel.vulnerability_score.desc()).offset(offset).limit(limit).all()

        results = []
        for p in profiles:
            factors = {}
            if p.contributing_factors:
                try:
                    factors = json.loads(p.contributing_factors)
                except Exception:
                    pass

            results.append({
                "id": p.id,
                "pipeline_segment_id": p.pipeline_segment_id,
                "segment_name": p.segment_name,
                "material": p.material,
                "diameter_mm": p.diameter_mm,
                "length_m": p.length_m,
                "pressure_zone_id": p.pressure_zone_id,
                "category": p.category,
                "vulnerability_score": p.vulnerability_score,
                "vulnerability_level": p.vulnerability_level,
                "hydraulic_score": p.hydraulic_score,
                "structural_score": p.structural_score,
                "incident_score": p.incident_score,
                "environmental_score": p.environmental_score,
                "contributing_factors": factors,
                "confidence": p.confidence,
                "data_completeness_pct": p.data_completeness_pct,
                "uncertainty_margin": p.uncertainty_margin,
                "deterioration_rate_per_day": p.deterioration_rate_per_day,
                "trend_direction": p.trend_direction,
                "active_incident_count": p.active_incident_count,
                "midpoint_lat": p.midpoint_lat,
                "midpoint_lng": p.midpoint_lng,
                "assessed_at": p.assessed_at.isoformat() if p.assessed_at else None,
                "is_simulated": p.is_simulated,
            })

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": results,
        }

    @classmethod
    def get_segment_deep_dive(cls, db: Session, segment_id: str) -> Dict[str, Any]:
        """
        Returns full deep dive for a single pipeline segment.
        """
        profile = db.query(PipelineVulnerabilityProfileModel).filter(
            PipelineVulnerabilityProfileModel.pipeline_segment_id == segment_id
        ).first()

        if not profile:
            cls.run_assessment(db)
            profile = db.query(PipelineVulnerabilityProfileModel).filter(
                PipelineVulnerabilityProfileModel.pipeline_segment_id == segment_id
            ).first()

        if not profile:
            raise AquaCrewException(
                status_code=404,
                code="SEGMENT_PROFILE_NOT_FOUND",
                message=f"Pipeline vulnerability profile for segment '{segment_id}' not found.",
            )

        risk = db.query(InfrastructureRiskAssessmentModel).filter(
            InfrastructureRiskAssessmentModel.pipeline_segment_id == segment_id
        ).first()

        inspection = db.query(InspectionPriorityRecordModel).filter(
            InspectionPriorityRecordModel.pipeline_segment_id == segment_id
        ).first()

        factors = {}
        if profile.contributing_factors:
            try:
                factors = json.loads(profile.contributing_factors)
            except Exception:
                pass

        risk_drivers = []
        if risk and risk.risk_drivers:
            try:
                risk_drivers = json.loads(risk.risk_drivers)
            except Exception:
                pass

        inspection_reasons = []
        if inspection and inspection.reasons:
            try:
                inspection_reasons = json.loads(inspection.reasons)
            except Exception:
                pass

        return {
            "pipeline_segment_id": profile.pipeline_segment_id,
            "segment_name": profile.segment_name,
            "material": profile.material,
            "diameter_mm": profile.diameter_mm,
            "length_m": profile.length_m,
            "pressure_zone_id": profile.pressure_zone_id,
            "category": profile.category,
            "vulnerability_score": profile.vulnerability_score,
            "vulnerability_level": profile.vulnerability_level,
            "hydraulic_score": profile.hydraulic_score,
            "structural_score": profile.structural_score,
            "incident_score": profile.incident_score,
            "environmental_score": profile.environmental_score,
            "contributing_factors": factors,
            "confidence": profile.confidence,
            "data_completeness_pct": profile.data_completeness_pct,
            "uncertainty_margin": profile.uncertainty_margin,
            "deterioration_rate_per_day": profile.deterioration_rate_per_day,
            "trend_direction": profile.trend_direction,
            "active_incident_count": profile.active_incident_count,
            "midpoint_lat": profile.midpoint_lat,
            "midpoint_lng": profile.midpoint_lng,
            "assessed_at": profile.assessed_at.isoformat() if profile.assessed_at else None,
            "predictive_forecast": {
                "projected_risk_24h": risk.projected_risk_24h if risk else profile.vulnerability_score,
                "projected_risk_7d": risk.projected_risk_7d if risk else profile.vulnerability_score,
                "projected_risk_30d": risk.projected_risk_30d if risk else profile.vulnerability_score,
                "trend_24h_delta": risk.trend_24h_delta if risk else 0.0,
                "trend_7d_delta": risk.trend_7d_delta if risk else 0.0,
                "trend_30d_delta": risk.trend_30d_delta if risk else 0.0,
                "primary_risk_drivers": risk_drivers,
                "mitigation_urgency": risk.mitigation_urgency if risk else "PLANNED",
                "hydraulic_deficit_flag": risk.hydraulic_deficit_flag if risk else False,
                "cluster_proximity_m": risk.cluster_proximity_m if risk else 9999.0,
            },
            "inspection_priority": {
                "id": inspection.id,
                "priority_score": inspection.priority_score,
                "priority_level": inspection.priority_level,
                "status": inspection.status,
                "suggested_action": inspection.suggested_action,
                "reasons": inspection_reasons,
                "assigned_rover_id": inspection.assigned_rover_id,
                "mission_recommendation_id": inspection.mission_recommendation_id,
            } if inspection else None,
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
        }

    @classmethod
    def get_clusters(cls, db: Session) -> List[Dict[str, Any]]:
        if db.query(SpatialIncidentClusterModel).count() == 0:
            cls.run_assessment(db)
        clusters = db.query(SpatialIncidentClusterModel).all()
        results = []
        for c in clusters:
            affected = []
            if c.affected_segment_ids:
                try:
                    affected = json.loads(c.affected_segment_ids)
                except Exception:
                    pass
            results.append({
                "id": c.id,
                "cluster_name": c.cluster_name,
                "zone_id": c.zone_id,
                "centroid_lat": c.centroid_lat,
                "centroid_lng": c.centroid_lng,
                "radius_m": c.radius_m,
                "incident_count": c.incident_count,
                "dominant_material": c.dominant_material,
                "average_severity": c.average_severity,
                "cluster_risk_level": c.cluster_risk_level,
                "affected_segment_ids": affected,
                "hotspot_intensity": c.hotspot_intensity,
                "is_active": c.is_active,
                "identified_at": c.identified_at.isoformat() if c.identified_at else None,
                "is_simulated": c.is_simulated,
            })
        return results

    @classmethod
    def get_zones(cls, db: Session) -> List[Dict[str, Any]]:
        if db.query(GeographicRiskZoneModel).count() == 0:
            cls.run_assessment(db)
        zones = db.query(GeographicRiskZoneModel).all()
        results = []
        for z in zones:
            bounds = None
            if z.bounds_json:
                try:
                    bounds = json.loads(z.bounds_json)
                except Exception:
                    pass
            results.append({
                "id": z.id,
                "zone_code": z.zone_code,
                "zone_name": z.zone_name,
                "description": z.description,
                "total_segments": z.total_segments,
                "total_length_km": z.total_length_km,
                "avg_vulnerability_score": z.avg_vulnerability_score,
                "dominant_risk_level": z.dominant_risk_level,
                "critical_segment_count": z.critical_segment_count,
                "active_clusters_count": z.active_clusters_count,
                "avg_pressure_psi": z.avg_pressure_psi,
                "bounds": bounds,
                "updated_at": z.updated_at.isoformat() if z.updated_at else None,
                "is_simulated": z.is_simulated,
            })
        return results

    @classmethod
    def get_heatmap(cls, db: Session) -> List[Dict[str, Any]]:
        if db.query(PipelineVulnerabilityProfileModel).count() == 0:
            cls.run_assessment(db)
        segments = PipelineRepository.get_all(db)
        profiles = {p.pipeline_segment_id: {"vulnerability_score": p.vulnerability_score, "vulnerability_level": p.vulnerability_level} for p in db.query(PipelineVulnerabilityProfileModel).all()}
        clusters = cls.get_clusters(db)
        return SpatialAnalysisService.generate_heatmap_points(segments, profiles, clusters)

    @classmethod
    def get_trends(cls, db: Session) -> List[Dict[str, Any]]:
        if db.query(PipelineVulnerabilityProfileModel).count() == 0:
            cls.run_assessment(db)
        profiles = db.query(PipelineVulnerabilityProfileModel).all()
        risks = {r.pipeline_segment_id: r for r in db.query(InfrastructureRiskAssessmentModel).all()}
        results = []
        for p in profiles:
            r = risks.get(p.pipeline_segment_id)
            results.append({
                "pipeline_segment_id": p.pipeline_segment_id,
                "segment_name": p.segment_name,
                "vulnerability_score": p.vulnerability_score,
                "trend_direction": p.trend_direction,
                "deterioration_rate_per_day": p.deterioration_rate_per_day,
                "trend_24h_delta": r.trend_24h_delta if r else 0.0,
                "trend_7d_delta": r.trend_7d_delta if r else 0.0,
                "trend_30d_delta": r.trend_30d_delta if r else 0.0,
                "rapid_degradation": (r.trend_7d_delta >= 2.5) if r else False,
            })
        return results

    @classmethod
    def get_predictions(cls, db: Session) -> List[Dict[str, Any]]:
        if db.query(InfrastructureRiskAssessmentModel).count() == 0:
            cls.run_assessment(db)
        risks = db.query(InfrastructureRiskAssessmentModel).all()
        profiles = {p.pipeline_segment_id: p for p in db.query(PipelineVulnerabilityProfileModel).all()}
        results = []
        for r in risks:
            p = profiles.get(r.pipeline_segment_id)
            drivers = []
            if r.risk_drivers:
                try:
                    drivers = json.loads(r.risk_drivers)
                except Exception:
                    pass
            results.append({
                "pipeline_segment_id": r.pipeline_segment_id,
                "segment_name": p.segment_name if p else r.pipeline_segment_id,
                "current_vulnerability_score": r.vulnerability_score,
                "risk_level": r.risk_level,
                "projected_risk_24h": r.projected_risk_24h,
                "projected_risk_7d": r.projected_risk_7d,
                "projected_risk_30d": r.projected_risk_30d,
                "trend_24h_delta": r.trend_24h_delta,
                "trend_7d_delta": r.trend_7d_delta,
                "trend_30d_delta": r.trend_30d_delta,
                "primary_risk_drivers": drivers,
                "mitigation_urgency": r.mitigation_urgency,
                "hydraulic_deficit_flag": r.hydraulic_deficit_flag,
                "cluster_proximity_m": r.cluster_proximity_m,
            })
        return results

    @classmethod
    def get_inspection_priorities(cls, db: Session, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if db.query(InspectionPriorityRecordModel).count() == 0:
            cls.run_assessment(db)
        query = db.query(InspectionPriorityRecordModel)
        if status:
            query = query.filter(InspectionPriorityRecordModel.status == status.upper())
        records = query.order_by(InspectionPriorityRecordModel.priority_score.desc()).all()
        results = []
        for r in records:
            reasons = []
            if r.reasons:
                try:
                    reasons = json.loads(r.reasons)
                except Exception:
                    pass
            results.append({
                "id": r.id,
                "pipeline_segment_id": r.pipeline_segment_id,
                "segment_name": r.segment_name,
                "priority_score": r.priority_score,
                "priority_level": r.priority_level,
                "status": r.status,
                "target_latitude": r.target_latitude,
                "target_longitude": r.target_longitude,
                "reasons": reasons,
                "suggested_action": r.suggested_action,
                "assigned_rover_id": r.assigned_rover_id,
                "mission_recommendation_id": r.mission_recommendation_id,
                "reviewed_by": r.reviewed_by,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "operator_notes": r.operator_notes,
                "dismissal_reason": r.dismissal_reason,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "is_simulated": r.is_simulated,
            })
        return results

