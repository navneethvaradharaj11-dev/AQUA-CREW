"""
AQUA CREW — Hardware Safety & Actuator Isolation Service (Task 18)
Enforces strict zero-trust hardware boundaries:
- HARDWARE_ACTUATION_ENABLED = False
- Rejection of all physical valve, pump, motor, and actuator control requests
- Allowlist verification for non-actuating telemetry and diagnostic commands
"""
from typing import Dict, Any, Optional
import logging
from app.config import settings
from app.core.exceptions import AquaCrewException
from app.modules.hardware_gateway import (
    ALLOWLISTED_DEVICE_COMMANDS,
    PROHIBITED_ACTUATION_COMMANDS,
    HARDWARE_ACTUATION_ENABLED,
)

logger = logging.getLogger("aqua_crew.iot.safety")


class HardwareActuationForbiddenException(AquaCrewException):
    """Raised when an operation attempts physical hardware actuation while prohibited."""
    def __init__(self, message: str, operation: str):
        super().__init__(
            status_code=403,
            code="HARDWARE_ACTUATION_PROHIBITED",
            message=message,
            details=[
                {
                    "operation": operation,
                    "safety_state": "HARDWARE_ACTUATION_DISABLED",
                    "advisory": "AQUA CREW is a simulation-first platform. Physical actuator commands are strictly prohibited.",
                }
            ],
        )


class HardwareSafetyService:
    @staticmethod
    def is_actuation_enabled() -> bool:
        """Returns whether physical hardware actuation is enabled (always False)."""
        return settings.HARDWARE_ACTUATION_ENABLED and HARDWARE_ACTUATION_ENABLED

    @classmethod
    def verify_operation_safety(cls, operation: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """
        Validates that a device command is non-actuating and safe.
        Rejects any command that could physically alter infrastructure conditions.
        """
        normalized_op = (operation or "").upper().strip()

        # Check explicit prohibited list or prohibited keyword patterns
        if normalized_op in PROHIBITED_ACTUATION_COMMANDS or (
            normalized_op not in ALLOWLISTED_DEVICE_COMMANDS
            and any(
                bad_word in normalized_op
                for bad_word in ["VALVE", "PUMP", "ACTUAT", "RELAY", "MOTOR_DRIVE", "SCADA"]
            )
        ):
            logger.warning(
                f"SECURITY VIOLATION: Prohibited physical actuation command '{normalized_op}' rejected."
            )
            raise HardwareActuationForbiddenException(
                message=f"Physical infrastructure actuation '{normalized_op}' is strictly prohibited by platform safety policy.",
                operation=normalized_op,
            )

        # Check allowlist
        if normalized_op not in ALLOWLISTED_DEVICE_COMMANDS:
            logger.warning(
                f"SAFETY REJECTION: Non-allowlisted device command '{normalized_op}' rejected."
            )
            raise HardwareActuationForbiddenException(
                message=f"Command '{normalized_op}' is not in the allowlisted non-actuating operations. Permitted: {sorted(list(ALLOWLISTED_DEVICE_COMMANDS))}",
                operation=normalized_op,
            )

        # Parameter checks (e.g. check for hidden actuator parameters)
        if parameters:
            for k in parameters.keys():
                k_norm = k.lower()
                if any(bad in k_norm for bad in ["valve_pos", "pump_rpm", "motor_power", "relay_state", "actuator"]):
                    raise HardwareActuationForbiddenException(
                        message=f"Parameter '{k}' specifies physical actuation, which is prohibited.",
                        operation=normalized_op,
                    )
