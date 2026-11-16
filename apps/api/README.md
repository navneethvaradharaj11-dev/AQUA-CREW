# AQUA CREW — API Backend Service

The core REST API and WebSocket gateway for the AQUA CREW platform, built with Python, FastAPI, and Pydantic.

## Prerequisites
- Python 3.11+
- Virtual environment (`venv`)

## Getting Started

1. Navigate to the API directory:
   ```bash
   cd apps/api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Explore the interactive documentation:
   - OpenAPI Swagger UI: `http://localhost:8000/api/v1/docs`
   - ReDoc: `http://localhost:8000/api/v1/redoc`
   - Health Check: `http://localhost:8000/api/v1/health`

