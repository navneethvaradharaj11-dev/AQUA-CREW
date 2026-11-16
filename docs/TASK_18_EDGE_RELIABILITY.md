# AQUA CREW — TASK 18 EDGE DEVICE & OFFLINE RELIABILITY ARCHITECTURE

> [!NOTE]
> Physical water infrastructure sensors operate in harsh environments: underground cast-iron vaults, damp manholes, and locations with intermittent NB-IoT/cellular coverage. AQUA CREW's edge reliability architecture guarantees store-and-forward persistence, bounded memory safety, clock synchronization compensation, and burst retransmission without server overload.

---

## 1. Edge Storage & Bounded Ring Buffer Queue

Edge hardware gateways (such as ESP32 nodes or industrial RTUs) possess finite SRAM and flash memory. Unbounded queuing during cellular blackouts results in memory exhaustion, out-of-memory kernel panics, and hardware reboot loops.

`EdgeBufferQueue` implements a bounded FIFO ring buffer:
- **Default Capacity**: 1,000 normalized telemetry frames per node.
- **Overflow Policy**: **FIFO Eviction (Drop Oldest)**. When the buffer reaches 1,000 items, the oldest reading is evicted to accommodate incoming real-time telemetry, ensuring that the most recent operational conditions are prioritized.
- **Drop Accounting**: Every evicted packet increments `dropped_overflow_count` for loss rate telemetry.

```mermaid
flowchart LR
    Sensor["New Sensor Reading"] --> Check{"Buffer Size < 1,000?"}
    Check -->|Yes| Push["Enqueue at Tail"]
    Check -->|No (Buffer Full)| Drop["Evict Oldest (Head)\nIncrement dropped_overflow_count"]
    Drop --> Push
    Reconnect["Cellular Uplink Restored"] --> Drain["drain(batch_size=100)\nBurst Transmit with Fingerprint"]
```

---

## 2. Exponential Backoff with Decorrelated Jitter

When a cellular base station experiences an outage or the central MQTT broker restarts, thousands of field nodes attempting simultaneous reconnection cause a thundering herd problem that overwhelms gateway network interfaces.

`EdgeRetransmissionEngine` computes truncated exponential backoff with decorrelated additive jitter:

$$\text{Delay}(a) = \min\left(t_{\max}, t_{\text{base}} \cdot 2^{\min(a, 10)}\right) \pm \text{Uniform}(-\gamma \cdot t, \gamma \cdot t)$$

Where:
- $t_{\text{base}} = 1.0\text{ second}$ (initial retry delay).
- $t_{\max} = 60.0\text{ seconds}$ (maximum backoff ceiling).
- $a$ is the consecutive reconnection attempt counter.
- $\gamma = 0.2$ (jitter factor of $\pm 20\%$).

### Backoff Progression Curve
| Attempt | Exponential Base | Range with $\pm 20\%$ Jitter |
|:---:|:---:|:---:|
| 0 | 1.0 s | 0.80 s – 1.20 s |
| 1 | 2.0 s | 1.60 s – 2.40 s |
| 2 | 4.0 s | 3.20 s – 4.80 s |
| 3 | 8.0 s | 6.40 s – 9.60 s |
| 4 | 16.0 s | 12.80 s – 19.20 s |
| 5+ | 32.0 s – 60.0 s (capped) | 48.0 s – 60.0 s |

---

## 3. Clock Synchronization & Drift Estimation

Many battery-powered IoT loggers lack continuous GPS reception in underground chambers and rely on low-power crystal Real-Time Clocks (RTCs), which drift over seasonal temperature fluctuations ($\pm 20\text{ ppm}$).

`EdgeRetransmissionEngine.estimate_clock_drift()` compares inbound device timestamps against central server time:
- **Acceptable Drift**: $|\Delta t| \le 5,000\text{ ms}$ (5.0 seconds).
- **Flagged Drift**: When $|\Delta t| > 5,000\text{ ms}$, the reading is flagged as `BEHIND` or `AHEAD`.
- **Stale Threshold**: When $\Delta t > 24\text{ hours}$ (e.g. buffered over long-term offline retention), the ingestion engine stores the reading with `data_quality = "STALE"` to preserve historical accuracy without corrupting real-time alarms.

---

## 4. Deterministic Deduplication Fingerprinting

During network reconnection, TCP connection resets can cause duplicate deliveries of buffered readings. The gateway calculates an SHA-256 fingerprint for every incoming reading:

$$\text{Fingerprint} = \text{SHA-256}(\text{device\_id} \,\|\, \text{sensor\_id} \,\|\, \text{seq} \,\|\, \text{timestamp})$$

- If an incoming fingerprint matches an existing entry in the 300-second cache, the duplicate is suppressed, preventing duplicate alarms in Task 07 AI Leak Detection.

