"""Rule-based mapping from audio features to visual prompt language (week3 pipeline)."""

from __future__ import annotations

from typing import Any


def _bucket_tempo(bpm: float) -> str:
    if bpm < 95:
        return "slow"
    if bpm < 128:
        return "medium"
    return "fast"


def _bucket_loudness(rms_mean: float) -> str:
    # After level normalization, RMS typically sits in a modest band; widen thresholds.
    if rms_mean < 0.04:
        return "quiet"
    if rms_mean < 0.09:
        return "medium"
    return "loud"


def _bucket_brightness(centroid_hz: float) -> str:
    if centroid_hz < 1800:
        return "low"
    if centroid_hz < 3500:
        return "mid"
    return "high"


def _bucket_rhythm(onset_mean: float, onset_std: float) -> str:
    pulse = onset_mean / (onset_std + 1e-6)
    if pulse < 1.1:
        return "sparse"
    if pulse < 2.0:
        return "steady"
    return "dense"


def _bucket_texture(zcr: float) -> str:
    if zcr < 0.05:
        return "smooth"
    if zcr < 0.12:
        return "grainy"
    return "rough"


TEMPO_PHRASES = {
    "slow": "slow drifting masses, long gentle curves, meditative negative space",
    "medium": "balanced motion, flowing organic shapes, measured rhythm in the composition",
    "fast": "rapid energetic strokes, staccato marks, kinetic bursts and sharp transitions",
}

LOUDNESS_PHRASES = {
    "quiet": "soft whispered tones, delicate washes, low-contrast misty layers",
    "medium": "moderate dynamic range, clear but not overwhelming presence",
    "loud": "bold high-impact blocks of color, dramatic contrast, commanding presence",
}

BRIGHTNESS_PHRASES = {
    "low": "deep moody shadows, warm low-end hues, submerged underwater darkness",
    "mid": "balanced luminosity, nuanced mid-tones, earthy and natural palette",
    "high": "bright crystalline highlights, sharp luminous edges, airy brilliance",
}

RHYTHM_PHRASES = {
    "sparse": "sparse punctuation, lots of breathing room, minimal repeating motifs",
    "steady": "regular repeating patterns, predictable visual cadence like a pulse",
    "dense": "layered overlapping texture, busy polyrhythmic visual complexity",
}

TEXTURE_PHRASES = {
    "smooth": "silky gradients, soft blends, airbrushed continuous surfaces",
    "grainy": "fine particulate noise, film grain, subtle tactile grit",
    "rough": "coarse choppy marks, heavy impasto feel, rugged broken edges",
}


def features_to_prompt(features: dict[str, Any]) -> dict[str, Any]:
    """
    Map extracted numeric features to discrete labels and natural-language fragments.
    Returns data suitable for JSON and for a future LLM/image stage.
    """
    tempo = _bucket_tempo(float(features["tempo_bpm"]))
    loud = _bucket_loudness(float(features["rms_mean"]))
    bright = _bucket_brightness(float(features["spectral_centroid_hz"]))
    rhythm = _bucket_rhythm(
        float(features["onset_strength_mean"]),
        float(features["onset_strength_std"]),
    )
    texture = _bucket_texture(float(features["zero_crossing_rate_mean"]))

    labels = {
        "tempo": tempo,
        "loudness": loud,
        "brightness": bright,
        "rhythm": rhythm,
        "texture": texture,
    }

    fragments = [
        TEMPO_PHRASES[tempo],
        LOUDNESS_PHRASES[loud],
        BRIGHTNESS_PHRASES[bright],
        RHYTHM_PHRASES[rhythm],
        TEXTURE_PHRASES[texture],
    ]

    header = (
        "Abstract synesthetic album art, non-representational, emotional translation of sound; "
    )
    body = "; ".join(fragments)
    prompt_preview = header + body + "."

    return {
        "labels": labels,
        "prompt_fragments": fragments,
        "prompt_preview": prompt_preview,
    }
