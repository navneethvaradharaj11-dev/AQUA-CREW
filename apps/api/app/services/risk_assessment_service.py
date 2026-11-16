"""
Rule-Based Severity and Risk Assessment Service
Determines risk category (LOW, MODERATE, HIGH, CRITICAL) and generates transparent explanations.
"""
from typing import Dict, Any, Tuple


class RiskAssessmentService:
    @staticmethod
    def estimate_flow_loss(classification: str, delta_p_bar: float, diameter_mm: float) -> float:
        """
        Estimates water loss in litres per hour based on hydraulic orifice model:
        Q ~ C_d * A * sqrt(2 * delta_P / rho).
        """
        if classification == "NORMAL":
            return 0.0

        # Empirical synthetic orifice sizing factor based on classification
        leak_diam_mm = {
            "LOW_LEAK_PROBABILITY": 1.5,
            "MEDIUM_LEAK_PROBABILITY": 4.5,
            "HIGH_LEAK_PROBABILITY": 12.0,
        }.get(classification, 2.0)

        # Orifice area in m^2
        area_m2 = 3.14159 * ((leak_diam_mm / 1000.0) / 2.0) ** 2
        # Pressure differential in Pascals (1 bar = 100,000 Pa)
        delta_p_pa = max(delta_p_bar, 0.2) * 100000.0
        # Water velocity: v = sqrt(2 * dP / rho), rho = 1000 kg/m^3
        v = (2.0 * delta_p_pa / 1000.0) ** 0.5
        # Discharge coefficient Cd ~ 0.62
        flow_m3_s = 0.62 * area_m2 * v
        flow_litres_per_hour = flow_m3_s * 1000.0 * 3600.0

        return round(float(flow_litres_per_hour), 1)

    @staticmethod
    def evaluate_risk(
        classification: str,
        confidence: float,
        anomaly_score: float,
        features: Dict[str, float],
        pipe_meta: Dict[str, Any],
    ) -> Tuple[str, float, str]:
        """
        Calculates risk level (LOW, MODERATE, HIGH, CRITICAL), estimated flow loss,
        and provides an auditable explanation.
        """
        delta_p = features.get("pressure_deviation_bar", 0.0)
        diam = features.get("pipe_diameter_mm", 300.0)
        loss_lph = RiskAssessmentService.estimate_flow_loss(classification, delta_p, diam)
        is_trunk_line = pipe_meta.get("category", "").lower() in ["primary", "trunk"]

        reasons = []

        if classification == "NORMAL" and anomaly_score < 0.40:
            risk = "LOW"
            reasons.append("Nominal acoustic and hydraulic telemetry within standard operational tolerances.")
            reasons.append("Zero anomalous pressure gradient detected.")

        elif classification == "HIGH_LEAK_PROBABILITY" or (loss_lph > 2000.0 and is_trunk_line):
            if is_trunk_line or loss_lph > 3000.0 or delta_p > 1.2:
                risk = "CRITICAL"
                reasons.append(f"Major acoustic resonance detected on critical pipeline segment ({pipe_meta.get('name', 'Trunk')}).")
                reasons.append(f"Severe pressure drop of {delta_p:.2f} bar with estimated water loss of {loss_lph:.0f} L/h.")
                reasons.append("Immediate virtual inspection mission dispatch and operator intervention recommended.")
            else:
                risk = "HIGH"
                reasons.append("Strong acoustic turbulence and significant moisture elevation.")
                reasons.append(f"Estimated water loss of {loss_lph:.0f} L/h exceeds standard threshold.")

        elif classification == "MEDIUM_LEAK_PROBABILITY" or anomaly_score >= 0.65 or loss_lph >= 500.0:
            risk = "MODERATE"
            reasons.append(f"Moderate broadband acoustic hiss detected with {confidence * 100:.1f}% model confidence.")
            reasons.append(f"Estimated water loss of {loss_lph:.0f} L/h. Priority inspection scheduled within 24 hours.")

        else:
            risk = "LOW"
            reasons.append(f"Minor acoustic perturbation or sensor drift detected ({classification}).")
            reasons.append("Hydraulic loss is negligible; continuous telemetry monitoring active.")

        explanation = " | ".join(reasons)
        return risk, loss_lph, explanation
