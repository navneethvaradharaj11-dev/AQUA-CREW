"""
Pump Operating Point Optimization Service (Task 14)
Evaluates pump characteristic curves, affinity law scaling, electrical energy efficiency,
tank operating limits, and switching penalties to determine optimal pump speeds and schedules.
"""
from typing import Dict, Any, List, Optional, Tuple
import math

from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult


DEFAULT_PUMP_CURVE = {"h0": 65.0, "a": 0.00015, "b": 2.0}  # H = 65 - 0.00015 * Q^2 (Q in L/s, H in m)
MIN_PUMP_SPEED = 0.50
MAX_PUMP_SPEED = 1.20
NOMINAL_PUMP_SPEED = 1.00


class PumpOptimizationService:
    """
    Analyzes and optimizes booster pump operations within hydraulic and electrical constraints.
    """
    NOMINAL_PUMP_SPEED = NOMINAL_PUMP_SPEED

    @classmethod
    def evaluate_pump_head(
        cls,
        flow_lps: float,
        speed: float = NOMINAL_PUMP_SPEED,
        curve_coeffs: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculates pump head in meters based on affinity-scaled head-discharge curve:
        H(Q, s) = s^2 * h0 - a * (Q / s)^b
        """
        coeffs = curve_coeffs or DEFAULT_PUMP_CURVE
        h0 = coeffs.get("h0", 65.0)
        a = coeffs.get("a", 0.00015)
        b = coeffs.get("b", 2.0)

        s_clamped = max(MIN_PUMP_SPEED, min(MAX_PUMP_SPEED, float(speed)))
        q_scaled = abs(flow_lps) / s_clamped
        head = (s_clamped ** 2) * h0 - a * (q_scaled ** b)
        return max(0.0, float(head))

    @classmethod
    def calculate_pump_power_kw(
        cls,
        flow_lps: float,
        head_m: float,
        rated_power_kw: float = 45.0,
        speed: float = NOMINAL_PUMP_SPEED,
        wire_to_water_efficiency: float = 0.72,
    ) -> Tuple[float, float, float]:
        """
        Calculates:
          1. Hydraulic power: P_hyd = rho * g * Q * H (kW)
          2. Electrical power with affinity scaling: P_elec = rated_kw * s^3
          3. Operating efficiency: eta = P_hyd / P_elec
        """
        s = max(MIN_PUMP_SPEED, min(MAX_PUMP_SPEED, float(speed)))
        q_m3s = abs(flow_lps) / 1000.0
        p_hyd_kw = 9.81 * q_m3s * max(0.0, head_m)

        # Electrical power scales as cube of speed (Affinity Law)
        p_elec_kw = rated_power_kw * (s ** 3)
        actual_eff = (p_hyd_kw / p_elec_kw) if p_elec_kw > 0 else wire_to_water_efficiency
        efficiency = min(0.95, max(0.10, actual_eff))

        return round(p_hyd_kw, 3), round(p_elec_kw, 3), round(efficiency, 3)

    @classmethod
    def evaluate_switching_penalty(
        cls,
        hourly_schedule: List[int],
        max_allowed_switches: int = 4,
        penalty_per_switch: float = 5.0,
    ) -> float:
        """
        Computes mechanical wear penalty for excessive pump switching (starts/stops).
        """
        if not hourly_schedule or len(hourly_schedule) < 2:
            return 0.0

        switches = 0
        for i in range(1, len(hourly_schedule)):
            if hourly_schedule[i] != hourly_schedule[i - 1]:
                switches += 1

        excess = max(0, switches - max_allowed_switches)
        return float(excess * penalty_per_switch)

    @classmethod
    def check_tank_limits(
        cls,
        initial_level_m: float,
        hourly_net_inflow_lps: List[float],
        tank_diameter_m: float = 18.0,
        min_level_m: float = 1.5,
        max_level_m: float = 12.0,
        timestep_seconds: float = 3600.0,
    ) -> Tuple[bool, List[float], List[str]]:
        """
        Verifies that tank levels remain within safe operational boundaries [min_level, max_level].
        """
        area_m2 = math.pi * ((tank_diameter_m / 2.0) ** 2)
        current_lvl = initial_level_m
        levels = [round(current_lvl, 2)]
        violations = []

        for hour_idx, net_q_lps in enumerate(hourly_net_inflow_lps):
            net_vol_m3 = (net_q_lps / 1000.0) * timestep_seconds
            delta_h = net_vol_m3 / area_m2
            current_lvl += delta_h
            levels.append(round(current_lvl, 2))

            if current_lvl < min_level_m:
                violations.append(f"Hour {hour_idx + 1}: Tank depleted below minimum safe reserve ({current_lvl:.2f} m < {min_level_m} m)")
            elif current_lvl > max_level_m:
                violations.append(f"Hour {hour_idx + 1}: Tank overflow exceeded ({current_lvl:.2f} m > {max_level_m} m)")

        is_valid = len(violations) == 0
        return is_valid, levels, violations
