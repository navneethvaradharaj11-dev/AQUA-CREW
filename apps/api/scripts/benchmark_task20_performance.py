"""
AQUA CREW — Comprehensive System Performance & Reliability Benchmark (Task 20)
Measures latency profiles, memory footprints, and throughput across:
1. Telemetry Ingestion & Normalization
2. Acoustic Signal Feature Extraction & AI Classification
3. Hydraulic Digital Twin Simulation
4. Incident Lifecycle State Transitions & Human Approval Signatures
5. Master 15-Step End-to-End Incident Lifecycle
"""
import os
import sys
import time
import json
import statistics
import tracemalloc
from datetime import datetime, timezone

# Add app to PYTHONPATH
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.database.session import Base, SessionLocal, init_db, engine
from app.repositories import (
    RoverRepository,
    MissionRepository,
    PipelineRepository,
    UserRepository,
    IncidentRepository,
)
from app.repositories.repair_repository import RepairRepository
from app.repositories.iot_repository import IotRepository
from app.services.incident_orchestration_service import IncidentOrchestrationService


def run_benchmark():
    print("=" * 70)
    print("AQUA CREW — TASK 20 COMPREHENSIVE PERFORMANCE & LATENCY BENCHMARK")
    print("=" * 70)

    tracemalloc.start()
    init_db()

    with SessionLocal() as db:
        UserRepository.seed_defaults(db)
        PipelineRepository.seed_defaults(db)
        RoverRepository.seed_defaults(db)
        MissionRepository.seed_defaults(db)
        RepairRepository.seed_default_crews(db)
        IotRepository.seed_defaults(db)
        IncidentRepository.seed_defaults(db)

    results = {}

    # 1. Telemetry Ingestion & Calibration Check Latency (500 iterations)
    ingest_times = []
    with SessionLocal() as db:
        for i in range(500):
            t0 = time.perf_counter()
            _ = IncidentOrchestrationService.execute_stage_1_telemetry_ingest(
                db=db,
                device_id="DEV-ACOUSTIC-01",
                sensor_id="SNS-AC-01-A",
                acoustic_db=75.0 + (i % 25),
                frequency_hz=1200.0 + (i % 300),
            )
            ingest_times.append((time.perf_counter() - t0) * 1000.0)

    results["telemetry_ingestion_ms"] = {
        "iterations": len(ingest_times),
        "mean_ms": round(statistics.mean(ingest_times), 3),
        "median_ms": round(statistics.median(ingest_times), 3),
        "p95_ms": round(statistics.quantiles(ingest_times, n=20)[18], 3),
        "min_ms": round(min(ingest_times), 3),
        "max_ms": round(max(ingest_times), 3),
    }

    # 2. AI Acoustic Leak Classification Latency (500 iterations)
    sample_telemetry = IncidentOrchestrationService.execute_stage_1_telemetry_ingest(
        db=None,
        device_id="DEV-ACOUSTIC-01",
        sensor_id="SNS-AC-01-A",
        acoustic_db=88.5,
        frequency_hz=1450.0,
    )
    ai_times = []
    for _ in range(500):
        t0 = time.perf_counter()
        _ = IncidentOrchestrationService.execute_stage_2_ai_leak_detection(sample_telemetry)
        ai_times.append((time.perf_counter() - t0) * 1000.0)

    results["ai_inference_ms"] = {
        "iterations": len(ai_times),
        "mean_ms": round(statistics.mean(ai_times), 3),
        "median_ms": round(statistics.median(ai_times), 3),
        "p95_ms": round(statistics.quantiles(ai_times, n=20)[18], 3),
        "min_ms": round(min(ai_times), 3),
        "max_ms": round(max(ai_times), 3),
    }

    # 3. Master 15-Step End-to-End Incident Lifecycle Execution (50 iterations)
    e2e_times = []
    with SessionLocal() as db:
        for _ in range(50):
            t0 = time.perf_counter()
            scenario_res = IncidentOrchestrationService.run_master_e2e_scenario(
                db=db,
                actor_id="USR-ENG-01",
                actor_role="ENGINEER",
                pipeline_segment_id="PIPE-SEC-4B-92",
                acoustic_db=89.5,
            )
            e2e_times.append((time.perf_counter() - t0) * 1000.0)

    results["master_e2e_lifecycle_ms"] = {
        "iterations": len(e2e_times),
        "mean_ms": round(statistics.mean(e2e_times), 3),
        "median_ms": round(statistics.median(e2e_times), 3),
        "p95_ms": round(statistics.quantiles(e2e_times, n=20)[18], 3),
        "min_ms": round(min(e2e_times), 3),
        "max_ms": round(max(e2e_times), 3),
    }

    # 4. Final Incident Dossier Compilation Latency (100 iterations)
    report_times = []
    with SessionLocal() as db:
        for _ in range(100):
            t0 = time.perf_counter()
            _ = IncidentOrchestrationService.generate_final_incident_report(db, "INC-2026-001")
            report_times.append((time.perf_counter() - t0) * 1000.0)

    results["dossier_compilation_ms"] = {
        "iterations": len(report_times),
        "mean_ms": round(statistics.mean(report_times), 3),
        "median_ms": round(statistics.median(report_times), 3),
        "p95_ms": round(statistics.quantiles(report_times, n=20)[18], 3),
        "min_ms": round(min(report_times), 3),
        "max_ms": round(max(report_times), 3),
    }

    # 5. Clean Reset Execution Latency
    reset_times = []
    with SessionLocal() as db:
        for _ in range(10):
            t0 = time.perf_counter()
            _ = IncidentOrchestrationService.reset_demo_scenario(db)
            reset_times.append((time.perf_counter() - t0) * 1000.0)

    results["demo_reset_ms"] = {
        "iterations": len(reset_times),
        "mean_ms": round(statistics.mean(reset_times), 3),
        "median_ms": round(statistics.median(reset_times), 3),
        "min_ms": round(min(reset_times), 3),
        "max_ms": round(max(reset_times), 3),
    }

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results["memory_usage_mb"] = {
        "current_mb": round(current_mem / (1024 * 1024), 2),
        "peak_mb": round(peak_mem / (1024 * 1024), 2),
    }

    results["benchmark_metadata"] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": "TASK_20_FINAL_PRODUCT_RELEASE",
        "python_version": sys.version.split()[0],
        "hardware_actuation_enabled": False,
        "environment": "SIMULATION_FIRST_SANDBOX",
    }

    REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
    output_path = os.path.join(REPO_ROOT, "docs", "benchmark_metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nBENCHMARK RESULTS SUMMARY:")
    print(f"  1. Telemetry Ingestion Latency:    Mean {results['telemetry_ingestion_ms']['mean_ms']} ms (P95: {results['telemetry_ingestion_ms']['p95_ms']} ms)")
    print(f"  2. AI Inference Latency:           Mean {results['ai_inference_ms']['mean_ms']} ms (P95: {results['ai_inference_ms']['p95_ms']} ms)")
    print(f"  3. Master E2E Lifecycle (15-step): Mean {results['master_e2e_lifecycle_ms']['mean_ms']} ms (P95: {results['master_e2e_lifecycle_ms']['p95_ms']} ms)")
    print(f"  4. Final Dossier Compilation:      Mean {results['dossier_compilation_ms']['mean_ms']} ms (P95: {results['dossier_compilation_ms']['p95_ms']} ms)")
    print(f"  5. Demo Scenario Reset:            Mean {results['demo_reset_ms']['mean_ms']} ms")
    print(f"  6. Peak Memory Footprint:          {results['memory_usage_mb']['peak_mb']} MB")
    print(f"\nSaved metrics to: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
