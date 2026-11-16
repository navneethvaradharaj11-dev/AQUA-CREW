"""
AQUA CREW — Temporal Risk Trend Service (Task 11 / 11.5)
Calculates multi-horizon deterioration velocity (24h, 7d, 30d),
direction classifications, and handles irregular timestamps, sparse data,
and duplicate observations using Ordinary Least Squares (OLS) regression.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import math

from app.models.pipeline_segment import PipelineSegmentModel
from app.models.predictive_maintenance import HistoricalTrendModel, PipelineHealthModel
from app.models.ai_detection import AiDetectionModel


class RiskTrendService:
    @classmethod
    def calculate_ols_slope(
        cls,
        observations: List[Tuple[datetime, float]],
    ) -> Tuple[Optional[float], str, Optional[float]]:
        """
        Calculates deterioration rate (score points per day) using Ordinary Least Squares (OLS)
        regression over a timestamped series of risk observations: [(t_0, v_0), (t_1, v_1), ...].
        
        Handles:
        - Irregular timestamps (uses elapsed days delta)
        - Duplicate timestamps (groups and averages values at identical timestamps)
        - Sparse history (returns INSUFFICIENT_DATA if < 2 distinct timestamps or span < 1 hour)
        
        Returns:
        (slope_per_day, data_sufficiency, r_squared)
        """
        if not observations or len(observations) < 2:
            return None, "INSUFFICIENT_DATA", None

        # 1. Group and average duplicate timestamps
        timestamp_buckets: Dict[float, List[float]] = {}
        for dt, val in observations:
            if dt is None or val is None or math.isnan(val):
                continue
            t_epoch = dt.timestamp() if isinstance(dt, datetime) else float(dt)
            if t_epoch not in timestamp_buckets:
                timestamp_buckets[t_epoch] = []
            timestamp_buckets[t_epoch].append(float(val))

        sorted_epochs = sorted(timestamp_buckets.keys())
        if len(sorted_epochs) < 2:
            return None, "INSUFFICIENT_DATA", None

        # Check total time span
        total_span_hours = (sorted_epochs[-1] - sorted_epochs[0]) / 3600.0
        if total_span_hours < 1.0:
            # Observation window too narrow to infer daily deterioration
            return None, "INSUFFICIENT_DATA", None

        # Construct (days_from_start, mean_val) pairs
        t0 = sorted_epochs[0]
        points: List[Tuple[float, float]] = []
        for ep in sorted_epochs:
            t_days = (ep - t0) / 86400.0  # seconds to days
            vals = timestamp_buckets[ep]
            mean_v = sum(vals) / len(vals)
            points.append((t_days, mean_v))

        n = len(points)
        sum_t = sum(p[0] for p in points)
        sum_v = sum(p[1] for p in points)
        mean_t = sum_t / n
        mean_v = sum_v / n

        ss_tt = sum((p[0] - mean_t) ** 2 for p in points)
        ss_tv = sum((p[0] - mean_t) * (p[1] - mean_v) for p in points)
        ss_vv = sum((p[1] - mean_v) ** 2 for p in points)

        if ss_tt < 1e-9:
            return 0.0, "LOW", 0.0

        slope = ss_tv / ss_tt  # points per day
        r_squared = (ss_tv ** 2) / (ss_tt * ss_vv) if (ss_tt * ss_vv) > 1e-9 else 0.0

        # Data sufficiency rating based on points count and time span
        if n >= 5 and total_span_hours >= 72.0:
            data_sufficiency = "HIGH"
        elif n >= 3 and total_span_hours >= 24.0:
            data_sufficiency = "MODERATE"
        else:
            data_sufficiency = "LOW"

        return round(slope, 3), data_sufficiency, round(r_squared, 3)

    @classmethod
    def calculate_temporal_trends(
        cls,
        segment: PipelineSegmentModel,
        current_vulnerability: float,
        trend_rec: Optional[HistoricalTrendModel] = None,
        health_rec: Optional[PipelineHealthModel] = None,
        recent_detections: Optional[List[AiDetectionModel]] = None,
        historical_observations: Optional[List[Tuple[datetime, float]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates 24-hour, 7-day, and 30-day risk changes and deterioration rates.
        Prioritizes OLS regression when timestamped series is available,
        falling back to Task 09 historical trend models or physical material baselines.
        """
        detections = recent_detections or []
        ols_slope, ols_sufficiency, r_squared = None, None, None

        # 1. Try OLS regression over timestamped observations
        if historical_observations:
            ols_slope, ols_sufficiency, r_squared = cls.calculate_ols_slope(historical_observations)

        if ols_slope is not None and ols_sufficiency != "INSUFFICIENT_DATA":
            daily_rate = max(-2.0, min(5.0, ols_slope))
            data_sufficiency = ols_sufficiency
        elif trend_rec and trend_rec.health_slope_per_day is not None:
            # health slope is points/day (negative means deteriorating health)
            # risk slope is inverse of health slope
            daily_rate = max(-1.5, min(3.0, -trend_rec.health_slope_per_day * 0.8))
            data_sufficiency = "HIGH"
        else:
            # Physical empirical baseline from pipe material and active leak alerts
            daily_rate = 0.05
            mat = (segment.material or "").lower()
            if "cast" in mat:
                daily_rate += 0.12
            elif "concrete" in mat:
                daily_rate += 0.08
            elif "ductile" in mat:
                daily_rate += 0.05

            if len(detections) > 0:
                daily_rate += len(detections) * 0.18
                data_sufficiency = "MODERATE"
            else:
                data_sufficiency = "LOW"

        # Adjust for unresolved high-severity detections
        unresolved = [d for d in detections if d.status in ["PENDING_REVIEW", "INSPECTION_DISPATCHED"]]
        if unresolved:
            daily_rate += 0.25

        daily_rate = round(daily_rate, 2)

        # 2. Multi-horizon deltas
        trend_24h_delta = round(daily_rate * 1.0, 2)
        trend_7d_delta = round(daily_rate * 7.0, 2)
        trend_30d_delta = round(daily_rate * 30.0, 2)

        # 3. Classify direction
        if trend_7d_delta > 1.5:
            trend_direction = "DETERIORATING"
        elif trend_7d_delta < -1.5:
            trend_direction = "IMPROVING"
        else:
            trend_direction = "STABLE"

        # Rapid degradation check
        rapid_degradation = (trend_24h_delta >= 0.4) or (trend_7d_delta >= 2.5)

        return {
            "pipeline_segment_id": segment.id,
            "deterioration_rate_per_day": daily_rate,
            "trend_direction": trend_direction,
            "trend_24h_delta": trend_24h_delta,
            "trend_7d_delta": trend_7d_delta,
            "trend_30d_delta": trend_30d_delta,
            "rapid_degradation": rapid_degradation,
            "data_sufficiency": data_sufficiency,
            "r_squared": r_squared,
            "assessed_at": datetime.now(timezone.utc),
        }
