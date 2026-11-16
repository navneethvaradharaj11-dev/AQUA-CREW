# AQUA CREW — TASK 18 OPERATIONAL LIMITATIONS & ROADMAP

> [!WARNING]
> This document details intentional safety boundaries, hardware assumptions, throughput thresholds, and edge protocol constraints governing Task 18.

---

## 1. Safety Boundaries & Intentional Invariants

### 1.1 Absolute Prohibition of Physical Actuation
- **Limitation**: AQUA CREW does not support physical valve positioning, pump starts/stops, or motor drive control.
- **Rationale**: Actuation in pressurized municipal water systems poses life-safety and infrastructure surge hazards (transient water hammer). Operating without physical dual interlocks and localized safety valves could rupture municipal pipes.
- **Invariant**: `HARDWARE_ACTUATION_ENABLED = false` is permanent until specialized hardware test benches with certified pneumatic safety reliefs are authorized.

### 1.2 Separation of Synthetic and Ground-Truth Evidence
- **Limitation**: Synthetic digital twin data can never claim `MEASURED` provenance.
- **Rationale**: Prevents machine learning models from training on self-generated simulation outputs (model collapse).
- **Invariant**: Ingestion engine strictly forces `provenance = "SIMULATED"` on all virtual devices.

---

## 2. Ingestion & Throughput Scale Boundaries

| Parameter | Operational Threshold | Enforcement Mechanism | Consequence of Breach |
|---|---|---|---|
| **Max MQTT Frame Size** | 64 KB (65,536 bytes) | `MqttSecurityGuard` | Packet dropped; logged as security violation |
| **Max Ingestion Rate per Device** | 60 messages / minute | Rate Limiter Middleware | HTTP 429 Too Many Requests |
| **Max Batch Ingest Size** | 100 readings / request | `BatchTelemetryIngestRequest` | HTTP 422 Unprocessable Content |
| **Edge Memory Bounded Buffer** | 1,000 readings / node | `EdgeBufferQueue` (FIFO) | Oldest readings evicted; loss counter incremented |
| **Deduplication Cache Window** | 300 seconds (5 minutes) | In-Memory Sliding Window | Replayed messages silently suppressed |
| **Clock Drift Synchronization** | $\pm 5,000\text{ ms}$ (5.0s) | `EdgeRetransmissionEngine` | Readings $> 24\text{h}$ old tagged `STALE` |

---

## 3. Communication Protocol Boundaries

1. **Raw Acoustic Waveform Transmission**:
   - The platform does not ingest uncompressed high-bandwidth raw PCM audio (e.g. 48 kHz 24-bit audio streams) over cellular links due to municipal data plan costs.
   - Field hydrophones must perform edge FFT preprocessing and transmit normalized Sound Pressure Level (dB SPL) and dominant peak frequency (Hz).
2. **Subsurface RF Attenuation**:
   - Radio waves undergo high attenuation through damp soil and concrete manhole covers. Field deployment requires external antenna mounts or above-ground repeater pedestals.
3. **Broker Dependency in Production**:
   - In production, a hardened Mosquitto or EMQX cluster is required. The bundled in-memory simulation mode is intended exclusively for test hermeticity and offline development.

---

## 4. Hardware Evolution Roadmap (Task 19+)

1. **Hardware-in-the-Loop (HIL) Testbed**:
   - Develop a closed-loop pneumatic/hydraulic physical test bench operating in a certified laboratory environment with hardware pressure relief valves.
2. **LoRaWAN Gateway Integration**:
   - Integrate standard LoRaWAN 1.0.4 / 1.1 regional frequency profiles (EU868, US915) via ChirpStack or The Things Network (TTN) webhooks.
3. **Dual-Key Hardware Actuation Authorization**:
   - Design an air-gapped cryptographic signing ceremony requiring two physical hardware security keys (FIDO2 / YubiKey) before allowing any physical valve maintenance cycle.

