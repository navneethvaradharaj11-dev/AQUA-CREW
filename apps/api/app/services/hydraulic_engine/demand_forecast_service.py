"""
Water Demand Forecast Integration Service (Task 14)
Forecasts time-varying diurnal demand profiles with statistical confidence bands
for multi-period network optimization.
"""
from typing import Dict, Any, List, Optional
import math

from app.services.hydraulic_engine.wntr_engine import DEFAULT_DIURNAL_PATTERN


class DemandForecastService:
    """
    Produces diurnal demand forecasts with uncertainty bounds for extended-period optimization.
    """

    @classmethod
    def generate_diurnal_forecast(
        cls,
        base_demand_lps: float,
        duration_hours: int = 24,
        demand_multiplier: float = 1.0,
        uncertainty_pct: float = 5.0,
        historical_readings: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Generates hourly expected demand with 95% confidence intervals (mean +/- 1.96 * sigma).
        """
        pattern = DEFAULT_DIURNAL_PATTERN
        pattern_len = len(pattern)

        hourly_forecast = []
        for h in range(duration_hours):
            diurnal_coeff = pattern[h % pattern_len]

            # If historical readings supplied, apply exponential smoothing blend
            if historical_readings and len(historical_readings) > h:
                hist_val = historical_readings[h]
                expected_q = 0.7 * (base_demand_lps * diurnal_coeff * demand_multiplier) + 0.3 * hist_val
            else:
                expected_q = base_demand_lps * diurnal_coeff * demand_multiplier

            sigma = expected_q * (uncertainty_pct / 100.0)
            ci_lower = max(0.0, expected_q - 1.96 * sigma)
            ci_upper = expected_q + 1.96 * sigma

            hourly_forecast.append({
                "hour_offset": h,
                "hour_label": f"{h:02d}:00",
                "diurnal_multiplier": round(diurnal_coeff * demand_multiplier, 3),
                "expected_demand_lps": round(expected_q, 3),
                "confidence_lower_lps": round(ci_lower, 3),
                "confidence_upper_lps": round(ci_upper, 3),
            })

        total_vol_m3 = sum(item["expected_demand_lps"] for item in hourly_forecast) * 3.6  # L/s * 3600s / 1000 = m3

        return {
            "forecast_duration_hours": duration_hours,
            "base_demand_lps": round(base_demand_lps, 3),
            "demand_multiplier": demand_multiplier,
            "uncertainty_percentage": uncertainty_pct,
            "total_forecast_volume_m3": round(total_vol_m3, 2),
            "hourly_forecast": hourly_forecast,
            "is_simulated": True,
            "source": "SYNTHETIC_DIURNAL_FORECAST_MODEL",
        }

