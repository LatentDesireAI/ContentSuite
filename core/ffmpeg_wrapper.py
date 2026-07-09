"""ffmpeg/ffprobe helpers for video processing."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from core.app_log import get_logger
from core.media_scan import collect_media_files
from core.metadata import (
    build_ffmpeg_metadata_flags,
    embed_author_in_folder,
    should_strip_media_metadata,
)
from core.video_compression import (
    DEFAULT_COMPRESSION_ID,
    ffmpeg_audio_encode_args,
    ffmpeg_container_mux_args,
    ffmpeg_mobile_video_prep_args,
    ffmpeg_video_encode_args,
    is_mp4_video_copy_safe,
)
from core.watermark import (
    WatermarkSettings,
    ffmpeg_overlay_filter,
    ffmpeg_overlay_on_label,
    watermark_height_px,
)

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v", ".wmv"}


def default_video_worker_count() -> int:
    """Parallel ffmpeg jobs — each encode already uses multiple CPU threads."""
    cpus = os.cpu_count() or 4
    return max(2, min(8, cpus // 4))


@dataclass
class VideoProbe:
    path: Path
    duration: float
    width: int
    height: int
    video_codec: str
    pix_fmt: str
    profile: str
    audio_codec: str | None
    container: str
    bitrate: int | None
    has_audio: bool

    @property
    def summary(self) -> str:
        audio = self.audio_codec or "none"
        dur = f"{self.duration:.1f}s" if self.duration > 0 else "?"
        return (
            f"{self.video_codec}/{self.container}, {self.width}x{self.height}, "
            f"{dur}, audio={audio}"
        )


@dataclass
class VideoJobResult:
    source: Path
    output: Path | None
    success: bool
    message: str = ""
    probe: VideoProbe | None = None


@dataclass
class VideoBatchSummary:
    total: int = 0
    processed: int = 0
    failed: int = 0
    results: list[VideoJobResult] = field(default_factory=list)


ProgressCallback = Callable[[int, int, VideoJobResult], None]


class FfmpegError(Exception):
    pass


def check_ffmpeg() -> tuple[bool, str]:
    for tool in ("ffmpeg", "ffprobe"):
        try:
            subprocess.run(
                [tool, "-version"],
                capture_output=True,
                check=True,
                creationflags=_creation_flags(),
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            return False, f"{tool} not available: {exc}"
    return True, ""


def _creation_flags() -> int:
    import sys

    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def collect_videos(folder: Path) -> list[Path]:
    return collect_media_files(folder, VIDEO_EXTENSIONS)


def probe_video(path: Path) -> VideoProbe:
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            creationflags=_creation_flags(),
        )
        data = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as exc:
        raise FfmpegError(f"ffprobe: {path.name}: {exc}") from exc

    fmt = data.get("format", {})
    streams = data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    duration = float(fmt.get("duration", 0) or 0)
    bitrate = None
    if fmt.get("bit_rate"):
        try:
            bitrate = int(fmt["bit_rate"])
        except (TypeError, ValueError):
            pass

    return VideoProbe(
        path=path,
        duration=duration,
        width=int(video_stream.get("width", 0) or 0),
        height=int(video_stream.get("height", 0) or 0),
        video_codec=video_stream.get("codec_name", "unknown"),
        pix_fmt=video_stream.get("pix_fmt", "") or "",
        profile=video_stream.get("profile", "") or "",
        audio_codec=audio_stream.get("codec_name") if audio_stream else None,
        container=fmt.get("format_name", path.suffix.lstrip(".")).split(",")[0],
        bitrate=bitrate,
        has_audio=audio_stream is not None,
    )


def thumbnail_cache_dir() -> Path:
    from core.config_store import config_path

    cache = config_path().parent / "thumbs"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def thumbnail_cache_path(video_path: Path) -> Path:
    stat = video_path.stat()
    digest = hashlib.sha1(
        f"{video_path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}".encode()
    ).hexdigest()[:16]
    return thumbnail_cache_dir() / f"{digest}.jpg"


def format_duration(seconds: float) -> str:
    if seconds <= 0:
        return "?:??"
    total = int(round(seconds))
    mins, secs = divmod(total, 60)
    if mins >= 60:
        hours, mins = divmod(mins, 60)
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def extract_thumbnail(
    video_path: Path,
    output_path: Path,
    *,
    time_sec: float = 1.0,
    width: int = 360,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg([
        "-ss", str(max(0.0, time_sec)),
        "-i", str(video_path),
        "-vframes", "1",
        "-vf", f"scale={width}:-1",
        "-q:v", "3",
        str(output_path),
    ])


def run_ffmpeg(args: list[str], *, quiet: bool = True) -> None:
    cmd = ["ffmpeg", "-y", *args]
    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
            creationflags=_creation_flags(),
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        tail = stderr[-800:] if len(stderr) > 800 else stderr
        raise FfmpegError(tail or str(exc)) from exc
    except FileNotFoundError as exc:
        raise FfmpegError("ffmpeg not found in PATH") from exc


def _encode_temp_path(output_path: Path) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "ContentSuite" / "encode"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir / f"{uuid.uuid4().hex}{output_path.suffix.lower()}"


def validate_video_output(path: Path) -> VideoProbe:
    """Raise if the file is truncated or missing a playable video stream."""
    if not path.is_file():
        raise FfmpegError(f"Output file missing: {path.name}")
    size = path.stat().st_size
    if size < 4096:
        raise FfmpegError(f"Output file too small ({size} bytes): {path.name}")
    try:
        probe = probe_video(path)
    except FfmpegError as exc:
        raise FfmpegError(
            f"Output unreadable (truncated or corrupt): {path.name}: {exc}"
        ) from exc
    if probe.width <= 0 or probe.height <= 0:
        raise FfmpegError(f"Output has no video stream: {path.name}")
    if probe.duration <= 0:
        raise FfmpegError(f"Output has invalid duration: {path.name}")
    return probe


def run_ffmpeg_to_file(args: list[str], output_path: Path, *, retries: int = 1) -> None:
    """Encode to a local temp file, validate, then atomically replace output."""
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        temp_out = _encode_temp_path(output_path)
        try:
            run_ffmpeg([*args, str(temp_out)])
            probe = validate_video_output(temp_out)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists():
                output_path.unlink()
            shutil.move(str(temp_out), str(output_path))
            if output_path.suffix.lower() in (".mp4", ".mov", ".m4v"):
                get_logger().info(
                    "Video output %s: %s %s %s (%d bytes)",
                    output_path.name,
                    probe.video_codec,
                    probe.pix_fmt or "?",
                    probe.profile or "",
                    output_path.stat().st_size,
                )
            return
        except (FfmpegError, OSError) as exc:
            last_error = exc
            if temp_out.exists():
                temp_out.unlink()
            if attempt < retries:
                get_logger().warning(
                    "Retrying %s after encode error (attempt %d): %s",
                    output_path.name,
                    attempt + 2,
                    exc,
                )
    if last_error is not None:
        raise last_error


JOB_OUTPUT_SUBDIR = {
    "watermark": "watermark",
    "gif": "gif",
    "convert": "videos",
    "metadata": "videos",
}


def job_output_dir(base_output: Path, job: str) -> Path:
    sub = JOB_OUTPUT_SUBDIR.get(job, "")
    return base_output / sub if sub else base_output


def calc_pixiv_ugoira_fps(chunk_sec: int, max_frames: int = 150) -> int:
    """FPS that keeps frame count within Pixiv ugoira limit for a chunk."""
    return max(1, max_frames // max(1, chunk_sec))


def resolve_ugoira_fps(
    chunk_sec: int,
    *,
    max_frames: int = 150,
    auto_fps: bool = True,
    manual_fps: int = 20,
) -> int:
    auto = calc_pixiv_ugoira_fps(chunk_sec, max_frames)
    if auto_fps:
        return auto
    return max(1, min(manual_fps, auto))


def _output_path(
    input_path: Path,
    output_dir: Path,
    suffix: str,
    ext: str,
    *,
    output_stem: str | None = None,
) -> Path:
    stem = output_stem if output_stem else input_path.stem
    if suffix and not output_stem:
        stem = f"{stem}{suffix}"
    return output_dir / f"{stem}{ext}"


def _append_video_metadata(
    args: list[str],
    *,
    remove_metadata: bool,
    author_meta: dict | None,
    title: str = "",
) -> None:
    if should_strip_media_metadata(remove_metadata, author_meta):
        args.extend(["-map_metadata", "-1", "-fflags", "+bitexact"])
    args.extend(build_ffmpeg_metadata_flags(author_meta, title=title))


def apply_watermark(
    input_path: Path,
    output_path: Path,
    watermark_path: Path,
    settings: WatermarkSettings,
    *,
    copy_audio: bool = True,
    remove_metadata: bool = True,
    compression_level: str = DEFAULT_COMPRESSION_ID,
    author_meta: dict | None = None,
    title: str = "",
) -> None:
    probe = probe_video(input_path)
    output_format = output_path.suffix.lstrip(".").lower() or "webm"
    filt = ffmpeg_overlay_filter(settings, frame_height=probe.height)
    args = [
        "-i", str(input_path),
        "-i", str(watermark_path),
        "-filter_complex", filt,
        *ffmpeg_video_encode_args(output_format, compression_level),
    ]
    if copy_audio and probe.has_audio:
        args.extend(ffmpeg_audio_encode_args(output_format))
    else:
        args.append("-an")
    _append_video_metadata(
        args,
        remove_metadata=remove_metadata,
        author_meta=author_meta,
        title=title,
    )
    args.extend(ffmpeg_container_mux_args(output_format))
    run_ffmpeg_to_file(args, output_path)


def export_gif(
    input_path: Path,
    output_path: Path,
    *,
    fps: int = 24,
    width: int = 720,
    remove_metadata: bool = True,
    author_meta: dict | None = None,
    title: str = "",
) -> None:
    palette_path = output_path.with_suffix(".palette.png")
    gif_tail: list[str] = []
    _append_video_metadata(
        gif_tail,
        remove_metadata=remove_metadata,
        author_meta=author_meta,
        title=title,
    )
    try:
        run_ffmpeg([
            "-i", str(input_path),
            "-vf", f"fps={fps},scale={width}:-1:flags=lanczos,palettegen",
            str(palette_path),
        ])
        run_ffmpeg([
            "-i", str(input_path),
            "-i", str(palette_path),
            "-lavfi",
            f"fps={fps},scale={width}:-1:flags=lanczos [x]; [x][1:v] paletteuse",
            *gif_tail,
            str(output_path),
        ])
    finally:
        if palette_path.exists():
            palette_path.unlink()


def patch_video_metadata(
    input_path: Path,
    output_path: Path,
    *,
    author_meta: dict | None = None,
    title: str = "",
) -> None:
    """Rewrite container metadata without re-encoding (-c copy)."""
    args = ["-i", str(input_path), "-c", "copy"]
    _append_video_metadata(
        args,
        remove_metadata=True,
        author_meta=author_meta,
        title=title or input_path.stem,
    )
    run_ffmpeg_to_file(args, output_path)


def convert_video(
    input_path: Path,
    output_path: Path,
    *,
    output_format: str = "webm",
    remove_metadata: bool = True,
    keep_audio: bool = True,
    reencode: bool = False,
    compression_level: str = DEFAULT_COMPRESSION_ID,
    author_meta: dict | None = None,
    title: str = "",
) -> None:
    fmt = output_format.lower().lstrip(".")
    probe = probe_video(input_path)

    needs_reencode = reencode or fmt == "webm"
    if fmt in ("mp4", "mov", "m4v") and not needs_reencode:
        if not is_mp4_video_copy_safe(
            probe.video_codec,
            pix_fmt=probe.pix_fmt,
            profile=probe.profile,
        ):
            get_logger().info(
                "Auto re-encoding %s for %s compatibility (codec=%s, pix_fmt=%s)",
                input_path.name,
                fmt.upper(),
                probe.video_codec,
                probe.pix_fmt or "?",
            )
            needs_reencode = True

    args = ["-i", str(input_path), "-map", "0:v:0"]

    if needs_reencode:
        if fmt in ("mp4", "mov", "m4v"):
            args.extend(ffmpeg_mobile_video_prep_args(fmt))
        args.extend(ffmpeg_video_encode_args(fmt, compression_level))
    else:
        args.extend(["-c:v", "copy"])

    if keep_audio and probe.has_audio:
        args.extend(["-map", "0:a?"])
        args.extend(ffmpeg_audio_encode_args(fmt))
    else:
        args.append("-an")

    _append_video_metadata(
        args,
        remove_metadata=remove_metadata,
        author_meta=author_meta,
        title=title,
    )
    args.extend(ffmpeg_container_mux_args(fmt))
    run_ffmpeg_to_file(args, output_path)


PIXIV_UGOIRA_DEFAULT_MAX_MB = 30


@dataclass
class UgoiraChunk:
    index: int
    frames_dir: Path
    frame_count: int
    json_path: Path
    size_bytes: int = 0
    jpeg_quality: int = 0


@dataclass
class UgoiraExportResult:
    source: Path
    output_dir: Path
    chunks: list[UgoiraChunk]
    total_frames: int


def _ugoira_delay_ms(fps: int) -> int:
    return max(1, round(1000 / max(1, fps)))


def _ugoira_folder_bytes(folder: Path) -> int:
    return sum(p.stat().st_size for p in folder.glob("*.jpg"))


def _ugoira_quality_to_qv(quality: int) -> int:
    return max(2, min(31, int((100 - quality) / 3) + 2))


def _ugoira_target_width(source_width: int, max_width: int) -> int | None:
    """Return output width when downscale is needed (never upscale)."""
    limit = max(0, int(max_width))
    if limit <= 0 or source_width <= limit:
        return None
    return limit


def _ugoira_vf_chain(fps: int, source_width: int, max_width: int) -> str:
    parts = [f"fps={fps}"]
    target_w = _ugoira_target_width(source_width, max_width)
    if target_w is not None:
        parts.append(f"scale={target_w}:-2")
    return ",".join(parts)


def _ugoira_scaled_height(
    source_width: int,
    source_height: int,
    max_width: int,
) -> int:
    target_w = _ugoira_target_width(source_width, max_width)
    if target_w is None:
        return source_height
    return max(1, round(source_height * target_w / source_width))


def _ugoira_watermark_filter(
    fps: int,
    source_width: int,
    source_height: int,
    max_width: int,
    settings: WatermarkSettings,
) -> str:
    scaled_h = _ugoira_scaled_height(source_width, source_height, max_width)
    target_w = _ugoira_target_width(source_width, max_width)
    if target_w is not None:
        main = f"[0:v]fps={fps},scale={target_w}:-2[vid]"
    else:
        main = f"[0:v]fps={fps}[vid]"
    overlay = ffmpeg_overlay_on_label(
        "vid", settings, frame_height=scaled_h, out_label="out"
    )
    return f"{main};{overlay}"


def _enforce_ugoira_max_width(frames_dir: Path, max_width: int) -> None:
    """Resize frames wider than max_width (safety net after ffmpeg extract)."""
    limit = max(0, int(max_width))
    if limit <= 0:
        return
    from PIL import Image

    for path in sorted(frames_dir.glob("*.jpg")):
        with Image.open(path) as img:
            if img.width <= limit:
                continue
            ratio = limit / img.width
            height = max(1, int(img.height * ratio))
            resized = img.resize((limit, height), Image.Resampling.LANCZOS).convert("RGB")
            resized.save(path, "JPEG", quality=95, optimize=True)


def _recompress_ugoira_frames(
    frames_dir: Path,
    quality: int,
    *,
    scale: float = 1.0,
) -> int:
    from PIL import Image

    q = max(30, min(95, quality))
    for path in sorted(frames_dir.glob("*.jpg")):
        with Image.open(path) as img:
            rgb = img.convert("RGB")
            if scale < 0.999:
                width = max(64, int(rgb.width * scale))
                height = max(64, int(rgb.height * scale))
                rgb = rgb.resize((width, height), Image.Resampling.LANCZOS)
            rgb.save(
                path,
                "JPEG",
                quality=q,
                optimize=True,
                subsampling=2,
            )
    return _ugoira_folder_bytes(frames_dir)


def fit_ugoira_chunk_to_budget(
    frames_dir: Path,
    max_bytes: int,
    *,
    start_quality: int,
    author_meta: dict | None = None,
) -> dict:
    """Shrink JPEG frames until the ugoira chunk fits Pixiv upload budget."""
    quality = max(30, min(95, start_quality))
    scale = 1.0
    size = _ugoira_folder_bytes(frames_dir)

    if size > max_bytes:
        while quality >= 30:
            size = _recompress_ugoira_frames(frames_dir, quality)
            if size <= max_bytes:
                break
            quality -= 5

        if size > max_bytes:
            scale = 0.9
            while scale >= 0.45:
                size = _recompress_ugoira_frames(frames_dir, max(30, quality), scale=scale)
                if size <= max_bytes:
                    break
                scale -= 0.08

        if size > max_bytes:
            scale = 0.45
            quality = 30
            size = _recompress_ugoira_frames(frames_dir, quality, scale=scale)

    if author_meta:
        embed_author_in_folder(frames_dir, author_meta, quality=quality)
        size = _ugoira_folder_bytes(frames_dir)

    return {
        "quality": quality,
        "scale": round(scale, 2),
        "bytes": size,
        "within_budget": size <= max_bytes,
    }


def _write_ugoira_json(frames_dir: Path, fps: int) -> Path:
    frames = sorted(frames_dir.glob("*.jpg"))
    delay = _ugoira_delay_ms(fps)
    payload = {
        "frames": [
            {"file": frame.name, "delay": delay}
            for frame in frames
        ],
    }
    json_path = frames_dir / "animation.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return json_path


UGOIRA_OPTION_KEYS = frozenset({
    "chunk_sec",
    "fps",
    "max_frames",
    "auto_fps",
    "quality",
    "auto_fit_size",
    "max_chunk_mb",
    "max_width",
    "watermark_path",
    "watermark_settings",
    "author_meta",
})


def filter_ugoira_options(options: dict) -> dict:
    return {key: options[key] for key in UGOIRA_OPTION_KEYS if key in options}


def export_ugoira(
    input_path: Path,
    output_dir: Path,
    *,
    chunk_sec: int = 10,
    fps: int = 20,
    max_frames: int = 150,
    auto_fps: bool = True,
    quality: int = 80,
    auto_fit_size: bool = True,
    max_chunk_mb: float = PIXIV_UGOIRA_DEFAULT_MAX_MB,
    max_width: int = 1200,
    watermark_path: Path | None = None,
    watermark_settings: WatermarkSettings | None = None,
    author_meta: dict | None = None,
) -> UgoiraExportResult:
    probe = probe_video(input_path)
    duration = probe.duration
    if duration <= 0:
        raise FfmpegError(f"could not determine duration: {input_path.name}")

    fps = resolve_ugoira_fps(
        chunk_sec,
        max_frames=max_frames,
        auto_fps=auto_fps,
        manual_fps=fps,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    num_chunks = max(1, math.ceil(duration / chunk_sec))
    chunks: list[UgoiraChunk] = []
    total_frames = 0
    qv = _ugoira_quality_to_qv(quality)
    max_chunk_bytes = max(1, int(max_chunk_mb * 1024 * 1024))
    extract_max_width = max(320, int(max_width))

    for i in range(num_chunks):
        start = i * chunk_sec
        part_path = output_dir / f"part_{i:03d}.mp4"
        frames_dir = output_dir / f"frames_{i:03d}"
        frames_dir.mkdir(parents=True, exist_ok=True)

        run_ffmpeg([
            "-ss", str(start),
            "-t", str(chunk_sec),
            "-i", str(input_path),
            "-c", "copy",
            str(part_path),
        ])

        if watermark_path and watermark_settings:
            scaled_h = _ugoira_scaled_height(
                probe.width, probe.height, extract_max_width
            )
            wm_h = watermark_height_px(scaled_h, watermark_settings)
            get_logger().info(
                "Ugoira watermark: scaled %dx%d, wm height %dpx (%.1f%%)",
                _ugoira_target_width(probe.width, extract_max_width) or probe.width,
                scaled_h,
                wm_h,
                watermark_settings.clamp().height_pct,
            )
            filt = _ugoira_watermark_filter(
                fps,
                probe.width,
                probe.height,
                extract_max_width,
                watermark_settings,
            )
            run_ffmpeg([
                "-i", str(part_path),
                "-i", str(watermark_path),
                "-filter_complex", filt,
                "-map", "[out]",
                "-vsync", "vfr",
                "-vframes", str(max_frames),
                "-q:v", str(qv),
                str(frames_dir / "%04d.jpg"),
            ])
        else:
            run_ffmpeg([
                "-i", str(part_path),
                "-vf", _ugoira_vf_chain(fps, probe.width, extract_max_width),
                "-vframes", str(max_frames),
                "-q:v", str(qv),
                str(frames_dir / "%04d.jpg"),
            ])

        if part_path.exists():
            part_path.unlink()

        _enforce_ugoira_max_width(frames_dir, extract_max_width)

        frame_count = len(list(frames_dir.glob("*.jpg")))
        fit_info = {"quality": quality, "scale": 1.0, "bytes": _ugoira_folder_bytes(frames_dir)}
        if auto_fit_size and frame_count > 0:
            fit_info = fit_ugoira_chunk_to_budget(
                frames_dir,
                max_chunk_bytes,
                start_quality=quality,
                author_meta=author_meta,
            )
        elif author_meta:
            embed_author_in_folder(frames_dir, author_meta, quality=quality)
            fit_info["bytes"] = _ugoira_folder_bytes(frames_dir)

        total_frames += frame_count
        json_path = _write_ugoira_json(frames_dir, fps)
        chunks.append(
            UgoiraChunk(
                i,
                frames_dir,
                frame_count,
                json_path,
                size_bytes=int(fit_info["bytes"]),
                jpeg_quality=int(fit_info["quality"]),
            )
        )

    return UgoiraExportResult(
        source=input_path,
        output_dir=output_dir,
        chunks=chunks,
        total_frames=total_frames,
    )


def _process_one(
    source: Path,
    output_dir: Path,
    job: str,
    **kwargs,
) -> VideoJobResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        probe = probe_video(source)
    except FfmpegError as exc:
        return VideoJobResult(source, None, False, str(exc))

    try:
        output_stem = kwargs.get("output_stem")

        if job == "watermark":
            wm_path = kwargs["watermark_path"]
            settings = kwargs["watermark_settings"]
            out = _output_path(
                source, output_dir, "_watermark", ".webm", output_stem=output_stem
            )
            apply_watermark(
                source,
                out,
                wm_path,
                settings,
                copy_audio=True,
                remove_metadata=kwargs.get("remove_metadata", True),
                compression_level=kwargs.get(
                    "compression_level", DEFAULT_COMPRESSION_ID
                ),
                author_meta=kwargs.get("author_meta"),
                title=output_stem or source.stem,
            )
            return VideoJobResult(source, out, True, probe=probe)

        if job == "gif":
            out = _output_path(source, output_dir, "", ".gif", output_stem=output_stem)
            export_gif(
                source,
                out,
                fps=kwargs["fps"],
                width=kwargs["width"],
                remove_metadata=kwargs.get("remove_metadata", True),
                author_meta=kwargs.get("author_meta"),
                title=output_stem or source.stem,
            )
            return VideoJobResult(source, out, True, probe=probe)

        if job == "convert":
            ext = f".{kwargs['output_format'].lstrip('.')}"
            suffix = ""
            if not output_stem:
                if not kwargs.get("keep_audio"):
                    suffix = "_noaudio"
                if kwargs.get("remove_metadata"):
                    suffix += "_clean"
            out = _output_path(
                source, output_dir, suffix, ext, output_stem=output_stem
            )
            convert_video(
                source,
                out,
                output_format=kwargs["output_format"],
                remove_metadata=kwargs.get("remove_metadata", True),
                keep_audio=kwargs.get("keep_audio", True),
                reencode=kwargs.get("reencode", False),
                compression_level=kwargs.get(
                    "compression_level", DEFAULT_COMPRESSION_ID
                ),
                author_meta=kwargs.get("author_meta"),
                title=output_stem or source.stem,
            )
            return VideoJobResult(source, out, True, probe=probe)

        if job == "metadata":
            title = output_stem or source.stem
            ext = source.suffix
            if kwargs.get("in_place"):
                temp = source.with_name(f".{source.stem}.meta{ext}")
                try:
                    patch_video_metadata(
                        source,
                        temp,
                        author_meta=kwargs.get("author_meta"),
                        title=title,
                    )
                    temp.replace(source)
                except Exception:
                    if temp.exists():
                        temp.unlink()
                    raise
                return VideoJobResult(source, source, True, probe=probe)

            out = _output_path(source, output_dir, "", ext, output_stem=output_stem)
            patch_video_metadata(
                source,
                out,
                author_meta=kwargs.get("author_meta"),
                title=title,
            )
            return VideoJobResult(source, out, True, probe=probe)

        return VideoJobResult(source, None, False, f"unknown operation: {job}")
    except FfmpegError as exc:
        return VideoJobResult(source, None, False, str(exc), probe=probe)


def process_video_batch(
    sources: list[Path],
    output_dir: Path,
    job: str,
    *,
    workers: int = 2,
    base_name: str = "",
    on_progress: ProgressCallback | None = None,
    **kwargs,
) -> VideoBatchSummary:
    summary = VideoBatchSummary(total=len(sources))
    if not sources:
        return summary

    in_place = bool(kwargs.get("in_place"))
    out_dir = output_dir if in_place else job_output_dir(output_dir, job)
    pack = base_name.strip()
    if job == "metadata" and in_place:
        pack = ""
    workers = max(1, min(workers, len(sources)))
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for index, src in enumerate(sources, start=1):
            job_kwargs = dict(kwargs)
            if pack:
                job_kwargs["output_stem"] = f"{pack}_{index}"
            futures[pool.submit(_process_one, src, out_dir, job, **job_kwargs)] = src
        for future in as_completed(futures):
            result = future.result()
            completed += 1
            if result.success:
                summary.processed += 1
            else:
                summary.failed += 1
            summary.results.append(result)
            if on_progress:
                on_progress(completed, len(sources), result)

    return summary