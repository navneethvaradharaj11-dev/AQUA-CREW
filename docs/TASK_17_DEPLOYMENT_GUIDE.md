# AQUA CREW — TASK 17: PRODUCTION DEPLOYMENT & CONTAINERIZATION GUIDE

## 1. Containerization Architecture

AQUA CREW employs multi-stage Docker container builds to minimize container attack surface, achieve minimal image footprint, and run under unprivileged system users.

### Container Images Overview:
1. **API Image (`docker/Dockerfile.api`)**:
   - Base: `python:3.11-slim-bookworm`
   - Multi-stage build separates compiler toolchains from final runtime image.
   - Non-root user: `appuser` (UID 10001).
   - Bundles `wntr`, `scipy`, `numpy`, `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`.
   - Embedded Docker `HEALTHCHECK` probing `GET /api/v1/health/liveness`.
2. **Web Frontend Image (`docker/Dockerfile.web`)**:
   - Base: `node:20-alpine`
   - Multi-stage build: dependency resolution $\to$ Next.js standalone build $\to$ minimal runtime.
   - Non-root user: `nextjs` (UID 10001).
   - Embedded Docker `HEALTHCHECK` probing `GET /api/health` or `GET /`.
3. **Database (`postgis/postgis:16-3.4`)**:
   - PostgreSQL 16 engine with PostGIS 3.4 geospatial extension enabled.

---

## 2. Docker Compose Deployment

The root `docker-compose.yml` orchestrates the local or single-node production deployment:

```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:16-3.4
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-aquacrew}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-aquacrew_secure_pass_2026!}
      POSTGRES_DB: ${POSTGRES_DB:-aquacrew_prod}
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aquacrew -d aquacrew_prod"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      API_ENV: production
      DATABASE_URL: postgresql://aquacrew:${POSTGRES_PASSWORD}@db:5432/aquacrew_prod
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      REQUIRE_AUTH: "true"
      CORS_ORIGINS: '["https://aquacrew.internal"]'
    ports:
      - "8000:8000"

  web:
    build:
      context: .
      dockerfile: docker/Dockerfile.web
    restart: unless-stopped
    depends_on:
      api:
        condition: service_healthy
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_API_URL: https://api.aquacrew.internal
    ports:
      - "3000:3000"

volumes:
  db_data:
```

---

## 3. Kubernetes Manifests Specification

For cloud-native Kubernetes deployments, standard manifests are provided:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aquacrew-api
  labels:
    app: aquacrew-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aquacrew-api
  template:
    metadata:
      labels:
        app: aquacrew-api
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        readOnlyRootFilesystem: true
      containers:
      - name: api
        image: aquacrew/api:1.0.0
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /api/v1/health/liveness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 15
        readinessProbe:
          httpGet:
            path: /api/v1/health/readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        envFrom:
        - secretRef:
            name: aquacrew-secrets
        - configMapRef:
            name: aquacrew-config
```

---

## 4. Production Security Deployment Checklist

Before enabling live ingress traffic, operators must verify:
- [x] `API_ENV=production` is set in the runtime environment.
- [x] `JWT_SECRET_KEY` is a randomly generated secret $\ge 32$ characters long (not the default dev key).
- [x] `REQUIRE_AUTH=true` is strictly enforced.
- [x] `DATABASE_URL` targets PostgreSQL 16 (SQLite is strictly rejected by `validate_production_security()`).
- [x] `CORS_ORIGINS` contains explicit production domain names (wildcard `*` is rejected at startup).
- [x] TLS 1.3 is terminated at the ingress controller with valid CA certificates.
- [x] Container filesystem is mounted read-only (`readOnlyRootFilesystem: true`).
- [x] Containers run as non-root users (`appuser` / `nextjs`).

