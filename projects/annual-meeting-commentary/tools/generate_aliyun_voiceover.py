"""Generate commentary voiceover chapters with Alibaba Cloud TTS."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.aliyun_tts import (
    AliyunTTSClient,
    DEFAULT_MODEL,
    DEFAULT_SAMPLE_RATE,
    redact_sensitive,
)


SCRIPT_PATH = PROJECT_DIR / "edit-plan.md"
OUTPUT_DIR = PROJECT_DIR / "generated" / "voiceover"


def extract_chapters(markdown: str) -> list[tuple[str, str]]:
    match = re.search(
        r"^## 旁白逐字稿草案\s*$([\s\S]*?)^## 素材状态与核验要求\s*$",
        markdown,
        re.MULTILINE,
    )
    if not match:
        raise ValueError("Could not locate the narration draft in edit-plan.md")
    chapters: list[tuple[str, str]] = []
    for chapter_match in re.finditer(
        r"^### (.+?)\s*$([\s\S]*?)(?=^### |\Z)", match.group(1), re.MULTILINE
    ):
        title = chapter_match.group(1).strip()
        body_lines = []
        for line in chapter_match.group(2).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("【"):
                continue
            body_lines.append(stripped)
        text = "\n".join(body_lines)
        if text:
            chapters.append((title, text))
    if not chapters:
        raise ValueError("No narration chapters found")
    return chapters


def safe_name(title: str, index: int) -> str:
    name = re.sub(r"^\d{2}:\d{2}[–-]\d{2}:\d{2}\s*[·.]\s*", "", title)
    name = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", name).strip("-")
    return f"{index:02d}-{name or 'chapter'}"


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


def write_srt(path: Path, text: str, duration_s: float) -> None:
    path.write_text(
        f"1\n00:00:00,000 --> {_timestamp(duration_s)}\n{text}\n",
        encoding="utf-8",
    )


def generate_voiceover(
    *,
    script: Path = SCRIPT_PATH,
    out_dir: Path = OUTPUT_DIR,
    model: str = DEFAULT_MODEL,
    voice: str,
    format: str = "mp3",
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    stream: bool = False,
    language_type: str | None = None,
    extra: Mapping[str, Any] | None = None,
    fallback_duration: float = 30.0,
    client: AliyunTTSClient | None = None,
) -> dict[str, Any]:
    if fallback_duration <= 0:
        raise ValueError("fallback_duration must be positive")
    source = Path(script).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    api = client or AliyunTTSClient()
    chapters = []
    for index, (title, text) in enumerate(
        extract_chapters(source.read_text(encoding="utf-8")), start=1
    ):
        name = safe_name(title, index)
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
        if duration is None:
            duration = fallback_duration
            print(
                f"Warning: ffprobe could not read {audio_path.name}; "
                f"using fallback duration {fallback_duration:.3f}s",
                file=sys.stderr,
            )
        write_srt(subtitle_path, text, duration)
        chapter_manifest = {
            "name": name,
            "title": title,
            "text": text,
            "voice": voice,
            "audio": audio_path.name,
            "srt": subtitle_path.name,
            "duration_s": round(duration, 3),
        }
        if format == "mp3":
            # Preserve the historical manifest field used by older consumers.
            chapter_manifest["mp3"] = audio_path.name
        chapters.append(chapter_manifest)
    parameters: dict[str, Any] = {
        "model": model,
        "voice": voice,
        "format": format,
        "sample_rate": sample_rate,
        "stream": stream,
        "fallback_duration": fallback_duration,
    }
    if language_type is not None:
        parameters["language_type"] = language_type
    if extra is not None:
        parameters["extra"] = redact_sensitive(extra)
    manifest = {
        "project": "annual-meeting-commentary",
        "source_script": str(source),
        "provider": "aliyun-dashscope",
        "model": model,
        "voice": voice,
        "format": format,
        "sample_rate": sample_rate,
        "stream": stream,
        "parameters": parameters,
        "chapters": chapters,
        "total_duration_s": round(sum(item["duration_s"] for item in chapters), 3),
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
    parser = argparse.ArgumentParser(description="Generate commentary voiceover with Alibaba Cloud TTS")
    parser.add_argument("--script", type=Path, default=SCRIPT_PATH)
    parser.add_argument("--out", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
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
    manifest = generate_voiceover(
        script=args.script,
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
