"""Generate the legacy TV guide voice clips with Alibaba Cloud TTS."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.aliyun_tts import (
    AliyunTTSClient,
    DEFAULT_MODEL,
    DEFAULT_SAMPLE_RATE,
    redact_sensitive,
)


OUT_DIR = Path("videos/annual-meeting-trailer/assets/audio/annual-meeting")

LINES = {
    "guide-intro": "今晚推荐，笑一个职场错调。",
    "guide-mid": "一群人把年会，唱成了职场现场。",
    "guide-outro": "《年会不能停！》，今晚推荐。",
}

SRT_TIMES = {
    "guide-intro": "00:00:00,000 --> 00:00:03,360",
    "guide-mid": "00:00:00,000 --> 00:00:03,936",
    "guide-outro": "00:00:00,000 --> 00:00:03,792",
}


def probe_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True,
            text=True,
            check=True,
            timeout=8,
        )
        value = float(result.stdout.strip())
        return value if value > 0 else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _timestamp(seconds: float) -> str:
    milliseconds = max(1, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds_part, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d},{millis:03d}"


def write_srt(path: Path, text: str, *, duration_s: float | None, fallback_time: str) -> None:
    timing = f"00:00:00,000 --> {_timestamp(duration_s)}" if duration_s is not None else fallback_time
    path.write_text(f"1\n{timing}\n{text}\n", encoding="utf-8")


def generate_all(
    *,
    out_dir: Path = OUT_DIR,
    model: str = DEFAULT_MODEL,
    voice: str,
    format: str = "mp3",
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    stream: bool = False,
    language_type: str | None = None,
    extra: Mapping[str, Any] | None = None,
    fallback_duration: float | None = 30.0,
    client: AliyunTTSClient | None = None,
) -> dict[str, Any]:
    if fallback_duration is not None and fallback_duration <= 0:
        raise ValueError("fallback_duration must be positive")
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    api = client or AliyunTTSClient()
    clips = []
    for name, text in LINES.items():
        audio_path = out_dir / f"{name}.{format}"
        subtitle_path = out_dir / f"{name}.srt"
        api.synthesize(
            text=text,
            voice=voice,
            out=audio_path,
            model=model,
            format=format,
            sample_rate=sample_rate,
            stream=stream,
            language_type=language_type,
            extra=extra,
        )
        duration = probe_duration(audio_path)
        fallback_time = SRT_TIMES[name]
        if duration is None:
            if fallback_duration is not None:
                duration = fallback_duration
                fallback_time = f"00:00:00,000 --> {_timestamp(fallback_duration)}"
                print(
                    f"Warning: ffprobe could not read {audio_path.name}; "
                    f"using fallback duration {fallback_duration:.3f}s",
                    file=sys.stderr,
                )
        write_srt(subtitle_path, text, duration_s=duration, fallback_time=fallback_time)
        clips.append({
            "name": name,
            "text": text,
            "audio": audio_path.name,
            "srt": subtitle_path.name,
            "duration_s": round(duration, 3) if duration is not None else None,
        })
    parameters: dict[str, Any] = {
        "model": model,
        "voice": voice,
        "format": format,
        "sample_rate": sample_rate,
        "stream": stream,
    }
    if language_type is not None:
        parameters["language_type"] = language_type
    if extra is not None:
        parameters["extra"] = redact_sensitive(extra)
    if fallback_duration is not None:
        parameters["fallback_duration"] = fallback_duration
    manifest = {
        "project": "annual-meeting-trailer",
        "provider": "aliyun-dashscope",
        "model": model,
        "voice": voice,
        "format": format,
        "sample_rate": sample_rate,
        "stream": stream,
        "parameters": parameters,
        "clips": clips,
    }
    (out_dir / "voiceover-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def _parse_extra(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("--extra-json must contain a JSON object")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate TV guide clips with Alibaba Cloud TTS")
    parser.add_argument("--voice", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--format", choices=("mp3", "wav"), default="mp3")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--language-type")
    parser.add_argument("--extra-json")
    parser.add_argument("--fallback-duration", type=float, default=30.0)
    parser.add_argument("--api-key", help=argparse.SUPPRESS)
    parser.add_argument("--base-url", help=argparse.SUPPRESS)
    parser.add_argument("--dotenv", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    client = AliyunTTSClient(api_key=args.api_key, base_url=args.base_url, dotenv_path=args.dotenv)
    manifest = generate_all(
        out_dir=args.out,
        model=args.model,
        voice=args.voice,
        format=args.format,
        sample_rate=args.sample_rate,
        stream=args.stream,
        language_type=args.language_type,
        extra=_parse_extra(args.extra_json),
        fallback_duration=args.fallback_duration,
        client=client,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
