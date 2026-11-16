"""
Automated Test Suite for Task 07: AI-Powered Leak Detection & Acoustic Intelligence
Tests signal processing, feature extraction, anomaly detection, classification, risk, localization, and REST API.
"""
import pytest
import numpy as np

from app.schemas.ai import (
    SyntheticWaveformRequest,
    SensorReadingCreate,
    LeakAnalyzeRequest,
)
from app.services.signal_processing_service import SignalProcessingService
from app.services.sensor_ingestion_service import SensorIngestionService
from app.services.feature_extraction_service import FeatureExtractionService
from app.services.anomaly_detection_service import AnomalyDetectionService
from app.services.leak_classification_service import LeakClassificationService
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.leak_localization_service import LeakLocalizationService


# --- 1. Signal Processing & Waveform Synthesis Tests ---

def test_synthetic_waveform_generation():
    req = SyntheticWaveformRequest(
        scenario="MODERATE_LEAK",
        duration_seconds=0.5,
        sampling_rate_hz=8000,
        noise_level=0.1,
    )
    waveform, t, dt = SignalProcessingService.generate_synthetic_waveform(req)
    assert len(waveform) == 4000
    assert len(t) == 4000
    assert dt == 1.0 / 8000.0


def test_acoustic_feature_extraction():
    req = SyntheticWaveformRequest(
        scenario="MINOR_LEAK",
        duration_seconds=1.0,
        sampling_rate_hz=8000,
    )
    waveform, _, _ = SignalProcessingService.generate_synthetic_waveform(req)
    feats = SignalProcessingService.extract_acoustic_features(waveform, 8000)

    assert feats.rms_amplitude > 0.0
    assert feats.peak_amplitude >= feats.rms_amplitude
    assert feats.dominant_frequency_hz > 500.0  # Leak hiss is in acoustic leak band
    assert feats.leak_band_energy_ratio > 0.0
    assert isinstance(feats.snr_db, float)


def test_waveform_analysis_for_ui_visualization():
    req = SyntheticWaveformRequest(
        scenario="MAJOR_LEAK",
        duration_seconds=1.0,
        sampling_rate_hz=8000,
    )
    resp = SignalProcessingService.analyze_synthetic_scenario(req)
    assert len(resp.time_series_sample) == 100
    assert len(resp.fft_spectrum_sample) > 0
    assert resp.is_simulated is True
    assert "Synthetic waveform" in resp.disclaimer


# --- 2. Sensor Ingestion & Quality Validation Tests ---

def test_sensor_ingestion_valid_reading(db_session):
    reading = SensorReadingCreate(
        sensor_id="SNS-AC-TEST-01",
        sensor_type="acoustic",
        pipeline_segment_id="PIPE-SEC-4B-92",
        measurement_value=68.5,
        measurement_unit="dB",
    )
    res = SensorIngestionService.ingest_reading(db_session, reading)
    assert res.id.startswith("READ-")
    assert res.quality_indicator in ["EXCELLENT", "GOOD"]
    assert res.is_simulated is True


def test_sensor_ingestion_outlier_rejection(db_session):
    reading = SensorReadingCreate(
        sensor_id="SNS-PRES-TEST-01",
        sensor_type="pressure",
        pipeline_segment_id="PIPE-SEC-4B-92",
        measurement_value=999.0,  # Exceeds physical bound of 16 bar
        measurement_unit="bar",
    )
    res = SensorIngestionService.ingest_reading(db_session, reading)
    assert res.id.startswith("SNS-ERR-")
    assert res.quality_indicator == "FAULT"


# --- 3. Feature Extraction Tests ---

def test_feature_vector_dimension_and_mapping():
    req = LeakAnalyzeRequest(
        pipeline_segment_id="PIPE-SEC-4B-92",
        pressure_bar=3.6,
        expected_pressure_bar=4.5,
        flow_rate_m3h=62.0,
        expected_flow_m3h=50.0,
        ground_moisture_pct=26.0,
        baseline_moisture_pct=15.0,
        acoustic_scenario="MODERATE_LEAK",
    )
    vec, named = FeatureExtractionService.extract_feature_vector(req)
    assert len(vec) == 12
    assert named["pressure_deviation_bar"] == pytest.approx(0.9, rel=1e-2)
    assert named["flow_deviation_m3h"] == pytest.approx(12.0, rel=1e-2)
    assert named["moisture_deviation_pct"] == pytest.approx(11.0, rel=1e-2)


# --- 4. Anomaly Detection Tests ---

def test_anomaly_detection_nominal_vs_anomaly():
    engine = AnomalyDetectionService(random_seed=42)

    # Nominal feature vector
    nominal_vec = np.array([0.08, 140.0, 240.0, 0.12, 0.05, 0.5, 0.5, 0.2, 0.98, 300.0, 1.0, 4.5])
    score_nom, is_anom_nom = engine.compute_anomaly_score(nominal_vec)
    assert score_nom < 0.65

    # Extreme anomaly feature vector
    anom_vec = np.array([0.95, 2200.0, 2400.0, 0.92, 2.5, 35.0, 28.0, 4.5, 0.90, 600.0, 2.0, 4.5])
    score_anom, is_anom_anom = engine.compute_anomaly_score(anom_vec)
    assert score_anom > score_nom
    assert is_anom_anom is True


# --- 5. Supervised Classification & Metrics Tests ---

