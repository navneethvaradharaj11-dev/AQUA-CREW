# AQUA CREW — TASK 17: DATABASE RELIABILITY, POOLING & CONCURRENCY GUARDS

## 1. Storage Architecture Overview

AQUA CREW relies on a dual-engine database architecture:
- **Production**: PostgreSQL 16 with PostGIS 3.4 spatial extensions for GIS pipeline features, network topology, high-concurrency connection pooling, and multi-tenant isolation.
- **Development & Hermetic Testing**: SQLite in WAL (Write-Ahead Logging) mode and in-memory isolated instances for unit test hermeticity.

---

## 2. Connection Pool Hardening

In `apps/api/app/database/session.py`, production PostgreSQL connections are managed with robust enterprise connection pooling parameters:

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,          # 20 persistent connections
    max_overflow=settings.DB_MAX_OVERFLOW,    # 10 burst connections (30 total)
    pool_timeout=settings.DB_POOL_TIMEOUT,    # 30 seconds wait before failure
    pool_recycle=settings.DB_POOL_RECYCLE,    # 1800s (30m) to prevent stale connections
    pool_pre_ping=True,                       # Validates socket health before checkout
)
```

### Automatic Reconnect & Health Check (`pool_pre_ping=True`)
The `pool_pre_ping` mechanism executes an optimistic lightweight query (e.g., `SELECT 1`) prior to handing a connection to a request. If the database server was restarted or a network blip dropped the socket, SQLAlchemy transparently recycles the stale socket and re-establishes a fresh connection without surfacing 500 errors to the API caller.

---

## 3. Transactional Integrity & Rollback Safeguards

Database session lifetimes are strictly bounded by FastAPI dependency injection:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

- **Deterministic Rollback**: Any unhandled exception or business logic failure immediately aborts open database transactions, preventing partial writes or corrupted relational graphs.
- **Connection Leak Prevention**: The `finally: db.close()` guarantee ensures connections are immediately returned to the pool regardless of outcome.

---

## 4. Concurrency Race Condition Guards

### Atomic Check-and-Set Rover Assignment
In high-concurrency environments, multiple operators or automated dispatch routines might attempt to assign different missions to the same idle rover simultaneously. A traditional read-modify-write pattern causes a race condition:
1. Dispatcher A reads Rover 1 (state: IDLE).
2. Dispatcher B reads Rover 1 (state: IDLE).
3. Dispatcher A assigns Mission A.
4. Dispatcher B assigns Mission B (overwriting Mission A).

**AQUA CREW Atomic Resolution (`apps/api/app/services/mission_service.py`)**:
```python
updated_count = (
    db.query(RoverModel)
    .filter(
        RoverModel.id == rover_id,
        RoverModel.operating_state == "IDLE",
        RoverModel.assigned_mission_id.is_(None),
    )
    .update({"assigned_mission_id": mission_id}, synchronize_session=False)
)
db.commit()

if updated_count == 0:
    raise AquaCrewException(
        status_code=409,
        code="ROVER_CONCURRENT_ASSIGNMENT_CONFLICT",
        message=f"Rover {rover_id} is no longer available or was concurrently assigned.",
    )
```
The database executes the check and mutation as a single atomic operation. The second concurrent request observes `updated_count == 0` and is cleanly rejected with HTTP 409 Conflict.

---

## 5. Schema Evolution & Migration Strategy

- **Alembic Versioning**: All schema alterations are versioned in `apps/api/alembic/versions/`.
- **Zero-Downtime Safe DDL**:
  - New columns use nullable fields or safe server defaults (`DEFAULT 0`).
  - No locking table rewrites in live production.
  - Foreign key constraints use cascading rules designed to prevent orphaned records.

