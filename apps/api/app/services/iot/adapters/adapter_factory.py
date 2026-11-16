"""
AQUA CREW — Sensor Adapter Factory (Task 18)
"""
from typing import Dict, Type
from app.services.iot.adapters.base_adapter import BaseSensorAdapter, NormalizedTelemetry
from app.services.iot.adapters.acoustic_adapter import AcousticSensorAdapter
from app.services.iot.adapters.pressure_adapter import PressureSensorAdapter
from app.services.iot.adapters.flow_adapter import FlowSensorAdapter
from app.services.iot.adapters.moisture_adapter import MoistureSensorAdapter
from app.services.iot.adapters.temperature_adapter import TemperatureSensorAdapter
from app.services.iot.adapters.optical_adapter import OpticalSensorAdapter
from app.services.iot.adapters.esp32_adapter import Esp32DeviceAdapter
from app.services.iot.adapters.virtual_adapter import VirtualSensorAdapter


class SensorAdapterFactory:
    _adapters: Dict[str, BaseSensorAdapter] = {}

    @classmethod
    def get_adapter(cls, sensor_type: str, device_type: str = "") -> BaseSensorAdapter:
        """
        Resolves adapter based on sensor type or device archetype.
        """
        st = (sensor_type or "").lower().strip()
        dt = (device_type or "").upper().strip()

        if dt == "VIRTUAL_SIMULATION_DEVICE" or st == "virtual":
            return VirtualSensorAdapter()

        if dt == "ESP32_DEVICE" or "ESP32" in dt:
            return Esp32DeviceAdapter()

        if st == "acoustic":
            return AcousticSensorAdapter()
        elif st == "pressure":
            return PressureSensorAdapter()
        elif st == "flow":
            return FlowSensorAdapter()
        elif st in ["moisture", "ground_moisture"]:
            return MoistureSensorAdapter()
        elif st in ["temperature", "temp"]:
            return TemperatureSensorAdapter()
        elif st in ["optical", "inspection"]:
            return OpticalSensorAdapter()

        # Fallback to virtual adapter
        return VirtualSensorAdapter()

