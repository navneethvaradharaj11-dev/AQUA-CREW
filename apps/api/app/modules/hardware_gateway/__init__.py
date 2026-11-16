"""
AQUA CREW - Architectural Boundary
Module 12: Hardware Communication Gateway - Hardware Abstraction Layer (HAL), MQTT, and IoT Device Management.
Task 18: Hardware & IoT Integration Readiness (Simulation-First Architecture)
"""

MODULE_NAME = "hardware_gateway"
IS_IMPLEMENTED = False
HARDWARE_STATUS = "HARDWARE NOT CONNECTED"
HARDWARE_ACTUATORS_DISABLED = True
HARDWARE_ACTUATION_ENABLED = False

# Explicitly allowlisted non-actuating operations
ALLOWLISTED_DEVICE_COMMANDS = {
    "READ_STATUS",
    "REQUEST_TELEMETRY",
    "READ_SENSOR_CONFIG",
    "UPDATE_CONFIG_NON_ACTUATING",
    "RUN_DEVICE_DIAGNOSTICS",
    "PING",
    "REPORT_BATTERY",
    "CALIBRATION_CHECK",
}

# Strictly prohibited physical actuation operations
PROHIBITED_ACTUATION_COMMANDS = {
    "CLOSE_VALVE",
    "OPEN_VALVE",
    "MODULATE_VALVE",
    "START_PUMP",
    "STOP_PUMP",
    "SET_PUMP_SPEED",
    "DISPATCH_PHYSICAL_ROVER",
    "DRIVE_MOTOR",
    "TRIGGER_PHYSICAL_RELAY",
    "OVERRIDE_SCADA_PLC",
}
