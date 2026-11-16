# AQUA CREW — TASK 18 IoT SECURITY & ZERO-TRUST HARDWARE ARCHITECTURE

> [!CAUTION]
> **CRITICAL CRITICAL INFRASTRUCTURE PROTECTION**:
> Water distribution networks are vital municipal infrastructure. Unauthorized or erroneous actuation of physical valves and pumps can cause transient water hammer surges, pipe bursts, secondary contamination, pressure loss to emergency services, and structural infrastructure failure.
> AQUA CREW enforces a **Zero-Trust Simulation-First Boundary**: `HARDWARE_ACTUATION_ENABLED = false`.

---

## 1. Zero-Trust IoT Security Model

AQUA CREW adopts a Zero-Trust security paradigm across all hardware, edge gateways, and IoT sensors. No device, network node, or protocol message is implicitly trusted, regardless of whether it originates within a private SCADA LAN, cellular VPN, or internet edge.

Every request and telemetry reading must satisfy four mandatory criteria:
1. **Explicit Identity Verification**: The transmitting device must possess an active, non-revoked record in `iot_devices` and present valid cryptographic proof (Bearer JWT or `X-Device-Secret` API key).
2. **Lifecycle State Integrity**: Quarantined (`status = "QUARANTINED"`) or revoked (`status = "REVOKED"`) devices are rejected with HTTP 403.
3. **Allowlisted Operation Validation**: Only explicitly allowlisted non-actuating commands may be executed. Actuation commands raise `HardwareActuationForbiddenException`.
4. **Metrological Integrity**: Telemetry readings are audited against calibration certificates. Readings from uncalibrated or overdue sensors are downgraded to `SUSPECT` or `UNCALIBRATED`.

---

## 2. Hardware Actuation Prohibition & Air-Gap Defense

Physical infrastructure actuation endpoints are prohibited by backend policy and isolated by air-gap logic:

```mermaid
flowchart LR
    Client["Client / Device Request"] --> Route{"Target Endpoint"}
    Route -->|POST /api/v1/iot/devices/{id}/commands| Filter["HardwareSafetyService"]
    Filter --> Check{"Command in ALLOWLISTED_DEVICE_COMMANDS?"}
    Check -->|No or Contains 'VALVE' / 'PUMP'| Block["HTTP 403 Forbidden\nCODE: HARDWARE_ACTUATION_PROHIBITED\nAudit Log: SECURITY_VIOLATION"]
    Check -->|Yes (READ_STATUS, RUN_DIAGNOSTICS)| Exec["Safe Non-Actuating Diagnostic Output"]
```

### Prohibited Actuation Operations
The following operations are classified as hazardous actuation and are rejected:
- `CLOSE_VALVE`, `OPEN_VALVE`, `MODULATE_VALVE`
- `START_PUMP`, `STOP_PUMP`, `SET_PUMP_SPEED`
- `DISPATCH_PHYSICAL_ROVER`, `DRIVE_MOTOR`
- `TRIGGER_PHYSICAL_RELAY`, `OVERRIDE_SCADA_PLC`

### Allowlisted Non-Actuating Operations
The platform strictly limits device commands to non-actuating read and diagnostic functions:
- `READ_STATUS`: Query current operating telemetry snapshot.
- `REQUEST_TELEMETRY`: Trigger immediate sensor telemetry transmission.
- `READ_SENSOR_CONFIG`: Query configured sensor parameters and sampling rates.
- `UPDATE_CONFIG_NON_ACTUATING`: Update reporting intervals (without altering physical actuation).
- `RUN_DEVICE_DIAGNOSTICS`: Perform internal self-test (bus sanity, RTC drift, battery level).
- `PING`: Verify network reachability.
- `REPORT_BATTERY`: Report battery state of charge and voltage curve.
- `CALIBRATION_CHECK`: Query active calibration status and due dates.

---

## 3. Cryptographic Credential Management

Device credentials follow strict cryptographic lifecycles managed by `IotRepository`:

```
Device Secret Format: aqdev_{device_id[:6]}_{urlsafe_b64_token}
Example: aqdev_dev-ac_1cW1diZN5lgU-LyFj91vBVyrFCNz314wo0wdkeVq-RM
```

### Storage and Verification
- Plaintext API keys are **never stored** in the database.
- The platform stores the SHA-256 cryptographic digest: `hashed_secret = sha256(secret)`.
- Key prefixes (e.g., `aqdev_dev-ac_...`) are retained in `device_credentials` for administrative auditing and UI identification.
- Each key is assigned an incremental `credential_version`.

