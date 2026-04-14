"""Load audio, normalize levels, extract features with librosa."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import librosa
import numpy as np


def _noise_gate(y: np.ndarray, threshold_ratio: float = 0.02) -> np.ndarray:
    """Attenuate samples well below the peak to reduce background hiss (light gate)."""
    peak = float(np.max(np.abs(y))) + 1e-9
    floor = peak * threshold_ratio
    out = y.astype(np.float64, copy=True)
    quiet = np.abs(out) < floor
    out[quiet] *= 0.05
    return out


def _level_normalize(y: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """Normalize perceived loudness toward a target RMS in dB (rough gain match)."""
    rms = float(np.sqrt(np.mean(np.square(y))) + 1e-12)
    current_db = 20.0 * np.log10(rms)
    gain_db = target_db - current_db
    gain = 10.0 ** (gain_db / 20.0)
    z = y * gain
    return np.clip(z, -1.0, 1.0)


def analyze_file(path: str | Path, sr: int = 22050) -> dict[str, Any]:
    """
    Load an audio file from disk, normalize, and compute scalar features for mapping.
    """
    path = Path(path)
    y, sr = librosa.load(str(path), sr=sr, mono=True)
    return analyze_array(y, sr)


def analyze_array(y: np.ndarray, sr: int) -> dict[str, Any]:
    """Run the same pipeline on an in-memory mono waveform."""
    y = np.asarray(y, dtype=np.float64)
    if y.size == 0:
        raise ValueError("Empty audio")

    min_len = int(sr * 0.5)
    if y.size < min_len:
        y = np.pad(y, (0, min_len - y.size), mode="constant")

    y = _noise_gate(y)
    y = _level_normalize(y)

    duration_sec = float(y.size / sr)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr, onset_envelope=onset_env)
    tempo_bpm = float(np.asarray(tempo_arr, dtype=np.float64).reshape(-1)[0])

    rms_frames = librosa.feature.rms(y=y)[0]
    rms_mean = float(np.mean(rms_frames))

    centroid_frames = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    centroid_hz = float(np.mean(centroid_frames))

    zcr_frames = librosa.feature.zero_crossing_rate(y)[0]
    zcr_mean = float(np.mean(zcr_frames))

    onset_mean = float(np.mean(onset_env))
    onset_std = float(np.std(onset_env))

    return {
        "duration_sec": round(duration_sec, 3),
        "tempo_bpm": round(tempo_bpm, 2),
        "rms_mean": round(rms_mean, 6),
        "spectral_centroid_hz": round(centroid_hz, 2),
        "zero_crossing_rate_mean": round(zcr_mean, 6),
        "onset_strength_mean": round(onset_mean, 4),
        "onset_strength_std": round(onset_std, 4),
        "sample_rate": sr,
    }


def analyze_upload(temp_path: str | Path) -> dict[str, Any]:
    """Convenience wrapper for a tempfile path from Flask uploads."""
    return analyze_file(temp_path)


def write_temp_upload(file_storage, suffix: str = ".wav") -> tuple[str, bool]:
    """
    Stream upload to a temp file. Returns (path, should_unlink).
    Caller should delete the file when done.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    file_storage.save(path)
    return path, True
