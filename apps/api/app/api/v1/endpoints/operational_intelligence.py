"""
FastAPI Endpoints for Unified Operational Intelligence & Decision Support (Task 12)
Prefix: /api/v1/operational-intelligence
Provides operational overview, prioritized recommendations, human-in-the-loop decisions,
incident correlations, digital twin hydraulic impact what-if, resource planning, and execution history.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from app.database.session import get_db
from app.models.operational_intelligence import (
    OperationalAssessmentModel,
    OperationalRecommendationModel,
    OperationalDecisionModel,
    OperationalPriorityModel,
    OperationalImpactAssessmentModel,
    OperationalEvidenceReferenceModel,
    OperationalExecutionRecordModel,
)
from app.models.pipeline_segment import PipelineSegmentModel
from app.models.ai_detection import AiDetectionModel
from app.models.infrastructure_intelligence import SpatialIncidentClusterModel
from app.models.user import UserModel
from app.core.auth import require_roles, require_viewer, require_operator
from app.schemas.operational_intelligence import (
    OperationalOverviewResponse,
    OperationalAssessmentResponse,
    OperationalRecommendationItem,
    OperationalRecommendationDetail,
    OperationalRecommendationListResponse,
    OperationalDecisionRequest,
    OperationalDecisionResponse,
    OperationalPriorityItem,
    OperationalPriorityListResponse,
    OperationalImpactItem,
    OperationalImpactAnalysisRequest,
    OperationalEvidenceItem,
    OperationalEvidenceListResponse,
    IncidentCorrelationItem,
    IncidentCorrelationListResponse,
    ResourcePlanningItem,
    ResourcePlanningResponse,
    OperationalExecutionItem,
    OperationalExecutionHistoryResponse,
)
from app.services.operational_intelligence.operational_intelligence_service import OperationalIntelligenceService
from app.services.operational_intelligence.operational_decision_service import OperationalDecisionService
from app.services.operational_intelligence.incident_correlation_service import IncidentCorrelationService
from app.services.operational_intelligence.operational_hydraulic_impact_service import OperationalHydraulicImpactService
from app.services.operational_intelligence.operational_resource_planning_service import OperationalResourcePlanningService

router = APIRouter()


@router.get("/overview", response_model=OperationalOverviewResponse)
def get_operational_overview(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns aggregated operational overview metrics, counts, and latest system assessment status.
    """
    return OperationalIntelligenceService.get_operational_overview(db)


