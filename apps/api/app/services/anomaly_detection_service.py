"""
Unsupervised Anomaly Detection Service
Employs Isolation Forest for continuous sensor behavior anomaly scoring.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, Tuple


class AnomalyDetectionService:
    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.15,
            random_state=self.random_seed,
            n_jobs=1,
        )
        self._is_fitted = False
        self._fit_synthetic_baseline()

    def _fit_synthetic_baseline(self):
        """
        Fits Isolation Forest on synthetic nominal baseline features.
        """
        rng = np.random.default_rng(self.random_seed)
        n_samples = 400

        # Nominal feature distributions:
        # rms ~ 0.08, dom_freq ~ 150 Hz, centroid ~ 250 Hz, leak_ratio ~ 0.12, delta_p ~ 0.05, delta_q ~ 1.0, delta_m ~ 0.5
        rms = rng.normal(0.08, 0.02, n_samples)
        dom_freq = rng.normal(150.0, 30.0, n_samples)
        centroid = rng.normal(250.0, 40.0, n_samples)
        leak_ratio = rng.normal(0.12, 0.04, n_samples)
        delta_p = rng.exponential(0.05, n_samples)
        delta_q = rng.exponential(1.0, n_samples)
        delta_m = rng.exponential(0.5, n_samples)
        delta_t = rng.normal(0.5, 0.2, n_samples)
        reliability = rng.uniform(0.90, 1.0, n_samples)
        diam = rng.choice([200.0, 300.0, 450.0, 600.0], n_samples)
        mat = rng.choice([1.0, 2.0, 3.0, 4.0], n_samples)
        pressure = rng.normal(4.5, 0.3, n_samples)

        X_nominal = np.column_stack([
            rms, dom_freq, centroid, leak_ratio,
            delta_p, delta_q, delta_m, delta_t,
            reliability, diam, mat, pressure
        ])

        self.model.fit(X_nominal)
        self._is_fitted = True

    def compute_anomaly_score(self, feature_vector: np.ndarray) -> Tuple[float, bool]:
        """
        Computes anomaly score scaled to [0.0, 1.0] and returns (anomaly_score, is_anomaly).
        Higher score represents higher degree of anomaly.
        """
        if not self._is_fitted:
            self._fit_synthetic_baseline()

        X = feature_vector.reshape(1, -1)
        raw_score = float(self.model.score_samples(X)[0])
        # raw_score is typically around -0.4 (nominal) to -0.8 (extreme outlier)
        # We scale raw_score to [0.0, 1.0] where 1.0 is extreme anomaly
        # Typically: score < -0.6 is anomalous
        normalized_score = float(np.clip(1.0 - (raw_score + 0.8) / 0.5, 0.0, 1.0))

        pred = int(self.model.predict(X)[0])
        is_anomaly = bool(pred == -1 or normalized_score >= 0.55)

        return round(normalized_score, 4), is_anomaly


# Singleton instance
anomaly_engine = AnomalyDetectionService()
