"""
Leakage Reduction Optimization Service (Task 14)
Models the relationship between nodal pressure modulation and orifice discharge reduction
using Torricelli's Law and emitter flow equations.
"""
from typing import Dict, Any, List, Optional, Tuple
import math

from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult


class LeakageOptimizationService:
    """
    Evaluates leakage sensitivity to operating pressure and calculates verified water savings.
    """

    @classmethod
    def calculate_orifice_leak_rate(
        cls,
        pressure_bar: float,
        orifice_area_m2: float = 0.0004,
        discharge_coeff: float = 0.75,
        water_density_kg_m3: float = 1000.0,
    ) -> float:
        """
        Torricelli's orifice flow formula:
        q_leak = Cd * A * sqrt(2 * P / rho) in m3/s, converted to L/s.
        """
        if pressure_bar <= 0.0 or orifice_area_m2 <= 0.0:
            return 0.0

        p_pascals = pressure_bar * 100000.0
        v_exit_mps = math.sqrt(2.0 * p_pascals / water_density_kg_m3)
        q_m3s = discharge_coeff * orifice_area_m2 * v_exit_mps
        return round(q_m3s * 1000.0, 4)

    @classmethod
    def compare_leakage(
        cls,
        baseline_result: HydraulicSimulationResult,
        candidate_result: HydraulicSimulationResult,
    ) -> Dict[str, Any]:
        """
        Calculates absolute and relative leakage reduction between baseline and candidate configurations.
        """
        base_leak_lps = sum(float(n.leak_flow_lps) for n in baseline_result.nodes.values())
        cand_leak_lps = sum(float(n.leak_flow_lps) for n in candidate_result.nodes.values())

        base_vol_m3 = base_leak_lps * 86.4
        cand_vol_m3 = cand_leak_lps * 86.4

        reduction_m3 = max(0.0, base_vol_m3 - cand_vol_m3)
        reduction_pct = ((base_vol_m3 - cand_vol_m3) / base_vol_m3 * 100.0) if base_vol_m3 > 0.001 else 0.0

        # Node by node breakdown
        node_deltas = {}
        for nid, base_n in baseline_result.nodes.items():
            cand_n = candidate_result.nodes.get(nid)
            b_l = float(base_n.leak_flow_lps)
            c_l = float(cand_n.leak_flow_lps) if cand_n else b_l
            if b_l > 0.001 or c_l > 0.001:
                node_deltas[nid] = {
                    "baseline_leak_lps": round(b_l, 3),
                    "candidate_leak_lps": round(c_l, 3),
                    "delta_leak_lps": round(b_l - c_l, 3),
                    "baseline_pressure_bar": float(base_n.pressure_bar),
                    "candidate_pressure_bar": float(cand_n.pressure_bar) if cand_n else float(base_n.pressure_bar),
                }

        return {
            "baseline_daily_leakage_m3": round(base_vol_m3, 2),
            "candidate_daily_leakage_m3": round(cand_vol_m3, 2),
            "leakage_reduction_m3": round(reduction_m3, 2),
            "leakage_reduction_pct": round(max(0.0, reduction_pct), 2),
            "node_breakdown": node_deltas,
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
        }

