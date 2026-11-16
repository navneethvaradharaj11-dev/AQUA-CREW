# AQUA CREW — TASK 18 HARDWARE INTEGRATION & DEVELOPER GUIDE

> [!IMPORTANT]
> **SAFETY PREREQUISITE**:
> Before integrating physical hardware into AQUA CREW, review the Hardware Safety Charter. Physical valve, pump, or actuator control interfaces must **never** be connected to AQUA CREW. Only telemetry acquisition, environmental monitoring, and diagnostic read channels are permitted.

---

## 1. Supported Field Hardware Interfaces

AQUA CREW integrates with industrial instrumentation across three primary physical layers:

```
[Physical Instrumentation]
  ├── 4-20 mA Current Loop (Pressure Transducers, Level Sensors)
  ├── RS-485 Modbus RTU / DNP3 (Electromagnetic Flowmeters)
  ├── I2C / SPI (Hydrophones, Accelerometers, Soil Moisture)
  └── Serial UART (Boroscopic Cameras)
         │
         ▼
[Edge Concentrator / Gateway (ESP32-S3, Raspberry Pi, Industrial RTU)]
         │
         ▼ (Encrypted Cellular LTE-M / NB-IoT / Ethernet)
[MQTT TLS 8883 / HTTPS REST Ingest]
         │
         ▼
[AQUA CREW Task 18 Gateway]
```

---

## 2. Implementing a Custom Sensor Adapter

To integrate a proprietary or non-standard transducer into AQUA CREW:

1. Create a new adapter file in `apps/api/app/services/iot/adapters/my_sensor_adapter.py`.
2. Subclass `BaseSensorAdapter` and implement `normalize(raw_input: Dict[str, Any]) -> NormalizedTelemetry`.
3. Register the adapter in `apps/api/app/services/iot/adapters/adapter_factory.py`.

### Example Adapter Implementation
```python
from datetime import datetime, timezone
from typing import Dict, Any
from app.services.iot.adapters.base_adapter import BaseSensorAdapter, NormalizedTelemetry

class ChlorineResidualAdapter(BaseSensorAdapter):
    def __init__(self):
        # 0.0 to 5.0 mg/L standard free chlorine in potable water
        super().__init__(expected_unit="mg/L", min_range=0.0, max_range=5.0)

    def normalize(self, raw_input: Dict[str, Any]) -> NormalizedTelemetry:
        raw_val = float(raw_input.get("value", raw_input.get("chlorine_mg_l", 0.0)))
        in_range, range_err = self.validate_range(raw_val)

        quality = "VALID" if in_range else "SUSPECT"
        ts_raw = raw_input.get("timestamp")
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")) if ts_raw else datetime.now(timezone.utc)

        return NormalizedTelemetry(
            device_id=str(raw_input.get("device_id", "DEV-CHLORINE-01")),
            sensor_id=str(raw_input.get("sensor_id", f"{raw_input.get('device_id', 'DEV')}-CL")),
            sensor_type="chlorine_residual",
            measurement_value=round(raw_val, 3),
            unit="mg/L",
            timestamp=ts,
            sequence_number=int(raw_input.get("seq", 1)),
            raw_payload=raw_input,
            data_quality=quality,
            provenance=str(raw_input.get("provenance", "MEASURED")),
            metadata={"range_warning": range_err},
        )
```

---

## 3. ESP32 Arduino / C++ Gateway Example

Below is a reference firmware implementation for an ESP32-S3 microcontroller reading a piezoresistive pressure transducer (4-20mA converted to ADC) and transmitting via MQTT over TLS:

```cpp
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "MUNICIPAL_UTILITY_WIFI";
const char* password = "SECURE_WPA3_KEY";
const char* mqtt_server = "api.aquacrew.internal";
const int mqtt_port = 8883;
const char* device_id = "DEV-PRESSURE-02";
const char* device_api_key = "aqdev_dev-pr_exampleKey1234567890";

WiFiClientSecure espClient;
PubSubClient client(espClient);
unsigned long seq = 0;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  // Load root CA certificate for mutual TLS
  espClient.setCACert(root_ca_pem);
  client.setServer(mqtt_server, mqtt_port);
}

void publishPressure() {
  int raw_adc = analogRead(34);
  float voltage = (raw_adc / 4095.0) * 3.3;
  float pressure_bar = (voltage - 0.5) * (16.0 / 2.0); // 0.5V to 2.5V maps to 0 to 16 bar

  StaticJsonDocument<256> doc;
  doc["version"] = "1.0";
  doc["device_id"] = device_id;
  doc["sensor_id"] = "SNS-PR-02-A";
  doc["sensor_type"] = "pressure";
  doc["value"] = pressure_bar;
  doc["unit"] = "bar";
  doc["seq"] = ++seq;
  doc["provenance"] = "MEASURED";

  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);

  String topic = "aquacrew/devices/" + String(device_id) + "/telemetry";
  client.publish(topic.c_str(), jsonBuffer);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
  publishPressure();
  delay(1000); // 1 Hz sampling
}
```

---

## 4. Hardware Integration Safety Checklist

Before commissioning any new field device:
- [x] Device is registered in AQUA CREW catalog via `POST /api/v1/iot/devices`.
- [x] Initial API key received and loaded securely onto edge hardware.
- [x] Certified ISO 17025 calibration record registered via `POST /api/v1/iot/calibration`.
- [x] Zero physical valve or pump control lines connected to microcontroller GPIO.
- [x] Local store-and-forward buffer verified with at least 500 records retention.
- [x] Ingestion verified via command center at `/app/iot-devices`.

