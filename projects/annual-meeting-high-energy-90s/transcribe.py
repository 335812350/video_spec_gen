import json
import os
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets" / "annual-meeting" / "media" / "年会不能停！.mp4"
OUT_DIR = Path(__file__).resolve().parent / "hyperframes" / "assets"
TMP_DIR = Path(__file__).resolve().parent / "_transcribe_tmp"
SEGMENTS = [
    ("gala-performance-hook", 6015.0, 6021.0, 0.0),
    ("gala-rap-opening", 6056.0, 6068.0, 6.0),
    ("corruption-video", 6140.0, 6160.0, 18.0),
    ("zhuang-meltdown", 6180.0, 6188.0, 38.0),
    ("rap-climax", 6241.0, 6259.0, 46.0),
    ("hu-truth-reveal", 6387.0, 6403.0, 64.0),
    ("anti-layoff-speech", 6486.0, 6496.0, 80.0),
]


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ass_time(seconds):
    centis = int(round(seconds * 100))
    h, rem = divmod(centis, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def srt_time(seconds):
    millis = int(round(seconds * 1000))
    h, rem = divmod(millis, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    audio_paths = []
    for idx, (_, source_in, source_out, _) in enumerate(SEGMENTS, 1):
        path = TMP_DIR / f"{idx:02d}.wav"
        run([
            "ffmpeg", "-y", "-ss", str(source_in), "-i", str(SOURCE),
            "-t", str(source_out - source_in), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(path),
        ])
        audio_paths.append(path)

    concat = TMP_DIR / "concat.wav"
    run([
        "ffmpeg", "-y", *sum((["-i", str(path)] for path in audio_paths), []),
        "-filter_complex", f"concat=n={len(audio_paths)}:v=0:a=1[out]",
        "-map", "[out]", "-c:a", "pcm_s16le", str(concat),
    ])

    try:
        model = WhisperModel("small", device="cuda", compute_type="float16")
        device = "cuda"
    except Exception:
        model = WhisperModel("small", device="cpu", compute_type="int8")
        device = "cpu"
    try:
        segments, info = model.transcribe(
            str(concat), language="zh", beam_size=5, word_timestamps=True,
            vad_filter=True, condition_on_previous_text=False,
        )
        segments = list(segments)
    except Exception:
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        device = "cpu"
        segments, info = model.transcribe(
            str(concat), language="zh", beam_size=5, word_timestamps=True,
            vad_filter=True, condition_on_previous_text=False,
        )
        segments = list(segments)

    cues = []
    offset_ranges = [(timeline, timeline + (source_out - source_in)) for _, source_in, source_out, timeline in SEGMENTS]
    for seg in segments:
        start, end = float(seg.start), float(seg.end)
        text = seg.text.strip()
        if not text:
            continue
        for timeline_start, timeline_end in offset_ranges:
            if start < timeline_end and end > timeline_start:
                start = max(start, timeline_start)
                end = min(end, timeline_end)
                if end > start:
                    cues.append({"start": round(start, 3), "end": round(end, 3), "text": text})
                break

    cues.sort(key=lambda cue: cue["start"])
    (OUT_DIR / "high-energy-transcript.json").write_text(
        json.dumps({"engine": "faster-whisper", "model": "small", "device": device, "language": info.language, "cues": cues}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    srt_lines = []
    for idx, cue in enumerate(cues, 1):
        srt_lines.extend([str(idx), f"{srt_time(cue['start'])} --> {srt_time(cue['end'])}", cue["text"], ""])
    (OUT_DIR / "high-energy-transcript.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    print(json.dumps({"device": device, "language": info.language, "segments": len(cues), "output": str(OUT_DIR)}, ensure_ascii=False))


if __name__ == "__main__":
    main()`r`n