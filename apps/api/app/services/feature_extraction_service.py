"""
Multi-Modal Feature Extraction and Normalization Service
Combines acoustic signals with hydraulic, soil, and pipeline infrastructure metadata.
"""
import numpy as np
from typing import Dict, Any, Tuple, Optional

from app.schemas.ai import LeakAnalyzeRequest, SyntheticWaveformRequest
from app.services.signal_processing_service import SignalProcessingService


MATERIAL_MAP = {
    "ductile_iron": 1.0,
    "cast_iron": 2.0,
    "steel": 3.0,
    "pvc": 4.0,
    "hdpe": 5.0,
}

FEATURE_NAMES = [
    "rms_amplitude",
    "dominant_frequency_hz",
    "spectral_centroid_hz",
    "leak_band_energy_ratio",
    "pressure_deviation_bar",
    "flow_deviation_m3h",
    "moisture_deviation_pct",
    "soil_temp_deviation_c",
    "sensor_reliability",
    "pipe_diameter_mm",
    "pipe_material_index",
    "operating_pressure_bar",
]


class FeatureExtractionService:
    @staticmethod
    def extract_feature_vector(
        req: LeakAnalyzeRequest,
        pipe_meta: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extracts 12-dimensional multi-modal feature vector from request and pipe metadata.
        Returns (feature_vector_array, named_feature_dict).
        """
        if pipe_meta is None:
            pipe_meta = {
                "diameter_mm": 300,
                "material": "ductile_iron",
                "operating_pressure_bar": 4.5,
            }

        # 1. Synthesize or extract acoustic features
        scenario = req.acoustic_scenario or "MODERATE_LEAK"
        synth_req = SyntheticWaveformRequest(
            scenario=scenario,
            duration_seconds=1.0,
            sampling_rate_hz=8000,
            pipe_material=pipe_meta.get("material", "ductile_iron"),
            pipe_diameter_mm=pipe_meta.get("diameter_mm", 300),
        )
        waveform, _, _ = SignalProcessingService.generate_synthetic_waveform(synth_req)
        acoustics = SignalProcessingService.extract_acoustic_features(waveform, 8000)

        # 2. Hydraulic & Environmental Deviations
        measured_p = req.pressure_bar if req.pressure_bar is not None else 4.2
        expected_p = req.expected_pressure_bar or 4.5
        delta_p = max(0.0, expected_p - measured_p)  # Pressure drop indicates potential leak

        measured_q = req.flow_rate_m3h if req.flow_rate_m3h is not None else 50.0
        expected_q = req.expected_flow_m3h or 50.0
        delta_q = abs(measured_q - expected_q)

        measured_m = req.ground_moisture_pct if req.ground_moisture_pct is not None else 18.0
        baseline_m = req.baseline_moisture_pct or 15.0
        delta_m = max(0.0, measured_m - baseline_m)

        measured_temp = req.soil_temp_c or 18.0
        delta_temp = abs(measured_temp - 18.0)

        # 3. Structural Metadata
        pipe_diam = float(pipe_meta.get("diameter_mm", 300))
        mat_str = str(pipe_meta.get("material", "ductile_iron")).lower()
        mat_idx = MATERIAL_MAP.get(mat_str, 1.0)
        op_pressure = float(pipe_meta.get("operating_pressure_bar", 4.5))
        reliability = req.sensor_reliability if req.sensor_reliability is not None else 0.95

        named_dict = {
            "rms_amplitude": acoustics.rms_amplitude,
            "dominant_frequency_hz": acoustics.dominant_frequency_hz,
            "spectral_centroid_hz": acoustics.spectral_centroid_hz,
            "leak_band_energy_ratio": acoustics.leak_band_energy_ratio,
            "pressure_deviation_bar": round(delta_p, 3),
            "flow_deviation_m3h": round(delta_q, 3),
            "moisture_deviation_pct": round(delta_m, 2),
            "soil_temp_deviation_c": round(delta_temp, 2),
            "sensor_reliability": round(reliability, 2),
            "pipe_diameter_mm": pipe_diam,
            "pipe_material_index": mat_idx,
            "operating_pressure_bar": op_pressure,
        }

        vector = np.array([named_dict[name] for name in FEATURE_NAMES], dtype=float)
        return vector, named_dict
