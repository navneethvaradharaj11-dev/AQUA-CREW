"""
AQUA CREW — Water & Ambient Temperature Sensor Adapter (Task 18)
Normalizes RTD and thermistor inputs into standard °C telemetry.
"""
from datetime import datetime, timezone
from typing import Dict, Any
from app.services.iot.adapters.base_adapter import BaseSensorAdapter, NormalizedTelemetry


class TemperatureSensorAdapter(BaseSensorAdapter):
    def __init__(self):
        super().__init__(expected_unit="°C", min_range=-30.0, max_range=90.0)

    def normalize(self, raw_input: Dict[str, Any]) -> NormalizedTelemetry:
        raw_val = float(raw_input.get("value", raw_input.get("temp_c", 0.0)))
        input_unit = str(raw_input.get("unit", "°C")).strip()

        # Handle Fahrenheit to Celsius
        if input_unit.upper() in ["°F", "F"]:
            val_c = (raw_val - 32.0) * (5.0 / 9.0)
        else:
            val_c = raw_val

        in_range, range_err = self.validate_range(val_c)
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
            sensor_id=str(raw_input.get("sensor_id", f"{raw_input.get('device_id', 'DEV')}-TEMP")),
            sensor_type="temperature",
            measurement_value=round(val_c, 2),
            unit="°C",
            timestamp=ts,
            sequence_number=int(raw_input.get("seq", raw_input.get("sequence_number", 1))),
            raw_payload=raw_input,
            data_quality=quality,
            provenance=str(raw_input.get("provenance", "MEASURED")),
            firmware_version=str(raw_input.get("firmware_version", "v1.0.0")),
            calibration_reference=str(raw_input.get("calibration_reference", "")),
            metadata={"freeze_risk": val_c <= 1.0, "range_warning": range_err},
        )

