"""
AQUA CREW — Flow Meter Adapter (Task 18)
Normalizes electromagnetic and ultrasonic flow meters into standard L/s telemetry.
"""
from datetime import datetime, timezone
from typing import Dict, Any
from app.services.iot.adapters.base_adapter import BaseSensorAdapter, NormalizedTelemetry


class FlowSensorAdapter(BaseSensorAdapter):
    def __init__(self):
        super().__init__(expected_unit="L/s", min_range=-50.0, max_range=1000.0)

    def normalize(self, raw_input: Dict[str, Any]) -> NormalizedTelemetry:
        raw_val = float(raw_input.get("value", raw_input.get("flow_rate_lps", 0.0)))
        input_unit = str(raw_input.get("unit", "L/s")).lower()

        # Handle unit conversion if device reports in m3/h or gpm
        if input_unit in ["m3/h", "m3h"]:
            val_lps = raw_val * (1000.0 / 3600.0)
        elif input_unit in ["gpm"]:
            val_lps = raw_val * 0.0630902
        else:
            val_lps = raw_val

        in_range, range_err = self.validate_range(val_lps)
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
            sensor_id=str(raw_input.get("sensor_id", f"{raw_input.get('device_id', 'DEV')}-FL")),
            sensor_type="flow",
            measurement_value=round(val_lps, 3),
            unit="L/s",
            timestamp=ts,
            sequence_number=int(raw_input.get("seq", raw_input.get("sequence_number", 1))),
            raw_payload=raw_input,
            data_quality=quality,
            provenance=str(raw_input.get("provenance", "MEASURED")),
            firmware_version=str(raw_input.get("firmware_version", "v3.0.4")),
            calibration_reference=str(raw_input.get("calibration_reference", "")),
            metadata={
                "bidirectional_flow": val_lps < 0,
                "raw_input_unit": input_unit,
                "range_warning": range_err,
            },
        )

