"""
AQUA CREW — Base Sensor Adapter & Telemetry Contract (Task 18)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple


@dataclass
class NormalizedTelemetry:
    device_id: str
    sensor_id: str
    sensor_type: str
    measurement_value: float
    unit: str
    timestamp: datetime
    sequence_number: int = 1
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    data_quality: str = "VALID"
    provenance: str = "MEASURED"
    firmware_version: str = "v1.0.0"
    calibration_reference: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSensorAdapter(ABC):
    """Abstract base class for all sensor and device adapters."""

    def __init__(self, expected_unit: str, min_range: float, max_range: float):
        self.expected_unit = expected_unit
        self.min_range = min_range
        self.max_range = max_range

    def validate_range(self, value: float) -> Tuple[bool, Optional[str]]:
        """Validates that a numeric reading falls within physical sensor limits."""
        if value < self.min_range:
            return False, f"Reading {value} {self.expected_unit} below physical floor ({self.min_range})."
        if value > self.max_range:
            return False, f"Reading {value} {self.expected_unit} above physical ceiling ({self.max_range})."
        return True, None

    @abstractmethod
    def normalize(self, raw_input: Dict[str, Any]) -> NormalizedTelemetry:
        """Transforms raw inbound payload into common NormalizedTelemetry contract."""
        pass

