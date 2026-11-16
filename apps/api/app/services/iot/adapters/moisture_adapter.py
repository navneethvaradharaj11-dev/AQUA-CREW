"""
AQUA CREW — Subsurface Moisture Sensor Adapter (Task 18)
Normalizes soil moisture probes and time-domain reflectometers into standard % VWC telemetry.
"""
from datetime import datetime, timezone
from typing import Dict, Any
from app.services.iot.adapters.base_adapter import BaseSensorAdapter, NormalizedTelemetry


class MoistureSensorAdapter(BaseSensorAdapter):
    def __init__(self):
        super().__init__(expected_unit="%", min_range=0.0, max_range=100.0)

    def normalize(self, raw_input: Dict[str, Any]) -> NormalizedTelemetry:
        raw_val = float(raw_input.get("value", raw_input.get("moisture_pct", 0.0)))
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
            sensor_id=str(raw_input.get("sensor_id", f"{raw_input.get('device_id', 'DEV')}-MOIST")),
            sensor_type="moisture",
            measurement_value=round(raw_val, 2),
            unit="%",
            timestamp=ts,
            sequence_number=int(raw_input.get("seq", raw_input.get("sequence_number", 1))),
            raw_payload=raw_input,
            data_quality=quality,
            provenance=str(raw_input.get("provenance", "MEASURED")),
            firmware_version=str(raw_input.get("firmware_version", "v1.1.0")),
            calibration_reference=str(raw_input.get("calibration_reference", "")),
            metadata={
                "dielectric_permittivity": float(raw_input.get("permittivity", 24.5)),
                "range_warning": range_err,
            },
        )

