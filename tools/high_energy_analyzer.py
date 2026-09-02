"""Deterministic media signals and selection validation for high-energy clips."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from array import array
from pathlib import Path
from typing import Any, Iterable


FEATURE_WEIGHTS = {
    "cut_density": 0.30,
    "audio_peak": 0.30,
    "visual_change": 0.25,
    "dialogue_signal": 0.15,
}


class AnalysisError(RuntimeError):
    pass


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _clamp01(value: Any) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return max(0.0, min(1.0, number))


def score_features(features: dict[str, Any]) -> float:
    """Return a 0-100 score, renormalizing when optional signals are missing."""

    weighted = 0.0
    weight_total = 0.0
    for name, weight in FEATURE_WEIGHTS.items():
        value = _clamp01(features.get(name))
        if value is None:
            continue
        weighted += value * weight
        weight_total += weight
    return round(100.0 * weighted / weight_total, 2) if weight_total else 0.0


def _signals(features: dict[str, Any]) -> list[str]:
    labels = {
        "cut_density": "rapid_cuts",
        "audio_peak": "audio_peak",
        "visual_change": "visual_change",
        "dialogue_signal": "dialogue_signal",
    }
    return [
        labels[name]
        for name in FEATURE_WEIGHTS
        if (_clamp01(features.get(name)) or 0.0) >= 0.75
    ]


def build_candidate_windows(
    shots: Iterable[dict[str, Any]],
    target_duration_s: float | None,
    *,
    max_candidates: int = 5,
    tolerance_ratio: float = 0.25,
) -> list[dict[str, Any]]:
    """Build ranked contiguous source windows when a target is available."""

    if target_duration_s is None:
        return []
    target = _number(target_duration_s)
    if target is None or target <= 0:
        raise ValueError("target_duration_s must be greater than zero")
    normalized = []
    for shot in shots:
        start = _number(shot.get("source_in"))
        end = _number(shot.get("source_out"))
        if start is None or end is None or end <= start:
            continue
        features = dict(shot.get("features") or {})
        score = _number(shot.get("score"))
        normalized.append({
            **shot,
            "source_in": start,
            "source_out": end,
            "score": score if score is not None else score_features(features),
            "features": features,
        })

    if not normalized:
        return []

    lower = max(0.1, target * (1.0 - tolerance_ratio))
    upper = target * (1.0 + tolerance_ratio)
    candidates: list[dict[str, Any]] = []
    for start_index in range(len(normalized)):
        duration = 0.0
        window = []
        for end_index in range(start_index, len(normalized)):
            shot = normalized[end_index]
            duration += shot["source_out"] - shot["source_in"]
            window.append(shot)
            if duration < lower:
                continue
            if duration > upper:
                break
            average_score = sum(item["score"] for item in window) / len(window)
            signal_values = {
                name: max(
                    (_clamp01(item["features"].get(name)) or 0.0)
                    for item in window
                )
                for name in FEATURE_WEIGHTS
            }
            candidates.append({
                "source_segments": [item.get("id", f"shot-{index + 1:03d}") for index, item in enumerate(window, start=start_index)],
                "source_in": window[0]["source_in"],
                "source_out": window[-1]["source_out"],
                "estimated_duration_s": round(duration, 3),
                "energy_score": round(average_score, 2),
                "signals": _signals(signal_values),
                "arc": ["needs_semantic_review"],
                "selection_reason": "Deterministic audio, cut-density and visual-signal shortlist; semantic review required.",
                "warnings": [],
            })

    candidates.sort(
        key=lambda item: (-item["energy_score"], abs(item["estimated_duration_s"] - target), item["source_in"])
    )
    unique: list[dict[str, Any]] = []
    seen_ranges = set()
    for candidate in candidates:
        key = (candidate["source_in"], candidate["source_out"])
        if key in seen_ranges:
            continue
        seen_ranges.add(key)
        candidate["candidate_id"] = f"hec-{len(unique) + 1:03d}"
        unique.append(candidate)
        if len(unique) >= max_candidates:
            break
    return unique


def validate_selection(
    selection: dict[str, Any],
    source_duration_s: float | None,
    *,
    tolerance_s: float = 0.5,
) -> dict[str, Any]:
    errors: list[str] = []
    segments = selection.get("segments") or []
    source_duration = _number(source_duration_s)
    target = _number(selection.get("target_duration_s"))
    allow_reuse = bool(selection.get("allow_reuse", False))
    order_policy = selection.get("order_policy", "chronological")
    seen_ids: set[str] = set()
    previous_timeline_end: float | None = None
    previous_source_in: float | None = None
    computed_duration = 0.0

    for segment in segments:
        segment_id = str(segment.get("segment_id", ""))
        source_in = _number(segment.get("source_in"))
        source_out = _number(segment.get("source_out"))
        timeline_start = _number(segment.get("timeline_start"))
        timeline_end = _number(segment.get("timeline_end"))
        rate = _number(segment.get("playback_rate"))
        audio_rate = _number(segment.get("audio_playback_rate"))

        if segment_id in seen_ids and not allow_reuse:
            errors.append("segment_reuse_requires_explicit_allow_reuse")
        seen_ids.add(segment_id)
        if source_in is None or source_out is None or source_in < 0 or source_out <= source_in:
            errors.append("invalid_source_range")
        elif source_duration is not None and source_out > source_duration + 1e-6:
            errors.append("source_range_out_of_bounds")
        if timeline_start is None or timeline_end is None or timeline_start < 0 or timeline_end <= timeline_start:
            errors.append("invalid_timeline_range")
        else:
            computed_duration += timeline_end - timeline_start
            if previous_timeline_end is not None:
                if timeline_start > previous_timeline_end + 1e-6:
                    errors.append("timeline_gap")
                elif timeline_start < previous_timeline_end - 1e-6:
                    errors.append("timeline_overlap")
            previous_timeline_end = timeline_end
        if rate is not None and audio_rate is not None and abs(rate - audio_rate) > 1e-6:
            errors.append("picture_audio_rate_mismatch")
        if order_policy == "chronological" and source_in is not None:
            if previous_source_in is not None and source_in < previous_source_in - 1e-6:
                errors.append("chronological_order_violation")
            previous_source_in = source_in

    if not segments:
        errors.append("selection_has_no_segments")
    if target is None or target <= 0:
        errors.append("invalid_target_duration")
    elif abs(computed_duration - target) > tolerance_s:
        errors.append("target_duration_mismatch")

    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "computed_duration_s": round(computed_duration, 3),
        "target_duration_s": target,
        "segment_count": len(segments),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], *, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
    )


def _tool_version(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        return "missing"
    try:
        result = _run([executable, "-version"])
    except (OSError, subprocess.CalledProcessError):
        return executable
    first_line = (result.stdout or result.stderr).splitlines()
    return first_line[0].strip() if first_line else executable


def probe_media(path: Path) -> dict[str, Any]:
    if shutil.which("ffprobe") is None:
        raise AnalysisError("ffprobe is required to determine source duration")
    try:
        result = _run([
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(path),
        ])
        payload = json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"ffprobe could not read {path}") from exc
    streams = payload.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    subtitles = [stream for stream in streams if stream.get("codec_type") == "subtitle"]
    return {
        "duration_s": _number(payload.get("format", {}).get("duration")),
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": video.get("r_frame_rate"),
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name"),
        "has_audio": bool(audio),
        "subtitle_streams": len(subtitles),
        "has_subtitles": bool(subtitles),
        "format": payload.get("format", {}).get("format_name"),
    }


def detect_scene_boundaries(path: Path, duration_s: float) -> tuple[list[float], list[str]]:
    warnings: list[str] = []
    if shutil.which("ffmpeg") is None:
        return [0.0, duration_s], ["ffmpeg_missing_scene_detection_skipped"]
    try:
        result = _run([
            "ffmpeg", "-hide_banner", "-i", str(path), "-vf",
            "select='gt(scene,0.30)',showinfo", "-an", "-f", "null", "-",
        ])
    except (OSError, subprocess.CalledProcessError):
        return [0.0, duration_s], ["scene_detection_failed"]
    boundaries = [0.0]
    for match in re.finditer(r"pts_time:([0-9]+(?:\.[0-9]+)?)", result.stderr):
        point = min(duration_s, max(0.0, float(match.group(1))))
        if point - boundaries[-1] >= 0.1:
            boundaries.append(point)
    if duration_s - boundaries[-1] >= 0.1:
        boundaries.append(duration_s)
    elif boundaries[-1] != duration_s:
        boundaries.append(duration_s)
    return boundaries, warnings


def extract_audio_bins(path: Path, *, sample_rate: int = 8000, bin_s: float = 0.5) -> tuple[list[dict[str, float]], list[str]]:
    if shutil.which("ffmpeg") is None:
        return [], ["ffmpeg_missing_audio_analysis_skipped"]
    try:
        result = _run([
            "ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1",
            "-ar", str(sample_rate), "-f", "s16le", "pipe:1",
        ], binary=True)
    except (OSError, subprocess.CalledProcessError):
        return [], ["audio_analysis_failed_or_audio_missing"]
    samples = array("h")
    samples.frombytes(result.stdout)
    samples_per_bin = max(1, int(sample_rate * bin_s))
    bins = []
    for index in range(0, len(samples), samples_per_bin):
        chunk = samples[index:index + samples_per_bin]
        if not chunk:
            continue
        normalized = [abs(value) / 32768.0 for value in chunk]
        rms = math.sqrt(sum(value * value for value in normalized) / len(normalized))
        bins.append({
            "start": round(index / sample_rate, 3),
            "end": round((index + len(chunk)) / sample_rate, 3),
            "rms": round(rms, 6),
            "peak": round(max(normalized), 6),
        })
    return bins, []


def load_transcript(path: str | Path | None) -> tuple[list[dict[str, Any]], list[str]]:
    """Load word-level timestamps emitted by HyperFrames transcription."""

    if path is None:
        return [], ["word_level_transcript_not_provided"]
    transcript_path = Path(path).expanduser()
    if not transcript_path.is_file():
        return [], ["transcript_file_missing"]
    if transcript_path.suffix.lower() in {".srt", ".vtt"}:
        return [], ["subtitle_file_requires_hyperframes_word_timestamps"]
    try:
        payload = json.loads(transcript_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return [], ["transcript_file_unreadable"]
    raw_words = payload.get("words", []) if isinstance(payload, dict) else payload
    if not isinstance(raw_words, list):
        return [], ["transcript_words_missing"]
    words = []
    for word in raw_words:
        if not isinstance(word, dict):
            continue
        start = _number(word.get("start"))
        end = _number(word.get("end"))
        text = str(word.get("text", "")).strip()
        if start is not None and end is not None and end > start and text:
            words.append({"text": text, "start": start, "end": end})
    if not words:
        return [], ["transcript_has_no_valid_words"]
    return words, []


def _shot_features(
    start: float,
    end: float,
    audio_bins: list[dict[str, float]],
    transcript_words: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    duration = end - start
    overlapping = [item for item in audio_bins if item["end"] > start and item["start"] < end]
    audio_peak = max((item["peak"] for item in overlapping), default=None)
    if transcript_words is None:
        dialogue_signal = None
    else:
        word_count = sum(
            1
            for word in transcript_words
            if word["end"] > start and word["start"] < end
        )
        dialogue_signal = min(1.0, word_count / 4.0)
    return {
        "cut_density": round(max(0.0, min(1.0, 1.0 - duration / 4.0)), 4),
        "audio_peak": audio_peak,
        "visual_change": None,
        "dialogue_signal": dialogue_signal,
    }


def analyze_file(
    input_path: str | Path,
    target_duration_s: float | None,
    output_path: str | Path,
    *,
    transcript_path: str | Path | None = None,
) -> dict[str, Any]:
    source = Path(input_path).expanduser().resolve()
    if not source.is_file():
        raise AnalysisError(f"source file does not exist: {input_path}")
    metadata = probe_media(source)
    duration = metadata.get("duration_s")
    if duration is None or duration <= 0:
        raise AnalysisError("source duration is unavailable")
    boundaries, warnings = detect_scene_boundaries(source, duration)
    audio_bins, audio_warnings = extract_audio_bins(source)
    warnings.extend(audio_warnings)
    transcript_words, transcript_warnings = load_transcript(transcript_path)
    warnings.extend(transcript_warnings)
    shots = []
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        features = _shot_features(
            start,
            end,
            audio_bins,
            transcript_words or None,
        )
        shots.append({
            "id": f"shot-{index:03d}",
            "source_in": round(start, 3),
            "source_out": round(end, 3),
            "duration_s": round(end - start, 3),
            "features": features,
            "score": score_features(features),
        })
    if target_duration_s is None:
        candidates = []
        warnings.append("duration_not_fixed_content_review_required")
    else:
        candidates = build_candidate_windows(shots, target_duration_s)
        if not candidates:
            warnings.append("no_candidate_matches_target_duration")
    transcript_info = None
    if transcript_path is not None:
        transcript_file = Path(transcript_path).expanduser()
        transcript_info = {
            "path": str(transcript_file.resolve()),
            "sha256": _sha256(transcript_file) if transcript_file.is_file() else None,
            "word_count": len(transcript_words),
        }
    payload = {
        "schema_version": 1,
        "analysis_type": "high-energy-clip",
        "source": {
            "path": str(source),
            "sha256": _sha256(source),
            "metadata": metadata,
        },
        "features": {
            "method": "ffprobe + ffmpeg scene detection + PCM audio energy",
            "semantic_review_required": True,
        },
        "duration": {
            "mode": "content_driven_pending" if target_duration_s is None else "fixed_target",
            "target_duration_s": _number(target_duration_s),
            "decision_required": target_duration_s is None,
        },
        "transcript": transcript_info,
        "shots": shots,
        "candidates": candidates,
        "warnings": sorted(set(warnings + ["visual_change_and_dialogue_signal_require_semantic_review"])),
        "tool_versions": {
            "ffprobe": _tool_version("ffprobe"),
            "ffmpeg": _tool_version("ffmpeg"),
        },
    }
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _command_analyze(args: argparse.Namespace) -> int:
    try:
        payload = analyze_file(
            args.input,
            args.target_duration,
            args.out,
            transcript_path=args.transcript,
        )
    except AnalysisError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({
        "ok": True,
        "out": str(args.out),
        "candidate_count": len(payload["candidates"]),
        "duration_mode": payload["duration"]["mode"],
    }))
    return 0


def _command_validate(args: argparse.Namespace) -> int:
    selection = json.loads(Path(args.selection).read_text(encoding="utf-8"))
    result = validate_selection(selection, args.source_duration, tolerance_s=args.tolerance)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze")
    analyze.add_argument("--input", required=True)
    analyze.add_argument(
        "--target-duration",
        type=float,
        help="Optional soft filter after a duration has been chosen; omit during content review.",
    )
    analyze.add_argument("--out", required=True)
    analyze.add_argument(
        "--transcript",
        help="Optional HyperFrames word-level transcript JSON for dialogue scoring.",
    )
    analyze.set_defaults(handler=_command_analyze)
    validate = commands.add_parser("validate")
    validate.add_argument("--selection", required=True)
    validate.add_argument("--source-duration", required=True, type=float)
    validate.add_argument("--tolerance", type=float, default=0.5)
    validate.set_defaults(handler=_command_validate)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    raise SystemExit(args.handler(args))