def test_leak_classification_and_metrics():
    clf_engine = LeakClassificationService(random_seed=42)
    metrics = clf_engine.get_model_metrics()

    assert "random_forest" in metrics
    assert "logistic_regression" in metrics
    rf_m = metrics["random_forest"]
    assert rf_m["accuracy"] > 0.70  # Authentic un-manufactured score
    assert rf_m["f1_macro"] > 0.70

    # Test inference
    test_vec = np.array([0.85, 1900.0, 2100.0, 0.88, 1.8, 25.0, 18.0, 3.2, 0.95, 450.0, 1.0, 4.5])
    named = {"rms_amplitude": 0.85, "pressure_deviation_bar": 1.8}
    pred_class, conf, attributions = clf_engine.classify_features(test_vec, named)

    assert pred_class in ["MEDIUM_LEAK_PROBABILITY", "HIGH_LEAK_PROBABILITY"]
    assert 0.0 <= conf <= 1.0
    assert len(attributions) > 0


# --- 6. Risk Assessment Tests ---

def test_risk_assessment_critical_rule():
    features = {"pressure_deviation_bar": 1.5, "pipe_diameter_mm": 600.0}
    pipe_meta = {"name": "Metro Trunk", "category": "primary"}
    risk, loss_lph, explanation = RiskAssessmentService.evaluate_risk(
        classification="HIGH_LEAK_PROBABILITY",
        confidence=0.92,
        anomaly_score=0.85,
        features=features,
        pipe_meta=pipe_meta,
    )
    assert risk == "CRITICAL"
    assert loss_lph > 1000.0
    assert "critical pipeline segment" in explanation.lower()


# --- 7. TDOA Acoustic Localization Tests ---

def test_tdoa_localization_valid_interpolation():
    pipe_meta = {
        "length_m": 1000.0,
        "material": "ductile_iron",
        "coordinates": [[-74.0150, 40.7100], [-74.0050, 40.7150]],
    }
    # delta_t = 0.0s means exactly mid-point (50%)
    lat, lng, unc, qual, method = LeakLocalizationService.estimate_location_tdoa(
        pipe_meta=pipe_meta,
        delta_t_seconds=0.0,
        snr_db=15.0,
    )
    assert lat is not None
    assert lng is not None
    assert unc is not None and unc < 15.0
    assert qual == "HIGH"
    assert "TDOA" in method


def test_tdoa_localization_low_snr_suppressed():
    pipe_meta = {
        "length_m": 1000.0,
        "material": "ductile_iron",
        "coordinates": [[-74.0150, 40.7100], [-74.0050, 40.7150]],
    }
    # Low SNR (< 5 dB) must suppress fake coordinates
    lat, lng, unc, qual, method = LeakLocalizationService.estimate_location_tdoa(
        pipe_meta=pipe_meta,
        delta_t_seconds=0.1,
        snr_db=3.2,
    )
    assert lat is None
    assert lng is None
    assert qual == "INSUFFICIENT_DATA"
    assert "too low" in method.lower()


# --- 8. REST API Endpoints Integration Tests ---

def test_api_analyze_leak(client):
    payload = {
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "pressure_bar": 3.8,
        "expected_pressure_bar": 4.5,
        "flow_rate_m3h": 65.0,
        "expected_flow_m3h": 50.0,
        "ground_moisture_pct": 24.0,
        "acoustic_scenario": "MODERATE_LEAK",
    }
    res = client.post("/api/v1/ai/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["id"].startswith("DET-")
    assert data["classification"] in [
        "NORMAL", "LOW_LEAK_PROBABILITY", "MEDIUM_LEAK_PROBABILITY", "HIGH_LEAK_PROBABILITY"
    ]
    assert "anomaly_score" in data
    assert "risk_level" in data
    assert data["is_simulated"] is True


def test_api_list_and_get_detections(client):
    # Ensure at least one detection exists
    client.post("/api/v1/ai/analyze", json={
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "pressure_bar": 3.8,
        "acoustic_scenario": "MODERATE_LEAK",
    })
    # Fetch list
    res = client.get("/api/v1/ai/detections")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    det_id = data[0]["id"]
    # Get by ID
    res_single = client.get(f"/api/v1/ai/detections/{det_id}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == det_id


def test_api_update_detection_status(client):
    # Ensure at least one detection exists
    create_res = client.post("/api/v1/ai/analyze", json={
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "pressure_bar": 3.8,
        "acoustic_scenario": "MODERATE_LEAK",
    })
    det_id = create_res.json()["id"]

    # Operator review action
    update_payload = {
        "status": "VERIFIED_BY_OPERATOR",
        "operator_notes": "Acoustic hiss cross-verified with ground moisture. Approving rover inspection."
    }
    patch_res = client.patch(f"/api/v1/ai/detections/{det_id}/status", json=update_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "VERIFIED_BY_OPERATOR"
    assert "Operator Notes:" in data["risk_explanation"]


def test_api_model_info_and_metrics(client):
    res_models = client.get("/api/v1/ai/models")
    assert res_models.status_code == 200
    assert "models" in res_models.json()

    res_metrics = client.get("/api/v1/ai/models/metrics")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    assert "random_forest" in metrics
    assert "accuracy" in metrics["random_forest"]


def test_api_ai_health(client):
    res = client.get("/api/v1/ai/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["is_simulated"] is True
