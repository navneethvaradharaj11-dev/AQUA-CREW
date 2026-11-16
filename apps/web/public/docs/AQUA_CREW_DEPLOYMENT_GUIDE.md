# AQUA CREW — Production Deployment & Infrastructure Guide
**Release:** v1.0.0-rc1  
**Target Architecture:** Multi-Container Production Stack with Nginx Gateway, PostgreSQL/PostGIS, Mosquitto MQTT, and FastAPI/Next.js Services  

---

## 1. Production Architecture Overview

The production deployment of AQUA CREW is containerized using Docker and orchestrated via Docker Compose. The topology isolates internal microservice networks while exposing a single hardened entry point via an Nginx reverse proxy.

```mermaid
graph TD
    User["Public Internet (HTTPS / Port 443 / 80)"] --> Gateway["gateway: Nginx Reverse Proxy"]
    
    subgraph InternalDMZ ["Internal Docker Bridge Network (aquacrew-net)"]
        Gateway -->|Reverse Proxy /| Web["web: Next.js 14 (:3000)"]
        Gateway -->|Reverse Proxy /api/*| API["api: FastAPI ASGI (:8000)"]
        Gateway -->|WebSocket /ws/*| API
        Gateway -->|WebSocket /mqtt/*| Mosquitto["mosquitto: MQTT Broker (:9001)"]
        
        API -->|SQL Port 5432| DB[("postgres: PostGIS 15 DB")]
        API -->|MQTT Port 1883| Mosquitto
    end
```

---

## 2. Docker Compose Multi-Service Configuration

The platform orchestrates five dedicated services in [docker-compose.yml](file:///e:/BRIDGE%20ASSIGNMENTS/Aqua%20Crew/docker-compose.yml):

| Service Name | Base Image | Internal Port | External Port | Role |
| :--- | :--- | :--- | :--- | :--- |
| `gateway` | `nginx:1.25-alpine` | `80`, `443` | `80`, `443` | Reverse proxy, static asset caching, TLS termination, WebSocket upgrade. |
| `web` | `node:20-alpine` | `3000` | Isolated | Next.js production server running pre-compiled standalone artifacts. |
| `api` | `python:3.11-slim` | `8000` | Isolated | FastAPI application server powered by Uvicorn ASGI workers. |
| `postgres` | `postgis/postgis:15-3.3-alpine` | `5432` | Isolated | Relational spatial database with persistent storage volume `pgdata`. |
| `mosquitto` | `eclipse-mosquitto:2.0` | `1883`, `9001` | `1883`, `9001` | High-throughput MQTT broker for edge IoT telemetry and WebSockets. |

---

## 3. Production Deployment Step-by-Step

### 3.1 Server Provisioning & Prerequisites
Install Docker Engine and Docker Compose on Ubuntu 22.04 LTS:
```bash
sudo apt update && sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### 3.2 Environment Secrets Configuration
Create `.env` in the repository root (do not commit to version control):
```dotenv
# Production Database Credentials
POSTGRES_USER=aquacrew_admin
POSTGRES_PASSWORD=UltraSecurePostgresPassword2026!
POSTGRES_DB=aquacrew_prod
DATABASE_URL=postgresql://aquacrew_admin:UltraSecurePostgresPassword2026!@postgres:5432/aquacrew_prod

# Backend Security & JWT
SECRET_KEY=e839f9b48c7361a8123de2189cb79b8f10283c8471829a8d9f9a8b7c6d5e4f3a
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=production
HARDWARE_ACTUATION_ENABLED=false

# MQTT Broker
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883

# Frontend URLs
NEXT_PUBLIC_API_URL=http://yourdomain.com
NEXT_PUBLIC_WS_URL=ws://yourdomain.com/ws
```

### 3.3 Build & Launch Containers
```bash
# Build production images and start in background
docker compose up -d --build

# Inspect running container health
docker compose ps
```

### 3.4 Execute Database Migrations and Seed
```bash
docker compose exec api python -m alembic upgrade head
docker compose exec api python -m app.db.seed_system_state
```

---

## 4. Reverse Proxy & WebSocket Configuration

The gateway uses the optimized configuration in [docker/nginx.conf](file:///e:/BRIDGE%20ASSIGNMENTS/Aqua%20Crew/docker/nginx.conf):
- **Upstream Timeouts:** Configured to `300s` for long-running hydraulic simulations.
- **WebSocket Headers:** `Upgrade $http_upgrade` and `Connection "upgrade"` mapped for `/ws/` routes.
- **Client Max Body Size:** Configured to `50M` to support GIS shapefile and EPANET `.inp` uploads.

---

## 5. Health Monitoring & Verification

Validate production health via automated probes:
- **API Health:** `curl -f http://localhost/api/v1/incidents/stats/overview`
- **Frontend Health:** `curl -f -I http://localhost`
- **Postgres Readiness:** `docker compose exec postgres pg_isready -U aquacrew_admin -d aquacrew_prod`
- **MQTT Broker Check:** `mosquitto_sub -h localhost -p 1883 -t "aquacrew/heartbeat" -C 1`

