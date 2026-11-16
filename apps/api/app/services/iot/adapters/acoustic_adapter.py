"""
AQUA CREW — Acoustic Leak Sensor Adapter (Task 18)
Normalizes stationary hydrophone and acoustic loggers into standard dB SPL telemetry.
"""
from datetime import datetime, timezone
from typing import Dict, Any
from app.services.iot.adapters.base_adapter import BaseSensorAdapter, NormalizedTelemetry


class AcousticSensorAdapter(BaseSensorAdapter):
    def __init__(self):
        super().__init__(expected_unit="dB", min_range=0.0, max_range=140.0)

    def normalize(self, raw_input: Dict[str, Any]) -> NormalizedTelemetry:
        raw_val = float(raw_input.get("value", raw_input.get("sound_pressure_level_db", 0.0)))
        in_range, range_err = self.validate_range(raw_val)

        quality = "VALID" if in_range else "SUSPECT"
        ts_raw = raw_input.get("timestamp")
        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(timezone.utc)
        elif isinstance(ts_raw, (int, float)):
            ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        return NormalizedTelemetry(
            device_id=str(raw_input.get("device_id", "DEV-UNKNOWN")),
            sensor_id=str(raw_input.get("sensor_id", f"{raw_input.get('device_id', 'DEV')}-AC")),
            sensor_type="acoustic",
            measurement_value=raw_val,
            unit="dB",
            timestamp=ts,
            sequence_number=int(raw_input.get("seq", raw_input.get("sequence_number", 1))),
            raw_payload=raw_input,
            data_quality=quality,
            provenance=str(raw_input.get("provenance", "MEASURED")),
            firmware_version=str(raw_input.get("firmware_version", "v1.4.2")),
            calibration_reference=str(raw_input.get("calibration_reference", "")),
            metadata={
                "dominant_freq_hz": float(raw_input.get("dominant_freq_hz", 500.0)),
                "audio_peak_db": float(raw_input.get("audio_peak_db", raw_val + 3.0)),
                "range_warning": range_err,
            },
        )