@router.get("/assessments", response_model=List[OperationalAssessmentResponse])
def list_assessments(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists historical operational assessments.
    """
    query = db.query(OperationalAssessmentModel).order_by(OperationalAssessmentModel.assessed_at.desc())
    records = query.offset(offset).limit(limit).all()
    results = []
    for r in records:
        results.append(OperationalAssessmentResponse(
            id=r.id,
            assessment_name=r.assessment_name,
            total_recommendations=r.total_recommendations,
            immediate_action_count=r.immediate_action_count,
            urgent_leak_count=r.urgent_leak_count,
            preventive_count=r.preventive_count,
            critical_segments_analyzed=r.critical_segments_analyzed,
            overall_network_urgency=r.overall_network_urgency,
            summary=json.loads(r.summary_json) if r.summary_json else {},
            assessed_at=r.assessed_at.isoformat() if r.assessed_at else None,
            is_simulated=r.is_simulated,
            source=r.source,
        ))
    return results


@router.get("/assessments/latest", response_model=Optional[OperationalAssessmentResponse])
def get_latest_assessment(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves the most recent operational assessment. If none exists, runs an assessment automatically.
    """
    assessment = db.query(OperationalAssessmentModel).order_by(
        OperationalAssessmentModel.assessed_at.desc()
    ).first()
    if not assessment:
        assessment = OperationalIntelligenceService.run_operational_assessment(db)

    return OperationalAssessmentResponse(
        id=assessment.id,
        assessment_name=assessment.assessment_name,
        total_recommendations=assessment.total_recommendations,
        immediate_action_count=assessment.immediate_action_count,
        urgent_leak_count=assessment.urgent_leak_count,
        preventive_count=assessment.preventive_count,
        critical_segments_analyzed=assessment.critical_segments_analyzed,
        overall_network_urgency=assessment.overall_network_urgency,
        summary=json.loads(assessment.summary_json) if assessment.summary_json else {},
        assessed_at=assessment.assessed_at.isoformat() if assessment.assessed_at else None,
        is_simulated=assessment.is_simulated,
        source=assessment.source,
    )


@router.post("/assessments/run", response_model=OperationalAssessmentResponse)
def trigger_operational_assessment(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Triggers an on-demand operational intelligence assessment, evaluating all live network segments.
    """
    assessment = OperationalIntelligenceService.run_operational_assessment(db)
    return OperationalAssessmentResponse(
        id=assessment.id,
        assessment_name=assessment.assessment_name,
        total_recommendations=assessment.total_recommendations,
        immediate_action_count=assessment.immediate_action_count,
        urgent_leak_count=assessment.urgent_leak_count,
        preventive_count=assessment.preventive_count,
        critical_segments_analyzed=assessment.critical_segments_analyzed,
        overall_network_urgency=assessment.overall_network_urgency,
        summary=json.loads(assessment.summary_json) if assessment.summary_json else {},
        assessed_at=assessment.assessed_at.isoformat() if assessment.assessed_at else None,
        is_simulated=assessment.is_simulated,
        source=assessment.source,
    )


@router.get("/recommendations", response_model=OperationalRecommendationListResponse)
def list_recommendations(
    category: Optional[str] = Query(None, description="Filter by recommendation category"),
    status: Optional[str] = Query(None, description="Filter by lifecycle status"),
    priority_tier: Optional[str] = Query(None, description="Filter by priority tier"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists operational recommendations with multi-criteria filtering and priority sorting.
    """
    query = db.query(OperationalRecommendationModel)
    if category:
        query = query.filter(OperationalRecommendationModel.category == category)
    if status:
        query = query.filter(OperationalRecommendationModel.status == status)
    if priority_tier:
        query = query.filter(OperationalRecommendationModel.priority_tier == priority_tier)

    total = query.count()
    if total == 0:
        # Seed initial assessment if empty
        OperationalIntelligenceService.run_operational_assessment(db)
        query = db.query(OperationalRecommendationModel)
        total = query.count()

    items = query.order_by(OperationalRecommendationModel.priority_score.desc()).offset(offset).limit(limit).all()

    resp_items = []
    for r in items:
        resp_items.append(OperationalRecommendationItem(
            id=r.id,
            assessment_id=r.assessment_id,
            category=r.category,
            pipeline_segment_id=r.pipeline_segment_id,
            segment_name=r.segment_name,
            associated_incident_id=r.associated_incident_id,
            associated_cluster_id=r.associated_cluster_id,
            risk_severity=r.risk_severity,
            priority_score=r.priority_score,
            priority_tier=r.priority_tier,
            recommended_action=r.recommended_action,
            action_details=r.action_details,
            why_explanation=r.why_explanation,
            what_missing=r.what_missing,
            expected_impact=r.expected_impact,
            contributing_factors=json.loads(r.contributing_factors_json) if r.contributing_factors_json else {},
            evidence_sources=json.loads(r.evidence_sources_json) if r.evidence_sources_json else [],
            resource_requirements=json.loads(r.resource_requirements_json) if r.resource_requirements_json else {},
            confidence=r.confidence,
            data_completeness_pct=r.data_completeness_pct,
            uncertainty_margin=r.uncertainty_margin,
            status=r.status,
            approval_status=r.approval_status,
            assigned_rover_id=r.assigned_rover_id,
            dispatched_mission_id=r.dispatched_mission_id,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
            expires_at=r.expires_at.isoformat() if r.expires_at else None,
            is_simulated=r.is_simulated,
            source=r.source,
        ))

    return OperationalRecommendationListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=resp_items,
    )


@router.get("/recommendations/{id}", response_model=OperationalRecommendationDetail)
def get_recommendation_detail(
    id: str = Path(..., description="Operational recommendation ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns full details for a specific recommendation, including linked evidence and impact analysis.
    """
    rec = db.query(OperationalRecommendationModel).filter(OperationalRecommendationModel.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation '{id}' not found.")

    evidences = db.query(OperationalEvidenceReferenceModel).filter(
        OperationalEvidenceReferenceModel.recommendation_id == id
    ).all()

    evidence_items = []
    for e in evidences:
        evidence_items.append(OperationalEvidenceItem(
            id=e.id,
            recommendation_id=e.recommendation_id,
            evidence_type=e.evidence_type,
            source_module=e.source_module,
            source_table=e.source_table,
            source_record_id=e.source_record_id,
            metric_name=e.metric_name,
            metric_value=e.metric_value,
            metric_unit=e.metric_unit,
            confidence_score=e.confidence_score,
            evidence_summary=e.evidence_summary,
            payload=json.loads(e.payload_json) if e.payload_json else {},
            recorded_at=e.recorded_at.isoformat() if e.recorded_at else None,
            is_simulated=e.is_simulated,
            source=e.source,
        ))

    impact = db.query(OperationalImpactAssessmentModel).filter(
        OperationalImpactAssessmentModel.recommendation_id == id
    ).first()

    impact_item = None
    if impact:
        impact_item = OperationalImpactItem(
            id=impact.id,
            recommendation_id=impact.recommendation_id,
            pipeline_segment_id=impact.pipeline_segment_id,
            scenario_id=impact.scenario_id,
            estimated_water_loss_m3_day=impact.estimated_water_loss_m3_day,
            is_water_loss_measured=impact.is_water_loss_measured,
            service_disruption_risk=impact.service_disruption_risk,
            affected_nodes_count=impact.affected_nodes_count,
            affected_population_estimate=impact.affected_population_estimate,
            hydraulic_headloss_delta_m=impact.hydraulic_headloss_delta_m,
            min_pressure_drop_bar=impact.min_pressure_drop_bar,
            estimated_inspection_distance_m=impact.estimated_inspection_distance_m,
            estimated_mission_energy_pct=impact.estimated_mission_energy_pct,
            estimated_inspection_duration_min=impact.estimated_inspection_duration_min,
            cost_impact_display=impact.cost_impact_display,
            data_quality_rating=impact.data_quality_rating,
            assumptions=json.loads(impact.assumptions_json) if impact.assumptions_json else {},
            uncertainty_margin_pct=impact.uncertainty_margin_pct,
            assessed_at=impact.assessed_at.isoformat() if impact.assessed_at else None,
            is_simulated=impact.is_simulated,
            source=impact.source,
        )

    return OperationalRecommendationDetail(
        id=rec.id,
        assessment_id=rec.assessment_id,
        category=rec.category,
        pipeline_segment_id=rec.pipeline_segment_id,
        segment_name=rec.segment_name,
        associated_incident_id=rec.associated_incident_id,
        associated_cluster_id=rec.associated_cluster_id,
        risk_severity=rec.risk_severity,
        priority_score=rec.priority_score,
        priority_tier=rec.priority_tier,
        recommended_action=rec.recommended_action,
        action_details=rec.action_details,
        why_explanation=rec.why_explanation,
        what_missing=rec.what_missing,
        expected_impact=rec.expected_impact,
        contributing_factors=json.loads(rec.contributing_factors_json) if rec.contributing_factors_json else {},
        evidence_sources=json.loads(rec.evidence_sources_json) if rec.evidence_sources_json else [],
        resource_requirements=json.loads(rec.resource_requirements_json) if rec.resource_requirements_json else {},
        confidence=rec.confidence,
        data_completeness_pct=rec.data_completeness_pct,
        uncertainty_margin=rec.uncertainty_margin,
        status=rec.status,
        approval_status=rec.approval_status,
        assigned_rover_id=rec.assigned_rover_id,
        dispatched_mission_id=rec.dispatched_mission_id,
        created_at=rec.created_at.isoformat() if rec.created_at else None,
        updated_at=rec.updated_at.isoformat() if rec.updated_at else None,
        expires_at=rec.expires_at.isoformat() if rec.expires_at else None,
        is_simulated=rec.is_simulated,
        source=rec.source,
        evidences=evidence_items,
        impact_assessment=impact_item,
    )


@router.post("/recommendations/{id}/approve", response_model=OperationalDecisionResponse)
def approve_recommendation(
    id: str = Path(..., description="Recommendation ID"),
    payload: OperationalDecisionRequest = ...,
    current_user: UserModel = Depends(require_roles(["OPERATOR", "ENGINEER", "ADMINISTRATOR"])),
    db: Session = Depends(get_db),
):
    """
    Approves an operational recommendation and triggers virtual rover mission dispatch if applicable.
    Enforces verified human operator identity and role authorization.
    """
    res = OperationalDecisionService.process_decision(
        db=db,
        recommendation_id=id,
        decision_type="APPROVED",
        decision_reason=payload.decision_reason,
        operator_id=current_user.id,
        operator_name=current_user.full_name or current_user.username,
        allocated_rover_id=payload.allocated_resource_id,
        override_priority=payload.override_priority,
    )
    return OperationalDecisionResponse(**res)


@router.post("/recommendations/{id}/reject", response_model=OperationalDecisionResponse)
def reject_recommendation(
    id: str = Path(..., description="Recommendation ID"),
    payload: OperationalDecisionRequest = ...,
    current_user: UserModel = Depends(require_roles(["OPERATOR", "ENGINEER", "ADMINISTRATOR"])),
    db: Session = Depends(get_db),
):
    """
    Rejects an operational recommendation with mandatory operator justification.
    Enforces verified human operator identity and role authorization.
    """
    res = OperationalDecisionService.process_decision(
        db=db,
        recommendation_id=id,
        decision_type="REJECTED",
        decision_reason=payload.decision_reason,
        operator_id=current_user.id,
        operator_name=current_user.full_name or current_user.username,
    )
    return OperationalDecisionResponse(**res)


@router.get("/recommendations/{id}/evidence", response_model=OperationalEvidenceListResponse)
def get_recommendation_evidence(
    id: str = Path(..., description="Recommendation ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns all supporting multi-system evidence linked to an operational recommendation.
    """
    evidences = db.query(OperationalEvidenceReferenceModel).filter(
        OperationalEvidenceReferenceModel.recommendation_id == id
    ).all()

    items = []
    for e in evidences:
        items.append(OperationalEvidenceItem(
            id=e.id,
            recommendation_id=e.recommendation_id,
            evidence_type=e.evidence_type,
            source_module=e.source_module,
            source_table=e.source_table,
            source_record_id=e.source_record_id,
            metric_name=e.metric_name,
            metric_value=e.metric_value,
            metric_unit=e.metric_unit,
            confidence_score=e.confidence_score,
            evidence_summary=e.evidence_summary,
            payload=json.loads(e.payload_json) if e.payload_json else {},
            recorded_at=e.recorded_at.isoformat() if e.recorded_at else None,
            is_simulated=e.is_simulated,
            source=e.source,
        ))

    return OperationalEvidenceListResponse(
        total=len(items),
        recommendation_id=id,
        items=items,
    )


@router.get("/recommendations/{id}/impact", response_model=Optional[OperationalImpactItem])
def get_recommendation_impact(
    id: str = Path(..., description="Recommendation ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Retrieves the operational impact assessment for the given recommendation.
    """
    impact = db.query(OperationalImpactAssessmentModel).filter(
        OperationalImpactAssessmentModel.recommendation_id == id
    ).first()
    if not impact:
        return None

    return OperationalImpactItem(
        id=impact.id,
        recommendation_id=impact.recommendation_id,
        pipeline_segment_id=impact.pipeline_segment_id,
        scenario_id=impact.scenario_id,
        estimated_water_loss_m3_day=impact.estimated_water_loss_m3_day,
        is_water_loss_measured=impact.is_water_loss_measured,
        service_disruption_risk=impact.service_disruption_risk,
        affected_nodes_count=impact.affected_nodes_count,
        affected_population_estimate=impact.affected_population_estimate,
        hydraulic_headloss_delta_m=impact.hydraulic_headloss_delta_m,
        min_pressure_drop_bar=impact.min_pressure_drop_bar,
        estimated_inspection_distance_m=impact.estimated_inspection_distance_m,
        estimated_mission_energy_pct=impact.estimated_mission_energy_pct,
        estimated_inspection_duration_min=impact.estimated_inspection_duration_min,
        cost_impact_display=impact.cost_impact_display,
        data_quality_rating=impact.data_quality_rating,
        assumptions=json.loads(impact.assumptions_json) if impact.assumptions_json else {},
        uncertainty_margin_pct=impact.uncertainty_margin_pct,
        assessed_at=impact.assessed_at.isoformat() if impact.assessed_at else None,
        is_simulated=impact.is_simulated,
        source=impact.source,
    )


@router.post("/impact/analyze", response_model=Dict[str, Any])
def run_what_if_impact_analysis(
    payload: OperationalImpactAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Performs on-demand digital twin hydraulic what-if analysis for candidate leak or burst scenarios.
    """
    seg = db.query(PipelineSegmentModel).filter(PipelineSegmentModel.id == payload.pipeline_segment_id).first()
    nominal_pressure = (float(seg.nominal_pressure_psi) / 14.5038) if seg and seg.nominal_pressure_psi else 4.2

    res = OperationalHydraulicImpactService.evaluate_leak_impact(
        db=db,
        pipeline_segment_id=payload.pipeline_segment_id,
        leak_orifice_diameter_mm=payload.leak_orifice_diameter_mm or 15.0,
        nominal_pressure_bar=nominal_pressure,
        demand_multiplier=payload.demand_multiplier or 1.0,
        duration_hours=payload.duration_hours or 24,
    )
    return res


@router.get("/correlations", response_model=IncidentCorrelationListResponse)
def get_incident_correlations(
    pipeline_segment_id: Optional[str] = Query(None, description="Filter by primary segment ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Evaluates cross-system incident correlations across acoustic, pressure, moisture, and spatial clusters.
    """
    segments = db.query(PipelineSegmentModel).all()
    detections = db.query(AiDetectionModel).all()
    clusters = db.query(SpatialIncidentClusterModel).all()

    det_dicts = [
        {
            "id": d.id,
            "pipeline_segment_id": d.pipeline_segment_id,
            "anomaly_score": d.anomaly_score,
            "classification": d.classification,
        }
        for d in detections
    ]
    cluster_dicts = [
        {
            "id": c.id,
            "cluster_name": c.cluster_name,
            "centroid_lat": c.centroid_lat,
            "centroid_lng": c.centroid_lng,
            "radius_m": c.radius_m,
            "incident_count": c.incident_count,
            "dominant_material": c.dominant_material,
            "hotspot_intensity": c.hotspot_intensity,
            "affected_segment_ids": json.loads(c.affected_segment_ids) if c.affected_segment_ids else [],
        }
        for c in clusters
    ]

    all_corrs = []
    target_segments = [s for s in segments if s.id == pipeline_segment_id] if pipeline_segment_id else segments

    for seg in target_segments:
        corrs = IncidentCorrelationService.correlate_events(
            primary_segment_id=str(seg.id),
            primary_segment_name=str(seg.name),
            detections=det_dicts,
            spatial_clusters=cluster_dicts,
        )
        for c in corrs:
            all_corrs.append(IncidentCorrelationItem(**c))

    return IncidentCorrelationListResponse(
        total=len(all_corrs),
        items=all_corrs,
    )


@router.get("/priorities", response_model=OperationalPriorityListResponse)
def get_operational_priorities(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns prioritized operational queue with separate criteria breakdown and ranking positions.
    """
    priorities = db.query(OperationalPriorityModel).order_by(
        OperationalPriorityModel.rank_position.asc()
    ).limit(limit).all()

    items = []
    for p in priorities:
        items.append(OperationalPriorityItem(
            id=p.id,
            recommendation_id=p.recommendation_id,
            pipeline_segment_id=p.pipeline_segment_id,
            rank_position=p.rank_position,
            composite_priority_score=p.composite_priority_score,
            incident_severity_component=p.incident_severity_component,
            vulnerability_component=p.vulnerability_component,
            asset_health_component=p.asset_health_component,
            hydraulic_impact_component=p.hydraulic_impact_component,
            service_criticality_component=p.service_criticality_component,
            recurrence_component=p.recurrence_component,
            confidence_weight=p.confidence_weight,
            weights_version=p.weights_version,
            weights_applied=json.loads(p.weights_applied_json) if p.weights_applied_json else {},
            reassessment_counter=p.reassessment_counter,
            last_ranked_at=p.last_ranked_at.isoformat() if p.last_ranked_at else None,
        ))

    return OperationalPriorityListResponse(total=len(items), items=items)


@router.get("/resource-planning", response_model=ResourcePlanningResponse)
def get_resource_planning(
    pipeline_segment_id: Optional[str] = Query(None, description="Optional target segment ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Evaluates virtual rover fleet suitability, thermal safety, battery gates, and scheduling feasibility.
    """
    segments = db.query(PipelineSegmentModel).all()
    if pipeline_segment_id:
        segments = [s for s in segments if s.id == pipeline_segment_id]

    items = []
    for seg in segments:
        plan = OperationalResourcePlanningService.evaluate_resources_for_target(
            db=db,
            pipeline_segment_id=str(seg.id),
            segment_name=str(seg.name),
            estimated_segment_length_m=float(seg.length_m or 1000.0),
        )
        items.append(ResourcePlanningItem(**plan))

    return ResourcePlanningResponse(
        total_resources_evaluated=len(items),
        items=items,
    )


@router.get("/decisions", response_model=List[Dict[str, Any]])
def get_operator_decisions(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns immutable audit log of operator decisions with SHA-256 signatures.
    """
    decisions = db.query(OperationalDecisionModel).order_by(
        OperationalDecisionModel.decision_timestamp.desc()
    ).limit(limit).all()

    results = []
    for d in decisions:
        results.append({
            "id": d.id,
            "recommendation_id": d.recommendation_id,
            "decision_type": d.decision_type,
            "decision_reason": d.decision_reason,
            "operator_id": d.operator_id,
            "operator_name": d.operator_name,
            "override_priority": d.override_priority,
            "allocated_resource_id": d.allocated_resource_id,
            "resulting_mission_id": d.resulting_mission_id,
            "decision_timestamp": d.decision_timestamp.isoformat() if d.decision_timestamp else None,
            "audit_hash": d.audit_hash,
            "is_simulated": d.is_simulated,
            "source": d.source,
        })
    return results


@router.get("/execution-history", response_model=OperationalExecutionHistoryResponse)
def get_execution_history(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns execution history tracking inspection progress, rover telemetry, and findings.
    """
    records = db.query(OperationalExecutionRecordModel).order_by(
        OperationalExecutionRecordModel.last_updated_at.desc()
    ).limit(limit).all()

    items = []
    for r in records:
        items.append(OperationalExecutionItem(
            id=r.id,
            recommendation_id=r.recommendation_id,
            decision_id=r.decision_id,
            mission_id=r.mission_id,
            assigned_rover_id=r.assigned_rover_id,
            execution_stage=r.execution_stage,
            start_time=r.start_time.isoformat() if r.start_time else None,
            end_time=r.end_time.isoformat() if r.end_time else None,
            distance_inspected_m=r.distance_inspected_m,
            energy_consumed_pct=r.energy_consumed_pct,
            findings_summary=r.findings_summary,
            leak_confirmed=r.leak_confirmed,
            last_updated_at=r.last_updated_at.isoformat() if r.last_updated_at else None,
        ))

    return OperationalExecutionHistoryResponse(total=len(items), items=items)

