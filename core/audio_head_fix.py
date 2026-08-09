"""Detect and mute the decoder burst at the very start of AI-generated clips.

Video models with a joint audio branch (MiniMax H3, LTX-2 and friends) often emit
garbage in the first audio latents: a short loud click right after t=0, heard as
"t..", "ts..", "f..". It is followed by the silence the prompt actually asked for,
so the fix is to fade the track in after the burst — never to cut it, which would
desync lip movement.

Detection is deliberately conservative: the burst is only treated as an artifact
when what follows it is essentially silent. A clip that genuinely starts with
sound (singing, music from frame zero) keeps a loud tail and is left untouched.
"""

from __future__ import annotations

import array
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core.app_log import get_logger

ANALYSIS_SAMPLE_RATE = 16000
ANALYSIS_DURATION_SEC = 1.2
FRAME_SEC = 0.01

# The burst peaks almost immediately; a later transient is real content.
ONSET_END_SEC = 0.15
# It never runs longer than this.
BURST_END_LIMIT_SEC = 0.60
# A pause of at least this length has to follow it — that pause is what tells an
# artifact apart from a clip that simply opens loud.
GAP_MIN_SEC = 0.15

# The burst has to be audible in absolute terms...
MIN_HEAD_PEAK_DBFS = -35.0
# ...the pause after it has to be effectively silent...
MAX_GAP_DBFS = -45.0
# ...and the two have to be far apart.
MIN_DROP_DB = 25.0

# How far below the peak the signal has to fall to count as the pause.
DECAY_MARGIN_DB = 35.0
DECAY_FLOOR_DBFS = -60.0

RELEASE_MARGIN_SEC = 0.04
MIN_MUTE_SEC = 0.10
MAX_MUTE_SEC = 0.60
FADE_SEC = 0.06

SILENCE_DBFS = -120.0


@dataclass(frozen=True)
class AudioHeadArtifact:
    """A start-of-clip burst worth muting."""

    mute_until: float
    fade: float
    head_peak_db: float
    gap_db: float

    @property
    def mute_ms(self) -> int:
        return int(round(self.mute_until * 1000))


def _decode_head_pcm(path: Path) -> array.array | None:
    """Decode the first second of audio to mono 16-bit PCM, or None if absent."""
    from core.ffmpeg_wrapper import subprocess_creation_flags

    cmd = [
        "ffmpeg",
        "-v", "error",
        "-i", str(path),
        "-vn",
        "-t", str(ANALYSIS_DURATION_SEC),
        "-ac", "1",
        "-ar", str(ANALYSIS_SAMPLE_RATE),
        "-f", "s16le",
        "-",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            check=True,
            creationflags=subprocess_creation_flags(),
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        get_logger().warning("Audio head probe failed for %s: %s", path.name, exc)
        return None

    raw = result.stdout
    if len(raw) < 2:
        return None
    samples = array.array("h")
    samples.frombytes(raw[: len(raw) - (len(raw) % 2)])
    return samples


def _frame_levels(samples: array.array) -> list[float]:
    """RMS level of each 10 ms frame, in dBFS."""
    step = int(ANALYSIS_SAMPLE_RATE * FRAME_SEC)
    levels: list[float] = []
    for start in range(0, len(samples) - step + 1, step):
        total = 0
        for value in samples[start : start + step]:
            total += value * value
        rms = math.sqrt(total / step)
        if rms < 1e-9:
            levels.append(SILENCE_DBFS)
        else:
            levels.append(20 * math.log10(rms / 32768.0))
    return levels


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(fraction * len(ordered)))
    return ordered[index]


def analyze_audio_head(levels: list[float]) -> AudioHeadArtifact | None:
    """Decide whether the frame levels describe a start-of-clip artifact.

    The signature is: something loud right at t=0, which then drops into a pause.
    Real openings — music, a held note, speech from frame one — never fall silent
    that soon, so they fall through and are left alone.
    """
    onset_end = int(ONSET_END_SEC / FRAME_SEC)
    burst_limit = int(BURST_END_LIMIT_SEC / FRAME_SEC)
    gap_frames = int(GAP_MIN_SEC / FRAME_SEC)

    if len(levels) < burst_limit + gap_frames:
        return None

    head_peak = max(levels[:onset_end])
    if head_peak < MIN_HEAD_PEAK_DBFS:
        return None

    quiet_threshold = max(head_peak - DECAY_MARGIN_DB, DECAY_FLOOR_DBFS)
    peak_index = levels.index(head_peak, 0, onset_end)

    for index in range(peak_index + 1, burst_limit):
        gap = levels[index : index + gap_frames]
        if max(gap) > quiet_threshold:
            continue
        # The burst may still be decaying through the first quiet-ish window, so
        # keep scanning instead of giving up on the clip.
        gap_level = _percentile(gap, 0.95)
        if gap_level > MAX_GAP_DBFS:
            continue
        if head_peak - gap_level < MIN_DROP_DB:
            continue
        mute_until = index * FRAME_SEC + RELEASE_MARGIN_SEC
        mute_until = max(MIN_MUTE_SEC, min(MAX_MUTE_SEC, mute_until))
        return AudioHeadArtifact(
            mute_until=round(mute_until, 3),
            fade=FADE_SEC,
            head_peak_db=round(head_peak, 1),
            gap_db=round(gap_level, 1),
        )

    return None


def detect_audio_head_artifact(path: Path) -> AudioHeadArtifact | None:
    """Probe a clip and return the burst to mute, or None to leave it alone."""
    samples = _decode_head_pcm(path)
    if samples is None or not len(samples):
        return None
    artifact = analyze_audio_head(_frame_levels(samples))
    if artifact is None:
        get_logger().info("Audio head clean: %s", path.name)
    else:
        get_logger().info(
            "Audio head artifact in %s: peak %.1f dBFS, gap %.1f dBFS, mute %d ms",
            path.name,
            artifact.head_peak_db,
            artifact.gap_db,
            artifact.mute_ms,
        )
    return artifact


def audio_head_filter(artifact: AudioHeadArtifact) -> str:
    """ffmpeg filter that silences the burst and fades in, timeline untouched."""
    return f"afade=t=in:st={artifact.mute_until:.3f}:d={artifact.fade:.3f}"


def ffmpeg_audio_head_args(artifact: AudioHeadArtifact | None) -> list[str]:
    if artifact is None:
        return []
    return ["-af", audio_head_filter(artifact)]
