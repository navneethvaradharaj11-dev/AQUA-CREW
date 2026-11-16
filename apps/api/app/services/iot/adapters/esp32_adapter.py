"""
AQUA CREW — ESP32 Hardware Gateway Device Adapter (Task 18)
Unpacks standard ESP32 IoT telemetry envelopes (including battery voltage, WiFi RSSI, reboot counter).
NOTE: Physical ESP32 hardware remains in simulation-first mode until a controlled hardware test is authorized.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.services.iot.adapters.base_adapter import BaseSensorAdapter, NormalizedTelemetry


class Esp32DeviceAdapter(BaseSensorAdapter):
    def __init__(self):
        super().__init__(expected_unit="multi", min_range=-1000.0, max_range=5000.0)

    def normalize(self, raw_input: Dict[str, Any]) -> NormalizedTelemetry:
        """
        Unpacks primary sensor measurement while capturing ESP32 node diagnostics.
        """
        device_id = str(raw_input.get("device_id", "DEV-ESP32-UNKNOWN"))
        primary_val = float(raw_input.get("value", raw_input.get("primary_reading", 0.0)))
        sensor_type = str(raw_input.get("sensor_type", "pressure"))
        unit = str(raw_input.get("unit", "bar"))

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

        # Diagnostics
        wifi_rssi = int(raw_input.get("wifi_rssi_dbm", -65))
        battery_mv = int(raw_input.get("battery_mv", 3700))
        uptime_s = int(raw_input.get("uptime_seconds", 3600))
        reboot_reason = str(raw_input.get("reboot_reason", "POWER_ON"))

        quality = "VALID"
        if battery_mv < 3200:
            quality = "SUSPECT"

        return NormalizedTelemetry(
            device_id=device_id,
            sensor_id=str(raw_input.get("sensor_id", f"{device_id}-{sensor_type[:2].upper()}")),
            sensor_type=sensor_type,
            measurement_value=primary_val,
            unit=unit,
            timestamp=ts,
            sequence_number=int(raw_input.get("seq", raw_input.get("sequence_number", 1))),
            raw_payload=raw_input,
            data_quality=quality,
            provenance=str(raw_input.get("provenance", "MEASURED")),
            firmware_version=str(raw_input.get("firmware_version", "v1.4.0-esp32")),
            calibration_reference=str(raw_input.get("calibration_reference", "")),
            metadata={
                "esp32_diagnostics": {
                    "wifi_rssi_dbm": wifi_rssi,
                    "battery_mv": battery_mv,
                    "uptime_seconds": uptime_s,
                    "reboot_reason": reboot_reason,
                    "hardware_safety": "SIMULATION_FIRST_MODE_ACTIVE",
                }
            },
        )

