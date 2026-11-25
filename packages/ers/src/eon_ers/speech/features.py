"""Acoustic prosody and spectral feature extraction for ERS."""

from __future__ import annotations

import numpy as np
from scipy.fft import rfft
from scipy.signal import find_peaks

from eon_ers.speech.preprocessing import SpeechPreprocessor


class AcousticFeatureExtractor:
    """Extracts non-linguistic acoustic prosody and spectral descriptors.

    Computes:
    - F0 Fundamental frequency (mean, std, range, slope)
    - RMS Energy (mean, variance, dynamic range)
    - Zero-Crossing Rate (ZCR)
    - Spectral Centroid & Flux
    - Mel-Frequency Filterbank statistics (MFCCs approximation)
    - Voice Activity Ratio / Speaking Rate
    """

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self.preprocessor = SpeechPreprocessor()

    def estimate_f0_autocorrelation(
        self, frame: np.ndarray, sample_rate: int, min_f0: float = 65.0, max_f0: float = 400.0
    ) -> float:
        """Estimate fundamental frequency (F0) of a windowed voiced frame via autocorrelation."""
        min_lag = int(sample_rate / max_f0)
        max_lag = int(sample_rate / min_f0)

        if len(frame) <= max_lag:
            return 0.0

        # Normalized autocorrelation
        corr = np.correlate(frame, frame, mode="full")
        corr = corr[len(frame) - 1 :]  # Non-negative lags

        if corr[0] <= 1e-9:
            return 0.0

        norm_corr = corr / corr[0]
        search_region = norm_corr[min_lag : min(len(norm_corr), max_lag)]
        if len(search_region) == 0:
            return 0.0

        peaks, _ = find_peaks(search_region, height=0.3)
        if len(peaks) == 0:
            return 0.0

        best_peak = peaks[np.argmax(search_region[peaks])] + min_lag
        f0 = float(sample_rate / best_peak)
        return f0

    def compute_mfccs(
        self, windowed_frames: np.ndarray, sample_rate: int, num_ceps: int = 13
    ) -> np.ndarray:
        """Extract Mel-Frequency Cepstral Coefficients using FFT and triangle filterbank."""
        num_frames, frame_len = windowed_frames.shape
        fft_len = 512
        if frame_len > fft_len:
            fft_len = 1024

        # Compute power spectrum
        mag_spec = np.abs(rfft(windowed_frames, n=fft_len, axis=1))
        power_spec = (mag_spec**2) / fft_len

        # Construct mel filterbank
        num_filters = 26
        low_freq = 133.33
        high_freq = sample_rate / 2.0

        low_mel = 2595.0 * np.log10(1.0 + low_freq / 700.0)
        high_mel = 2595.0 * np.log10(1.0 + high_freq / 700.0)
        mel_points = np.linspace(low_mel, high_mel, num_filters + 2)
        hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
        bin_points = np.floor((fft_len + 1) * hz_points / sample_rate).astype(int)

        n_bins = power_spec.shape[1]
        fbanks = np.zeros((num_filters, n_bins), dtype=np.float32)
        for m in range(1, num_filters + 1):
            f_m_minus = min(bin_points[m - 1], n_bins - 1)
            f_m = min(bin_points[m], n_bins - 1)
            f_m_plus = min(bin_points[m + 1], n_bins - 1)

            for k in range(f_m_minus, f_m):
                if f_m > f_m_minus:
                    fbanks[m - 1, k] = (k - bin_points[m - 1]) / (bin_points[m] - bin_points[m - 1])
            for k in range(f_m, f_m_plus):
                if f_m_plus > f_m:
                    fbanks[m - 1, k] = (bin_points[m + 1] - k) / (bin_points[m + 1] - bin_points[m])

        filter_energies = np.dot(power_spec, fbanks.T)
        filter_energies = np.where(filter_energies <= 1e-9, 1e-9, filter_energies)
        log_energies = np.log(filter_energies)

        # Type-II DCT
        from scipy.fft import dct

        mfccs = dct(log_energies, type=2, axis=1, norm="ortho")[:, :num_ceps]
        return mfccs

    def extract_features(self, signal: np.ndarray, sample_rate: int) -> dict[str, float]:
        """Extract complete numerical prosody and spectral descriptor dictionary safely."""
        if signal.size == 0 or sample_rate <= 0:
            return {
                "f0_mean_hz": 0.0,
                "f0_std_hz": 0.0,
                "f0_range_hz": 0.0,
                "energy_rms_mean": 0.0,
                "energy_std": 0.0,
                "energy_max": 0.0,
                "zero_crossing_rate": 0.0,
                "spectral_centroid_hz": 0.0,
                "voice_activity_ratio": 0.0,
                "mfcc_0": 0.0,
                "mfcc_1": 0.0,
                "mfcc_2": 0.0,
            }

        clean_sig = np.nan_to_num(signal.astype(np.float32), nan=0.0, posinf=1.0, neginf=-1.0)
        frames, windowed_frames = self.preprocessor.frame_signal(clean_sig, sample_rate)
        num_frames, frame_len = frames.shape

        # 1. Energy contour & RMS
        frame_energies = np.sqrt(np.mean(frames**2, axis=1) + 1e-9)
        mean_energy = float(np.mean(frame_energies))
        energy_std = float(np.std(frame_energies))
        energy_max = float(np.max(frame_energies))

        # 2. Zero Crossing Rate (ZCR)
        zcr_per_frame = np.mean(np.abs(np.diff(np.sign(frames), axis=1)) > 0, axis=1)
        mean_zcr = float(np.mean(zcr_per_frame))

        # 3. Voice Activity Detection (VAD) ratio
        voice_thresh = max(1e-4, mean_energy * 0.4)
        voiced_mask = frame_energies > voice_thresh
        voice_ratio = float(np.mean(voiced_mask))

        # 4. F0 Pitch contour
        f0_values: list[float] = []
        for i in range(num_frames):
            if voiced_mask[i]:
                f0 = self.estimate_f0_autocorrelation(windowed_frames[i], sample_rate)
                if f0 > 0:
                    f0_values.append(f0)

        if len(f0_values) >= 3:
            f0_mean = float(np.mean(f0_values))
            f0_std = float(np.std(f0_values))
            f0_range = float(np.max(f0_values) - np.min(f0_values))
        else:
            f0_mean = 0.0
            f0_std = 0.0
            f0_range = 0.0

        # 5. Spectral Centroid
        mag_spec = np.abs(rfft(windowed_frames, axis=1))
        freqs = np.linspace(0, sample_rate / 2.0, mag_spec.shape[1])
        mag_sum = np.sum(mag_spec, axis=1) + 1e-9
        centroids = np.sum(mag_spec * freqs, axis=1) / mag_sum
        mean_centroid = float(np.mean(centroids))

        # 6. MFCC mean vectors
        try:
            mfccs = self.compute_mfccs(windowed_frames, sample_rate, num_ceps=13)
            mfcc_means = np.mean(mfccs, axis=0)
            mfcc_0 = float(mfcc_means[0])
            mfcc_1 = float(mfcc_means[1])
            mfcc_2 = float(mfcc_means[2])
        except Exception:
            mfcc_0, mfcc_1, mfcc_2 = 0.0, 0.0, 0.0

        return {
            "f0_mean_hz": round(f0_mean, 2),
            "f0_std_hz": round(f0_std, 2),
            "f0_range_hz": round(f0_range, 2),
            "energy_rms_mean": round(mean_energy, 4),
            "energy_std": round(energy_std, 4),
            "energy_max": round(energy_max, 4),
            "zero_crossing_rate": round(mean_zcr, 4),
            "spectral_centroid_hz": round(mean_centroid, 2),
            "voice_activity_ratio": round(voice_ratio, 4),
            "mfcc_0": round(mfcc_0, 4),
            "mfcc_1": round(mfcc_1, 4),
            "mfcc_2": round(mfcc_2, 4),
        }
