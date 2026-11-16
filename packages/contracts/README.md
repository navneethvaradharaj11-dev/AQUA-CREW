# @aqua-crew/contracts

Shared data contracts, API response envelopes, and telemetry schemas for the AQUA CREW platform.

## Structure
- `src/`: TypeScript definitions (`api.ts`, `telemetry.ts`) used across frontend applications.
- `python/`: Pydantic v2 schemas used across backend services, simulation engines, and AI workers.

## Guiding Principles
- Any modification to rover telemetry or core API responses begins here.
- Strict typing ensures frontend and backend never diverge during subsequent feature milestones.

