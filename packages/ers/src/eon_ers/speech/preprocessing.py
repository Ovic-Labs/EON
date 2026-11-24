"""Speech audio preprocessing and framing for ERS."""

from __future__ import annotations

import numpy as np


class SpeechPreprocessor:
    """Preprocesses raw audio waveforms into sliding analysis frames."""

    def __init__(self, frame_duration_ms: float = 25.0, hop_duration_ms: float = 10.0) -> None:
        self.frame_duration_ms = frame_duration_ms
        self.hop_duration_ms = hop_duration_ms

    def frame_signal(self, signal: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
        """Slice 1D waveform into overlapping analysis frames and apply Hamming window.

        Returns:
            tuple[np.ndarray, np.ndarray]:
                - frames: 2D array of shape (num_frames, frame_len)
                - windowed_frames: 2D array of windowed frames
        """
        frame_len = int(round((self.frame_duration_ms / 1000.0) * sample_rate))
        hop_len = int(round((self.hop_duration_ms / 1000.0) * sample_rate))

        signal_len = len(signal)
        if signal_len < frame_len:
            # Zero-pad short signal to minimum frame length
            padded = np.zeros(frame_len, dtype=np.float32)
            padded[:signal_len] = signal
            signal = padded
            signal_len = frame_len

        num_frames = max(1, (signal_len - frame_len) // hop_len + 1)
        frames = np.zeros((num_frames, frame_len), dtype=np.float32)

        for i in range(num_frames):
            start = i * hop_len
            end = start + frame_len
            frames[i] = signal[start:end]

        window = np.hamming(frame_len).astype(np.float32)
        windowed_frames = frames * window

        return frames, windowed_frames
