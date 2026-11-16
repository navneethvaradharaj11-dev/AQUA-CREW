# AQUA CREW — LLM PROVIDER INTEGRATION & DETERMINISTIC FALLBACK ARCHITECTURE
## Task 13 Technical Guide & Provider Reference

### 1. Dual-Engine Inference Philosophy
AQUA CREW employs a flexible, resilient model integration strategy designed for mission-critical infrastructure operations:
1. **Configurable Cloud & On-Premises Inference**: Seamless support for NVIDIA NIM microservices (e.g., Meta Llama 3.1 70B Instruct, Mistral Mixtral 8x22B) and OpenAI-compatible endpoints.
2. **Deterministic Grounded Fallback Engine**: An embedded rule-based reasoning engine that functions completely offline without internet connectivity, external API keys, or GPU hardware, providing 100% reliable, hallucination-free decision support.

---

### 2. Configuration Parameters
All AI engine settings are configured via environment variables prefixed with `AQUA_` (in `apps/api/app/config.py`):

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `AQUA_AI_PROVIDER` | `str` | `"DETERMINISTIC"` | Active provider: `DETERMINISTIC`, `NVIDIA_NIM`, or `OPENAI`. |
| `AQUA_AI_BASE_URL` | `str` | `None` | Endpoint base URL (e.g. `https://integrate.api.nvidia.com/v1`). |
| `AQUA_AI_MODEL` | `str` | `"meta/llama-3.1-70b-instruct"` | Primary generative model identifier. |
| `AQUA_AI_API_KEY` | `str` | `None` | API bearer token or NIM API key (credentials masked in API). |
| `AQUA_AI_TIMEOUT` | `float` | `30.0` | Maximum HTTP connection and socket read timeout in seconds. |
| `AQUA_AI_MAX_TOKENS` | `int` | `2048` | Maximum output generation token budget. |
| `AQUA_AI_TEMPERATURE`| `float` | `0.2` | Temperature setting (low value for factual precision). |

---

### 3. Provider Architecture & Factory Pattern
The `AIProviderFactory` manages instantiation and automatic failover:

```
                  +-----------------------------------+
                  |        AIProviderFactory          |
                  +-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
  (Valid API Key Present)                         (No Key / Error / Timeout)
            |                                               |
            v                                               v
+-------------------------+                     +-------------------------+
|    OpenAINimProvider    |                     |  DeterministicProvider  |
|  - NVIDIA NIM Endpoint  |  --- Failover --->  |  - 100% Local / Offline |
|  - OpenAI-Compatible    |   on Exception      |  - Zero Hallucination   |
|  - Grounded Sys Prompt  |                     |  - Rule-Based Answers   |
+-------------------------+                     +-------------------------+
```

#### Automatic Failover Trigger Conditions:
1. `AQUA_AI_API_KEY` is empty, unset, or whitespace.
2. HTTP connection failure, DNS resolution error, or network timeout (> 30s).
3. Non-200 HTTP response status (e.g. 401 Unauthorized, 429 Rate Limit, 503 Service Unavailable).
4. Invalid or unparseable JSON payload returned by external endpoint.

---

### 4. Deterministic Grounded Engine (`DeterministicProvider`)
When operating in deterministic mode:
- **Model Identifier**: `deterministic-grounded-engine`
- **Provider Identifier**: `DETERMINISTIC`
- **Execution**: Evaluates the detected query intent and structured operational context to generate rigorous engineering explanations formatted in GitHub Flavored Markdown.
- **Precision**: Synthesizes exact equations (Torricelli, Todini, Hazen-Williams), verified percentages, and physical asset parameters directly from the SQLite/PostgreSQL database.
- **Zero Cost**: Eliminates token billing costs and external network latency.

---

### 5. Secret Protection & API Telemetry
The platform enforces strict credential protection:
- `GET /api/v1/advanced-ai/providers`: Exposes provider status and active model, but masks all API keys (e.g. `nvapi...39a1` or `"configured"`).
- Never writes external API keys to database tables, conversation history, or log files.
- All requests and responses are tagged with `is_simulated: true` and `source: "VIRTUAL_SIMULATION_ENGINE"`.