### Credential Rotation Workflow
1. An administrator invokes `POST /api/v1/iot/devices/{device_id}/credentials/rotate`.
2. Existing active credentials for the device are marked `revoked = true` with `revoked_at = utcnow()` and `revocation_reason = "credential_rotation"`.
3. A new cryptographic token is generated and hashed.
4. The new plaintext secret is returned **once** in the HTTP response; it cannot be retrieved thereafter.
5. An immutable audit record is committed to `device_audit_logs`.

---

## 4. Threat Modeling (STRIDE Analysis)

| Threat Category | Potential Attack Vector | AQUA CREW Architectural Mitigation |
|---|---|---|
| **Spoofing** | Rogue node impersonating pressure sensor to inject false pressure drops | Cryptographic API keys (`X-Device-Secret`), device registry validation, mTLS X.509 client authentication. |
| **Tampering** | Man-in-the-middle modification of acoustic telemetry packets | TLS 1.3 / mTLS transport encryption, SHA-256 payload fingerprinting, strict JSON schema validation. |
| **Repudiation** | Operator denying dispatch of unauthorized diagnostic command | Tamper-evident `device_audit_logs` capturing actor identity, source IP, timestamp, and command details. |
| **Information Disclosure** | Sniffing municipal water network layout and hydraulic telemetry | Mandatory TLS on MQTT (Port 8883) and REST (HTTPS); RBAC permissions restricting raw telemetry access. |
| **Denial of Service** | Flooding MQTT broker with telemetry bursts or malformed packets | Max payload limit (64 KB), rate limiter (60 req/min per device), FIFO bounded buffer (1,000 items). |
| **Elevation of Privilege** | Using device credentials to actuate physical distribution valves | Complete elimination of actuator endpoints; `HARDWARE_ACTUATION_ENABLED = false`; RBAC role hierarchy. |

---

## 5. Role-Based Access Control (RBAC) Matrix

AQUA CREW enforces Zero-Trust RBAC across all IoT endpoints via `app.core.auth`:

| Endpoint Category | Method | Path | VIEWER | OPERATOR | ENGINEER | ADMIN |
|---|---|---|:---:|:---:|:---:|:---:|
| **Fleet Status** | `GET` | `/api/v1/iot/status` | ✅ | ✅ | ✅ | ✅ |
| **Device Directory** | `GET` | `/api/v1/iot/devices` | ✅ | ✅ | ✅ | ✅ |
| **Device Registration**| `POST`| `/api/v1/iot/devices` | ❌ | ✅ | ✅ | ✅ |
| **Device Quarantine** | `POST`| `/api/v1/iot/devices/{id}/quarantine` | ❌ | ❌ | ❌ | ✅ |
| **Device Revocation** | `POST`| `/api/v1/iot/devices/{id}/revoke` | ❌ | ❌ | ❌ | ✅ |
| **Credential Rotation**| `POST`| `/api/v1/iot/devices/{id}/credentials/rotate` | ❌ | ❌ | ❌ | ✅ |
| **Allowlisted Command**| `POST`| `/api/v1/iot/devices/{id}/commands` | ❌ | ✅ | ✅ | ✅ |
| **Actuator Command** | `POST`| `/api/v1/iot/devices/{id}/commands` | 🚫 **BLOCKED** | 🚫 **BLOCKED** | 🚫 **BLOCKED** | 🚫 **BLOCKED** |
| **Telemetry Ingestion**| `POST`| `/api/v1/iot/telemetry/ingest` | ❌ | ✅ | ✅ | ✅ |
| **Read Telemetry** | `GET` | `/api/v1/iot/telemetry/latest` | ✅ | ✅ | ✅ | ✅ |
| **Record Calibration** | `POST`| `/api/v1/iot/calibration` | ❌ | ✅ | ✅ | ✅ |
| **Security Audit Log** | `GET` | `/api/v1/iot/audit` | ❌ | ❌ | ❌ | ✅ |

---

## 6. Tamper-Evident Security Audit Ledger

All security-sensitive operations are captured in `device_audit_logs`:
- **Schema**:
  - `id`: Unique identifier (`AUD-XXXX`).
  - `device_id`: Target device identifier.
  - `action`: `REGISTRATION`, `CREDENTIAL_ROTATION`, `QUARANTINE`, `CREDENTIAL_REVOCATION`, `DEVICE_COMMAND_DISPATCHED`, `FAILED_AUTHENTICATION`.
  - `actor`: Authenticated user ID or system principal.
  - `status`: `SUCCESS`, `DENIED`, `BLOCKED`.
  - `ip_address`: Originating IPv4/IPv6 client address.
  - `details`: JSON payload capturing key prefixes, command names, and parameter hashes.
  - `timestamp`: UTC timestamp with microsecond precision.

