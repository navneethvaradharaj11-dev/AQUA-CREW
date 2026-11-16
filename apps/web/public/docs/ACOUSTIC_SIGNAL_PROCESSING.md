# AQUA CREW — Acoustic Signal Processing Specification
**Task 07 — AI-Powered Leak Detection & Acoustic Intelligence**

## 1. Executive Summary & Physics Foundations

In pressurized metropolitan water distribution networks, pipe wall ruptures, joint failures, and pinhole orifices generate turbulent jetting fluid flows that create acoustic emission waves. These acoustic emissions propagate through the water column and pipe walls as longitudinal and flexural vibrations.

AQUA CREW's acoustic analysis pipeline utilizes synthetic acoustic waveforms generated from deterministic mathematical acoustic models simulating real-world fluid dynamics.

> [!WARNING]
> **SIMULATION PROVENANCE**: All acoustic waveforms, spectra, and audio telemetry in AQUA CREW are synthetically generated for software architecture, signal validation, and human-in-the-loop operator training. They do not constitute raw physical field sensor recordings.

---

## 2. Synthetic Acoustic Waveform Generation

The synthetic acoustic signal generation engine is implemented in `apps/api/app/services/signal_processing_service.py`.

### 2.1 Acoustic Scenarios Supported

| Scenario Identifier | Center Frequency (\(f_c\)) | Typical Bandwidth (\(B\)) | Target RMS (\(SPL\)) | Physical Phenomenon |
|---|---|---|---|---|
| `NORMAL_FLOW` | 180 Hz | 60 Hz | 32–42 dB | Laminar/turbulent baseline flow, minimal pipe wall agitation |
| `MINOR_LEAK` | 750 Hz | 200 Hz | 55–65 dB | Pinhole fissure, micro-jetting |
| `MODERATE_LEAK` | 1,200 Hz | 400 Hz | 68–78 dB | Joint slippage, circumferential crack, pronounced acoustic hiss |
| `MAJOR_LEAK` | 1,800 Hz | 650 Hz | 82–95 dB | Full transverse fracture, high-velocity turbulent jetting |
| `ENVIRONMENTAL_NOISE` | 350 Hz | 250 Hz | 50–60 dB | Surface traffic, subway rumble, construction vibrations |
| `PRESSURE_FLUCTUATION` | 80 Hz | 40 Hz | 45–55 dB | Water hammer transients, pump throttling |
| `MECHANICAL_VIBRATION` | 120 Hz | 50 Hz | 48–58 dB | Pump harmonics, HVAC mechanical coupling |

### 2.2 Mathematical Signal Synthesis Model

The acoustic time series \(s(t)\) is synthesized at sampling rate \(f_s = 8,000 \text{ Hz}\) over duration \(T = 2.0 \text{ s}\) via additive harmonic sinusoids plus shaped Gaussian noise:

\[
s(t) = A_1 \sin(2\pi f_c t) + A_2 \sin(2\pi (1.4 f_c) t) + A_3 \sin(2\pi (2.1 f_c) t) + \eta(t)
\]

where:
- \(f_c\) is the fundamental acoustic center frequency.
- \(A_1, A_2, A_3\) are harmonic amplitude weights.
- \(\eta(t) \sim \mathcal{N}(0, \sigma^2)\) is band-limited Gaussian noise scaled to achieve the target Signal-to-Noise Ratio (\(\text{SNR}_{\text{dB}}\)).

---

## 3. Extracted Acoustic Signal Features

The signal-processing module applies Fast Fourier Transform (FFT) and windowing to extract ten core acoustic features:

### 3.1 Root Mean Square (RMS) Amplitude
Quantifies overall acoustic sound pressure level:
\[
\text{RMS} = \sqrt{\frac{1}{N} \sum_{n=0}^{N-1} s[n]^2}
\]
Converted to decibels (SPL ref \(20\,\mu\text{Pa}\)):
\[
SPL_{\text{dB}} = 20 \log_{10}\left(\frac{\text{RMS}}{20 \times 10^{-6}}\right)
\]

### 3.2 Peak Amplitude & Crest Factor
Measures maximum instantaneous deviation and impulsiveness:
\[
\text{Peak} = \max |s[n]|, \quad \text{Crest Factor} = \frac{\text{Peak}}{\text{RMS}}
\]

### 3.3 Dominant Frequency (\(f_{\text{dom}}\))
Frequency index corresponding to maximum FFT magnitude:
\[
f_{\text{dom}} = \arg\max_{f_k} |S[k]|
\]

### 3.4 Spectral Centroid
Center of mass of the frequency spectrum:
\[
\text{Centroid} = \frac{\sum_{k=0}^{K-1} f_k |S[k]|}{\sum_{k=0}^{K-1} |S[k]|}
\]
Higher spectral centroids signify high-frequency jetting hiss characteristic of pressurized leaks.

### 3.5 Spectral Bandwidth
Spread of spectral energy around the centroid:
\[
\text{Bandwidth} = \sqrt{\frac{\sum_{k=0}^{K-1} (f_k - \text{Centroid})^2 |S[k]|}{\sum_{k=0}^{K-1} |S[k]|}}
\]

### 3.6 Spectral Energy
Total spectral power in the analysis frame:
\[
E_{\text{spectral}} = \sum_{k=0}^{K-1} |S[k]|^2
\]

### 3.7 Signal-to-Noise Ratio (SNR)
Ratio between peak spectral peak magnitude and average noise floor:
\[
\text{SNR}_{\text{dB}} = 10 \log_{10}\left(\frac{P_{\text{signal}}}{P_{\text{noise}}}\right)
\]

---

## 4. UI Spectral Decomposition Display

For real-time operator inspection in `/app/intelligence`:
- **Time-Domain Visualizer**: 80-point downsampled normalized amplitude polyline rendering acoustic waves across a 2.0s duration window.
- **Frequency-Domain Visualizer**: 12-bin discrete FFT energy bars spanning \(0 \text{ Hz}\) to \(4,000 \text{ Hz}\), highlighting the dominant resonance peak.

