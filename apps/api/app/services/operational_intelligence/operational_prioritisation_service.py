"""
Operational Prioritisation Service (Task 12 - Phase 5)
Provides deterministic, explainable multi-criteria priority ranking for operational recommendations.
Strictly separates failure likelihood, consequence criticality, evidence confidence,
and operational resource feasibility (resource availability does not alter underlying risk).
"""
from typing import Dict, Any, List, Optional
import math


class OperationalPrioritisationService:
    VERSION = "v1.0.0-multi-criteria-pareto"

    # Default calibrated multi-factor weights (sum = 1.0)
    DEFAULT_WEIGHTS = {
        "incident_severity": 0.25,
        "vulnerability": 0.20,
        "asset_health_deficit": 0.20,
        "hydraulic_impact": 0.15,
        "service_criticality": 0.12,
        "recurrence": 0.08,
    }

    @classmethod
    def calculate_priority(
        cls,
        incident_severity: float,          # 0.0 to 100.0
        vulnerability_score: float,        # 0.0 to 100.0 (from Task 11)
        health_score: float,               # 0.0 to 100.0 (from Task 09; deficit = 100 - health)
        hydraulic_impact: float,           # 0.0 to 100.0 (from Task 10)
        diameter_mm: int,                  # Pipe diameter in mm (consequence driver)
        historical_incident_count: int,    # Previous leaks/alarms
        confidence: float = 0.85,          # 0.0 to 1.0 evidence confidence
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates a deterministic composite priority score with separate factor attribution.
        """
        weights = custom_weights or cls.DEFAULT_WEIGHTS.copy()
        
        # Normalize weights if sum != 1.0
        total_w = sum(weights.values())
        if total_w > 0 and not math.isclose(total_w, 1.0, rel_tol=1e-5):
            weights = {k: v / total_w for k, v in weights.items()}

        # 1. Clamp inputs to safe bounds
        inc_sev = max(0.0, min(100.0, float(incident_severity)))
        vuln = max(0.0, min(100.0, float(vulnerability_score)))
        
        # 2. Health deficit: poor health (e.g. 20) yields high deficit (80)
        clamped_health = max(0.0, min(100.0, float(health_score)))
        health_deficit = 100.0 - clamped_health
        
        # 3. Hydraulic impact
        hyd = max(0.0, min(100.0, float(hydraulic_impact)))
        
        # 4. Service Criticality (based on diameter and transmission consequence)
        if diameter_mm >= 600:
            crit = 100.0
        elif diameter_mm >= 450:
            crit = 80.0
        elif diameter_mm >= 300:
            crit = 60.0
        elif diameter_mm >= 150:
            crit = 40.0
        else:
            crit = 20.0
            
        # 5. Recurrence factor: saturate at 5+ historical incidents
        recurrence = min(100.0, float(historical_incident_count) * 20.0)

        # 6. Linear composite scoring
        raw_composite = (
            weights["incident_severity"] * inc_sev +
            weights["vulnerability"] * vuln +
            weights["asset_health_deficit"] * health_deficit +
            weights["hydraulic_impact"] * hyd +
            weights["service_criticality"] * crit +
            weights["recurrence"] * recurrence
        )

        # 7. Confidence moderation: lower confidence introduces a conservative discount towards neutral (50)
        conf = max(0.2, min(1.0, float(confidence)))
        # Blended with neutral 50: Priority_adj = conf * raw + (1 - conf) * 50
        blended_score = conf * raw_composite + (1.0 - conf) * 50.0
        final_score = round(max(0.0, min(100.0, blended_score)), 2)

        # 8. Deterministic Priority Tier Mapping
        if final_score >= 80.0:
            priority_tier = "CRITICAL_IMMEDIATE"
        elif final_score >= 65.0:
            priority_tier = "URGENT"
        elif final_score >= 50.0:
            priority_tier = "HIGH_PRIORITY"
        elif final_score >= 30.0:
            priority_tier = "ROUTINE"
        else:
            priority_tier = "DEFERRED"

        return {
            "composite_priority_score": final_score,
            "priority_tier": priority_tier,
            "components": {
                "incident_severity": round(inc_sev, 2),
                "vulnerability": round(vuln, 2),
                "asset_health_deficit": round(health_deficit, 2),
                "hydraulic_impact": round(hyd, 2),
                "service_criticality": round(crit, 2),
                "recurrence": round(recurrence, 2),
            },
            "weights_applied": {k: round(v, 4) for k, v in weights.items()},
            "weights_version": cls.VERSION,
            "confidence_weight": conf,
            "raw_composite": round(raw_composite, 2),
        }

    @classmethod
    def rank_recommendations(cls, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts recommendations deterministically in descending priority score order,
        breaking ties by incident severity, vulnerability, and creation timestamp.
        """
        def sort_key(item: Dict[str, Any]):
            score = item.get("priority_score", 0.0)
            factors = item.get("contributing_factors", {})
            inc = factors.get("incident_severity", 0.0)
            vuln = factors.get("vulnerability", 0.0)
            created = item.get("created_at") or ""
            return (-score, -inc, -vuln, str(created))

        sorted_items = sorted(items, key=sort_key)
        for rank, item in enumerate(sorted_items, start=1):
            item["rank_position"] = rank
        return sorted_items

