# AQUA CREW — Hardware Integration & Abstraction Roadmap
## Task 06: Future Integration Pathway (MQTT, ROS 2, Sensor Gateways, Hardware Security)

### 1. Overview & Strategy

The AQUA CREW platform adheres to a strict **Software-First Architecture**. Physical autonomous rovers and IoT hardware are deliberately abstracted behind a clean interface layer (**Hardware Abstraction Layer - HAL**).

> **IMPORTANT CURRENT STATUS**: This platform is in an active **SOFTWARE-ONLY SIMULATION PHASE**. No physical hardware communication is active, and no physical actuators, lasers, valves, or motors are commanded. All telemetry carries `is_simulated: true` and `source: "VIRTUAL_SIMULATION_ENGINE"`.

---

### 2. Hardware Abstraction Layer (HAL) Architecture

```
┌────────────────────────────────────────────────────────┐
│               AQUA CREW Application Core               │
│         (Mission Control, Detection Engine, UI)        │
└───────────────────────────▲────────────────────────────┘
                            │ Standardized Telemetry / Commands
┌───────────────────────────▼────────────────────────────┐
│             Hardware Abstraction Layer (HAL)           │
│   ┌────────────────────────────────────────────────┐   │
│   │               IRoverGateway Interface          │   │
│   │  - send_command(rover_id, cmd, payload)        │   │
│   │  - stream_telemetry()                          │   │
│   │  - query_hardware_status(rover_id)             │   │
│   └────────────────────────────────────────────────┘   │
└───────────────▲────────────────────────▲───────────────┘
                │                        │
  ┌─────────────┴─────────────┐    ┌─────┴─────────────────────┐
  │  VirtualSimulatedDriver   │    │ PhysicalHardwareDriver    │
  │  [CURRENT ACTIVE MODE]    │    │ [FUTURE PATHWAY]          │
  │  - Python Physics Sim     │    │ - MQTT Protocol Broker    │
  │  - Kinematic Motion Model │    │ - ROS 2 / micro-ROS Bridge│
  │  - Synthetic Noise Gen    │    │ - LoRaWAN / Cellular IoT  │
  └───────────────────────────┘    └───────────────────────────┘
```

---

### 3. Future Hardware Integration Protocols

#### 3.1 MQTT Broker Integration (Edge Telemetry)
For distributed field rovers and stationary IoT pipe sensors communicating over cellular (LTE-M/NB-IoT) or Wi-Fi:
- **Broker**: Eclipse Mosquitto or EMQX cluster with TLS encryption on port 8883.
- **Topic Hierarchy**:
  - `aqua/v1/rovers/{device_id}/telemetry` (QoS 0 or 1, publishes `RoverTelemetryPacket`)
  - `aqua/v1/rovers/{device_id}/commands` (QoS 2, receives validated commands)
  - `aqua/v1/sensors/{sensor_id}/telemetry` (QoS 1, acoustic & pressure sensor packets)
  - `aqua/v1/rovers/{device_id}/status` (Last Will and Testament [LWT] payload marking `OFFLINE` on disconnect)

#### 3.2 ROS 2 & micro-ROS Integration (Internal Rover Computing)
For on-board computing platforms (e.g. NVIDIA Jetson Orin Nano, Raspberry Pi 5 running ROS 2 Jazzy Jalisco):
- **Nodes & Topics**:
  - `/rover/kinematics/pose`: `geometry_msgs/msg/PoseWithCovarianceStamped`
  - `/rover/kinematics/cmd_vel`: `geometry_msgs/msg/Twist`
  - `/rover/sensors/acoustic`: `sensor_msgs/msg/ChannelFloat32`
  - `/rover/diagnostics/battery`: `sensor_msgs/msg/BatteryState`
  - `/rover/nav/waypoints`: Action server executing `nav2_msgs/action/NavigateThroughPoses`
- **Bridge**: A Python `rclpy` bridge node translating ROS 2 topics to FastAPI/WebSocket telemetry packets.

#### 3.3 Sensor Gateways (Acoustic & Pressure)
- Stationed at District Metered Area (DMA) boundaries and PRV (Pressure Reducing Valve) chambers.
- Sample acoustic noise at $8\dots32\text{ kHz}$ to detect high-frequency pipe hiss ($800\dots2400\text{ Hz}$).
- Transmit summarized FFT peak profiles and transient pressure spikes via Modbus-TCP or MQTT to the AQUA CREW backend.

---

### 4. Hardware Security & Secure Command Authorization

When physical rovers are deployed, commands that move physical hardware will require enterprise-grade security:
1. **Mutual TLS (mTLS) Authentication**: Every physical rover carries an X.509 device certificate securely provisioned inside a hardware Trusted Platform Module (TPM 2.0 or ATECC608A secure element).
2. **Cryptographic Command Signing**: Any physical movement or valve actuation command will require an Ed25519 cryptographic signature from an authorized municipal operator key:
   - Header: `X-AquaCrew-Signature: <Ed25519-Sig>`
   - Payload includes nonces and expiration timestamps ($\le 5\text{s}$) to prevent replay attacks.
3. **Role-Based Access Control (RBAC)**: Distinct permissions for `OPERATOR_OBSERVE`, `DISPATCH_MISSION`, and `EMERGENCY_OVERRIDE`.
4. **Physical Safety Interlocks (Hardware-Level)**:
   - Physical emergency stop button on rover chassis cuts actuator relay directly without software dependency.
   - On-board watchdog timer cuts motor power if telemetry heartbeat is not received within $3000\text{ ms}$.
