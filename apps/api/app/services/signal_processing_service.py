"""
Acoustic Signal Processing and Waveform Synthesis Service
Utilizes NumPy and SciPy for synthetic acoustic physics modeling and spectral analysis.
"""
import numpy as np
from scipy import signal
from scipy.fft import rfft, rfftfreq
from typing import Dict, Any, Tuple, List

from app.schemas.ai import SyntheticWaveformRequest, SyntheticWaveformResponse, AcousticFeatures


class SignalProcessingService:
    @staticmethod
    def generate_synthetic_waveform(req: SyntheticWaveformRequest) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Generates synthetic acoustic waveform (amplitude array, time array, dt)
        sampled at sampling_rate_hz for the requested duration.
        """
        fs = req.sampling_rate_hz
        t = np.linspace(0, req.duration_seconds, int(fs * req.duration_seconds), endpoint=False)
        scenario = req.scenario.upper()
        rng = np.random.default_rng(seed=42)

        # Baseline noise (pink/gaussian)
        noise = rng.normal(0, req.noise_level * 0.2, len(t))

        if scenario == "NORMAL_FLOW":
            # Laminar fluid flow: gentle low frequency (< 300 Hz)
            waveform = 0.08 * np.sin(2 * np.pi * 120 * t) + 0.05 * np.sin(2 * np.pi * 220 * t) + noise

        elif scenario == "BACKGROUND_NOISE":
            # Environmental urban surface traffic / seismic rumble (50 - 180 Hz)
            waveform = 0.20 * np.sin(2 * np.pi * 60 * t) + 0.15 * np.sin(2 * np.pi * 110 * t) + (noise * 1.5)

        elif scenario == "MINOR_LEAK":
            # Incipient micro-leak: narrow resonant acoustic hiss at ~1450 Hz
            leak_tone = 0.25 * np.sin(2 * np.pi * 1450 * t) + 0.12 * np.sin(2 * np.pi * 1750 * t)
            flow_carrier = 0.06 * np.sin(2 * np.pi * 180 * t)
            waveform = leak_tone + flow_carrier + noise

        elif scenario == "MODERATE_LEAK":
            # Crack or joint separation: sustained turbulent broadband hiss (1000 - 2400 Hz)
            carrier = 0.45 * np.sin(2 * np.pi * 1350 * t) + 0.35 * np.sin(2 * np.pi * 1850 * t) + 0.25 * np.sin(2 * np.pi * 2200 * t)
            # Add filtered turbulent noise
            turbulent_noise = rng.normal(0, 0.25, len(t))
            waveform = carrier + turbulent_noise + noise

        elif scenario == "MAJOR_LEAK":
            # Pipe rupture: massive high-energy turbulent roar across 600 - 3200 Hz
            broadband = (
                0.80 * np.sin(2 * np.pi * 920 * t)
                + 0.65 * np.sin(2 * np.pi * 1600 * t)
                + 0.55 * np.sin(2 * np.pi * 2450 * t)
                + 0.40 * np.sin(2 * np.pi * 3100 * t)
            )
            cavitation = rng.uniform(-0.4, 0.4, len(t))
            waveform = broadband + cavitation + (noise * 1.8)

        elif scenario == "PRESSURE_TRANSIENT":
            # Water hammer or valve slam: exponential decay shock pulse
            decay = np.exp(-t * 8.0)
            shock = 1.2 * np.sin(2 * np.pi * 85 * t) * decay
            waveform = shock + noise

        elif scenario == "MECHANICAL_VIBRATION":
            # Pump / electrical motor harmonics: 50 Hz, 100 Hz, 150 Hz
            harmonics = (
                0.50 * np.sin(2 * np.pi * 50 * t)
                + 0.35 * np.sin(2 * np.pi * 100 * t)
                + 0.20 * np.sin(2 * np.pi * 150 * t)
            )
            waveform = harmonics + noise

        else:
            # Fallback nominal
            waveform = 0.1 * np.sin(2 * np.pi * 150 * t) + noise

        return waveform, t, 1.0 / fs

    @staticmethod
    def extract_acoustic_features(waveform: np.ndarray, fs: int) -> AcousticFeatures:
        """
        Calculates time-domain and FFT spectral metrics from an acoustic waveform.
        """
        n = len(waveform)
        if n == 0:
            return AcousticFeatures(
                rms_amplitude=0.0,
                peak_amplitude=0.0,
                std_dev=0.0,
                snr_db=0.0,
                dominant_frequency_hz=0.0,
                spectral_centroid_hz=0.0,
                spectral_bandwidth_hz=0.0,
                leak_band_energy_ratio=0.0,
                short_time_energy=0.0,
            )

        # 1. Time-Domain Features
        rms = float(np.sqrt(np.mean(waveform ** 2)))
        peak = float(np.max(np.abs(waveform)))
        std_dev = float(np.std(waveform))
        short_time_energy = float(np.sum(waveform ** 2) / n)

        # 2. Windowing and Spectral Analysis (Hanning window)
        window = np.hanning(n)
        windowed = waveform * window
        fft_vals = np.abs(rfft(windowed))
        freqs = rfftfreq(n, 1.0 / fs)

        total_spectral_energy = np.sum(fft_vals ** 2) + 1e-12

        # Dominant frequency
        dom_idx = int(np.argmax(fft_vals))
        dominant_freq = float(freqs[dom_idx])

        # Spectral Centroid (Center of Mass)
        spectral_centroid = float(np.sum(freqs * fft_vals) / (np.sum(fft_vals) + 1e-12))

        # Spectral Bandwidth (Spread around Centroid)
        spectral_bandwidth = float(np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * fft_vals) / (np.sum(fft_vals) + 1e-12)))

        # Leak band energy ratio (500 Hz - 3000 Hz)
        leak_band_mask = (freqs >= 500.0) & (freqs <= 3000.0)
        leak_band_energy = np.sum(fft_vals[leak_band_mask] ** 2)
        leak_band_ratio = float(leak_band_energy / total_spectral_energy)

        # Signal-to-Noise Ratio (ratio of leak band to non-leak background)
        noise_band_mask = ~leak_band_mask
        noise_energy = np.sum(fft_vals[noise_band_mask] ** 2) + 1e-12
        snr_linear = leak_band_energy / noise_energy
        snr_db = float(10.0 * np.log10(max(snr_linear, 1e-6)))

        return AcousticFeatures(
            rms_amplitude=round(rms, 4),
            peak_amplitude=round(peak, 4),
            std_dev=round(std_dev, 4),
            snr_db=round(snr_db, 2),
            dominant_frequency_hz=round(dominant_freq, 1),
            spectral_centroid_hz=round(spectral_centroid, 1),
            spectral_bandwidth_hz=round(spectral_bandwidth, 1),
            leak_band_energy_ratio=round(leak_band_ratio, 4),
            short_time_energy=round(short_time_energy, 4),
        )

    @classmethod
    def analyze_synthetic_scenario(cls, req: SyntheticWaveformRequest) -> SyntheticWaveformResponse:
        """
        Synthesizes a scenario waveform, computes acoustic features, and produces
        downsampled visual series for UI plotting.
        """
        waveform, t, dt = cls.generate_synthetic_waveform(req)
        features = cls.extract_acoustic_features(waveform, req.sampling_rate_hz)

        # Downsample waveform for UI transmission (100 representative points)
        downsample_step = max(1, len(waveform) // 100)
        time_series_sample = [round(float(v), 4) for v in waveform[::downsample_step][:100]]

        # FFT sample for UI spectrum plotting (first 60 frequency bins up to 4000 Hz)
        n = len(waveform)
        fft_vals = np.abs(rfft(waveform * np.hanning(n)))
        freqs = rfftfreq(n, dt)
        fft_step = max(1, len(freqs) // 60)
        fft_spectrum = [
            {"frequency_hz": round(float(f), 1), "magnitude": round(float(m), 3)}
            for f, m in zip(freqs[::fft_step][:60], fft_vals[::fft_step][:60])
        ]

        return SyntheticWaveformResponse(
            scenario=req.scenario,
            sampling_rate_hz=req.sampling_rate_hz,
            duration_seconds=req.duration_seconds,
            sample_count=len(waveform),
            features=features,
            time_series_sample=time_series_sample,
            fft_spectrum_sample=fft_spectrum,
            is_simulated=True,
            disclaimer="Synthetic waveform generated by virtual acoustic physics model. Not actual field telemetry.",
        )
