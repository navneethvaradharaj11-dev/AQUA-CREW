"""
AQUA CREW — Pressure Sensor Adapter (Task 18)
Normalizes piezoresistive pressure transducers into standard bar telemetry.
"""
from datetime import datetime, timezone
from typing import Dict, Any
from app.services.iot.adapters.base_adapter import BaseSensorAdapter, NormalizedTelemetry


class PressureSensorAdapter(BaseSensorAdapter):
    def __init__(self):
        super().__init__(expected_unit="bar", min_range=0.0, max_range=25.0)

    def normalize(self, raw_input: Dict[str, Any]) -> NormalizedTelemetry:
        raw_val = float(raw_input.get("value", raw_input.get("pressure_bar", 0.0)))
        input_unit = str(raw_input.get("unit", "bar")).lower()

        # Handle unit conversion if device reports in psi or kPa
        if input_unit in ["psi"]:
            val_bar = raw_val * 0.0689476
        elif input_unit in ["kpa"]:
            val_bar = raw_val * 0.01
        else:
            val_bar = raw_val

        in_range, range_err = self.validate_range(val_bar)
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
            sensor_id=str(raw_input.get("sensor_id", f"{raw_input.get('device_id', 'DEV')}-PR")),
            sensor_type="pressure",
            measurement_value=round(val_bar, 4),
            unit="bar",
            timestamp=ts,
            sequence_number=int(raw_input.get("seq", raw_input.get("sequence_number", 1))),
            raw_payload=raw_input,
            data_quality=quality,
            provenance=str(raw_input.get("provenance", "MEASURED")),
            firmware_version=str(raw_input.get("firmware_version", "v2.1.0")),
            calibration_reference=str(raw_input.get("calibration_reference", "")),
            metadata={
                "transient_shock_detected": bool(raw_input.get("transient_shock", False)),
                "raw_input_unit": input_unit,
                "range_warning": range_err,
            },
        )

