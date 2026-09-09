"""Dependency-free Alibaba Cloud Model Studio TTS client.

The module intentionally uses only the Python standard library.  ``transport``
is injectable so callers can test request construction without network access.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HOST = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com"
DEFAULT_BASE_URL = f"{HOST}/api/v1"
DEFAULT_MODEL = "qwen-audio-3.0-tts-flash"
DEFAULT_SAMPLE_RATE = 24000
MAX_CLONE_AUDIO_BYTES = 10 * 1024 * 1024
_AUDIO_TTS_PATH = "/services/audio/tts/SpeechSynthesizer"
_MULTIMODAL_PATH = "/services/aigc/multimodal-generation/generation"
_CUSTOMIZATION_PATH = "/services/audio/tts/customization"


class ConfigError(RuntimeError):
    """Raised when the local Alibaba configuration is incomplete."""


class AliyunAPIError(RuntimeError):
    """Raised for an unsuccessful Model Studio HTTP response."""


@dataclass(frozen=True, repr=False)
class AliyunConfig:
    api_key: str = field(repr=False)
    base_url: str = DEFAULT_BASE_URL

    def __repr__(self) -> str:
        return f"AliyunConfig(base_url={self.base_url!r}, api_key='***')"


Config = AliyunConfig


_SENSITIVE_FIELD_NAMES = {
    "api_key",
    "apikey",
    "authorization",
    "access_token",
    "token",
    "secret",
    "password",
}


def redact_sensitive(value: Any) -> Any:
    """Return JSON-shaped data with credential-like fields masked."""
    if isinstance(value, Mapping):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in _SENSITIVE_FIELD_NAMES or normalized.endswith("_api_key"):
                redacted[key] = "***"
            else:
                redacted[key] = redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive(item) for item in value]
    return value


def _parse_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[name] = value
    return values


def load_config(
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    dotenv_path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> AliyunConfig:
    """Resolve config in explicit > environment > ``.env.local`` order."""
    env = os.environ if environ is None else environ
    path = Path(dotenv_path) if dotenv_path is not None else Path.cwd() / ".env.local"
    file_values = _parse_dotenv(path)
    resolved_key = api_key or env.get("DASHSCOPE_API_KEY") or file_values.get("DASHSCOPE_API_KEY")
    if not resolved_key or not resolved_key.strip():
        raise ConfigError(
            "DASHSCOPE_API_KEY is required; pass api_key, set the environment variable, "
            f"or add it to {path}"
        )
    resolved_base = base_url or env.get("DASHSCOPE_BASE_URL") or file_values.get(
        "DASHSCOPE_BASE_URL", DEFAULT_BASE_URL
    )
    return AliyunConfig(api_key=resolved_key.strip(), base_url=resolved_base.strip().rstrip("/"))


def endpoint_for_model(model: str, *, base_url: str = DEFAULT_BASE_URL) -> str:
    """Return the DashScope-native endpoint for a supported TTS model family."""
    normalized = model.strip().lower()
    if normalized.startswith(("qwen-audio-", "cosyvoice-")):
        path = _AUDIO_TTS_PATH
    elif normalized.startswith(("qwen3-tts-", "qwen-tts")):
        path = _MULTIMODAL_PATH
    else:
        raise ValueError(
            f"unsupported TTS model {model!r}; use a qwen-audio, cosyvoice, or qwen3-tts model"
        )
    return f"{base_url.rstrip('/')}{path}"


class UrllibTransport:
    """Default stdlib HTTP transport; replace it with a fake in offline tests."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: Mapping[str, Any] | None = None,
        timeout: float = 60,
    ):
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = Request(url, data=encoded, headers=dict(headers), method=method)
        return urlopen(request, timeout=timeout)


def _response_status(response: Any) -> int:
    status = getattr(response, "status", None)
    if status is None and hasattr(response, "getcode"):
        status = response.getcode()
    return int(status or 200)


def _read_response(response: Any) -> bytes:
    try:
        return response.read()
    finally:
        close = getattr(response, "close", None)
        if close:
            close()


def _deep_merge(base: dict[str, Any], extra: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in extra.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _decode_audio_data(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("Alibaba TTS returned invalid base64 audio data") from exc


def _audio_from_payload(payload: Mapping[str, Any]) -> tuple[bytes | None, str | None]:
    output = payload.get("output") or {}
    audio = output.get("audio") or {}
    if not isinstance(audio, Mapping):
        audio = {}
    data = audio.get("data")
    url = audio.get("url") or output.get("audio_url")
    return (_decode_audio_data(data) if data else None), (str(url) if url else None)


def _iter_sse_events(response: Any) -> Iterable[dict[str, Any]]:
    if hasattr(response, "iter_lines"):
        lines = response.iter_lines()
    elif hasattr(response, "readline"):
        def read_lines():
            while True:
                line = response.readline()
                if not line:
                    break
                yield line
        lines = read_lines()
    else:
        lines = _read_response(response).splitlines()
    for raw_line in lines:
        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8", errors="replace")
        else:
            line = str(raw_line)
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Alibaba TTS returned malformed SSE data") from exc
        if isinstance(event, Mapping) and event.get("error"):
            raise RuntimeError("Alibaba TTS stream returned an error")
        if isinstance(event, dict):
            yield event


def _audio_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
    }.get(suffix, mimetypes.types_map.get(suffix, "application/octet-stream"))


def _validate_audio_header(path: Path) -> None:
    """Reject files whose container signature does not match their extension."""
    header = path.read_bytes()[:16]
    suffix = path.suffix.lower()
    valid = {
        ".wav": len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE",
        ".mp3": header[:3] == b"ID3" or (len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0),
        ".m4a": len(header) >= 8 and header[4:8] == b"ftyp",
        ".flac": header[:4] == b"fLaC",
        ".ogg": header[:4] == b"OggS",
    }
    if not valid.get(suffix, False):
        raise ValueError(f"audio file header does not match {suffix} format: {path}")


def _validate_audio_quality(path: Path) -> None:
    """Use ffprobe when available to reject empty or non-audio containers."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,sample_rate,channels,duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=8,
        )
    except FileNotFoundError:
        return
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"audio quality validation failed for {path}") from exc
    try:
        streams = json.loads(result.stdout).get("streams", [])
    except (AttributeError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"audio quality validation returned invalid data for {path}") from exc
    if not isinstance(streams, list):
        raise ValueError(f"audio quality metadata has no stream list: {path}")
    audio_streams = [
        stream for stream in streams
        if isinstance(stream, Mapping) and stream.get("codec_type") == "audio"
    ]
    if not audio_streams:
        raise ValueError(f"audio file contains no audio stream: {path}")
    stream = audio_streams[0]
    try:
        duration = float(stream.get("duration") or 0)
        sample_rate = int(stream.get("sample_rate") or 0)
        channels = int(stream.get("channels") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"audio quality metadata is invalid: {path}") from exc
    if duration <= 0 or sample_rate <= 0 or channels <= 0:
        raise ValueError(
            f"audio quality must include positive duration, sample rate, and channel count: {path}"
        )


class AliyunTTSClient:
    """Client for HTTP/SSE TTS, model and custom voice APIs."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        dotenv_path: str | Path | None = None,
        config: AliyunConfig | None = None,
        transport: Any | None = None,
        timeout: float = 120,
    ):
        if config is not None and any(value is not None for value in (api_key, base_url, dotenv_path)):
            raise ValueError("pass config or api_key/base_url/dotenv_path, not both")
        self.config = config or load_config(
            api_key=api_key, base_url=base_url, dotenv_path=dotenv_path
        )
        self.transport = transport or UrllibTransport()
        self.timeout = timeout

    def _request(
        self,
        method: str,
        url: str,
        *,
        body: Mapping[str, Any] | None = None,
        stream: bool = False,
        authenticated: bool = True,
    ) -> Any:
        headers: dict[str, str] = {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if authenticated:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        if stream:
            headers.update({"X-DashScope-SSE": "enable", "Accept": "text/event-stream"})
        response = self.transport.request(
            method, url, headers=headers, body=body, timeout=self.timeout
        )
        status = _response_status(response)
        if status < 200 or status >= 300:
            close = getattr(response, "close", None)
            if close:
                close()
            raise AliyunAPIError(f"Alibaba Model Studio request failed (HTTP {status})")
        return response

    def synthesize(
        self,
        *,
        text: str,
        voice: str,
        out: str | Path,
        model: str = DEFAULT_MODEL,
        format: str = "mp3",
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        stream: bool = False,
        language_type: str | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> Path:
        if not voice or not voice.strip():
            raise ValueError("voice is required; system or custom voice ID must be explicit")
        if not text or not text.strip():
            raise ValueError("text is required")
        audio_format = format.lower()
        if audio_format not in {"mp3", "wav"}:
            raise ValueError("format must be mp3 or wav")
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        endpoint = endpoint_for_model(model, base_url=self.config.base_url)
        is_qwen3 = endpoint.endswith(_MULTIMODAL_PATH)
        if is_qwen3:
            body: dict[str, Any] = {
                "model": model,
                "input": {"text": text, "voice": voice},
                "parameters": {"format": audio_format, "sample_rate": sample_rate},
                "stream": bool(stream),
            }
            if language_type:
                body["input"]["language_type"] = language_type
        else:
            body = {
                "model": model,
                "input": {
                    "text": text,
                    "voice": voice,
                    "format": audio_format,
                    "sample_rate": sample_rate,
                },
            }
            if language_type:
                body["input"]["language_type"] = language_type
        if extra is not None:
            if not isinstance(extra, Mapping):
                raise ValueError("extra must be a JSON object")
            _deep_merge(body, extra)
            if not isinstance(body.get("input"), dict):
                raise ValueError("--extra-json input must be a JSON object")
            # Stable CLI parameters remain authoritative over pass-through JSON.
            body["model"] = model
            body["input"]["text"] = text
            body["input"]["voice"] = voice
            if is_qwen3:
                if not isinstance(body.get("parameters"), dict):
                    raise ValueError("--extra-json parameters must be a JSON object")
                body.setdefault("parameters", {})["format"] = audio_format
                body["parameters"]["sample_rate"] = sample_rate
            else:
                body["input"]["format"] = audio_format
                body["input"]["sample_rate"] = sample_rate
        response = self._request("POST", endpoint, body=body, stream=stream)
        chunks: list[bytes] = []
        audio_url: str | None = None
        if stream:
            try:
                for event in _iter_sse_events(response):
                    chunk, url = _audio_from_payload(event)
                    if chunk:
                        chunks.append(chunk)
                    audio_url = audio_url or url
            finally:
                close = getattr(response, "close", None)
                if close:
                    close()
        else:
            payload_bytes = _read_response(response)
            try:
                payload = json.loads(payload_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("Alibaba TTS returned an invalid JSON response") from exc
            chunk, audio_url = _audio_from_payload(payload)
            if chunk:
                chunks.append(chunk)
        if not chunks and audio_url:
            audio_response = self._request("GET", audio_url, authenticated=False)
            chunks.append(_read_response(audio_response))
        if not chunks:
            raise RuntimeError("Alibaba TTS response contained no audio data or URL")
        output = Path(out)
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                for chunk in chunks:
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, output)
        except BaseException:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
        return output

    def _get_json(self, path: str, *, query: Mapping[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urlencode(query, doseq=True)}"
        response = self._request("GET", url)
        raw = _read_response(response)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Alibaba API returned invalid JSON") from exc

    def _get_collection(
        self, path: str, *, row_key: str, query: Mapping[str, Any], page_size: int = 200
    ) -> dict[str, Any]:
        page = 1
        combined: list[Any] = []
        last: dict[str, Any] = {}
        while True:
            payload = self._get_json(
                path, query={**query, "page_no": page, "page_size": page_size}
            )
            last = payload
            output = payload.get("output") or {}
            rows = output.get(row_key) or []
            combined.extend(rows)
            total = output.get("total")
            if not rows or (total is None and len(rows) < page_size) or (
                total is not None and len(combined) >= int(total)
            ):
                output = dict(output)
                output[row_key] = combined
                output["total"] = int(total) if total is not None else len(combined)
                last["output"] = output
                return last
            page += 1

    def models(self, *, page_size: int = 200) -> dict[str, Any]:
        return {
            "catalog": self._get_collection(
                "/models", row_key="models", query={"supports": "inference"}, page_size=page_size
            ),
            "permissions": self._get_collection(
                "/models/permissions",
                row_key="permissions",
                query={"authorization_scope": "AUTHORIZED", "action": "INFERENCE"},
                page_size=min(page_size, 200),
            ),
        }

    def voices(
        self,
        *,
        model: str = "voice-enrollment",
        target_model: str | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        action = "list" if model == "qwen-voice-enrollment" else "list_voice"
        input_body: dict[str, Any] = {"action": action}
        if target_model:
            input_body["target_model"] = target_model
        body: dict[str, Any] = {"model": model, "input": input_body}
        if extra:
            if not isinstance(extra, Mapping):
                raise ValueError("extra must be a JSON object")
            _deep_merge(body, extra)
            if not isinstance(body.get("input"), dict):
                raise ValueError("--extra-json input must be a JSON object")
            body["model"] = model
            body["input"]["action"] = action
        response = self._request(
            "POST", f"{self.config.base_url.rstrip('/')}{_CUSTOMIZATION_PATH}", body=body
        )
        raw = _read_response(response)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Alibaba voice API returned invalid JSON") from exc

    def clone(
        self,
        *,
        target_model: str,
        prefix: str,
        audio_url: str | None = None,
        audio: str | Path | None = None,
        language_hints: list[str] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if bool(audio_url) == (audio is not None):
            raise ValueError("provide exactly one of audio-url or audio")
        endpoint_for_model(target_model, base_url=self.config.base_url)
        normalized = target_model.lower()
        if not prefix or not prefix.strip():
            raise ValueError("prefix is required")
        if audio_url and not normalized.startswith(("qwen-audio-", "cosyvoice-")):
            raise ValueError("audio-url cloning is supported for Qwen-Audio/CosyVoice models")
        if audio is not None and not normalized.startswith(("qwen3-tts-", "qwen-tts")):
            raise ValueError(
                "local audio cloning is only supported for Qwen-TTS; use audio-url for Qwen-Audio/CosyVoice"
            )
        body: dict[str, Any]
        if audio_url:
            body = {
                "model": "voice-enrollment",
                "input": {
                    "action": "create_voice",
                    "target_model": target_model,
                    "prefix": prefix,
                    "url": audio_url,
                },
            }
        else:
            audio_path = Path(audio)  # type: ignore[arg-type]
            if not audio_path.is_file():
                raise ValueError(f"audio file does not exist: {audio_path}")
            size = audio_path.stat().st_size
            if size == 0:
                raise ValueError("audio file must not be empty")
            if size > MAX_CLONE_AUDIO_BYTES:
                raise ValueError("local audio file must be no larger than 10 MB")
            suffix = audio_path.suffix.lower()
            if suffix not in {".wav", ".mp3", ".m4a", ".flac", ".ogg"}:
                raise ValueError("local audio must have a wav, mp3, m4a, flac, or ogg extension")
            _validate_audio_header(audio_path)
            _validate_audio_quality(audio_path)
            encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
            body = {
                "model": "qwen-voice-enrollment",
                "input": {
                    "action": "create",
                    "target_model": target_model,
                    "preferred_name": prefix,
                    "audio": {"data": f"data:{_audio_mime(audio_path)};base64,{encoded}"},
                },
            }
        action = "create_voice" if audio_url else "create"
        if language_hints:
            body["input"]["language_hints"] = list(language_hints)
        if extra:
            if not isinstance(extra, Mapping):
                raise ValueError("extra must be a JSON object")
            _deep_merge(body, extra)
            if not isinstance(body.get("input"), dict):
                raise ValueError("--extra-json input must be a JSON object")
            body["input"]["action"] = action
            body["input"]["target_model"] = target_model
            if audio_url:
                body["input"]["prefix"] = prefix
            else:
                body["input"]["preferred_name"] = prefix
        response = self._request(
            "POST", f"{self.config.base_url.rstrip('/')}{_CUSTOMIZATION_PATH}", body=body
        )
        raw = _read_response(response)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Alibaba voice enrollment API returned invalid JSON") from exc


def _wrapper_client(kwargs: dict[str, Any]) -> AliyunTTSClient:
    client = kwargs.pop("client", None)
    if client is not None:
        return client
    return AliyunTTSClient(
        api_key=kwargs.pop("api_key", None),
        base_url=kwargs.pop("base_url", None),
        dotenv_path=kwargs.pop("dotenv_path", None),
        config=kwargs.pop("config", None),
        transport=kwargs.pop("transport", None),
    )


def synthesize(**kwargs: Any) -> Path:
    client = _wrapper_client(kwargs)
    return client.synthesize(**kwargs)


def models(**kwargs: Any) -> dict[str, Any]:
    client = _wrapper_client(kwargs)
    return client.models(**kwargs)


def voices(**kwargs: Any) -> dict[str, Any]:
    client = _wrapper_client(kwargs)
    return client.voices(**kwargs)


def clone(**kwargs: Any) -> dict[str, Any]:
    client = _wrapper_client(kwargs)
    return client.clone(**kwargs)


def _json_arg(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--extra-json must be valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--extra-json must contain a JSON object")
    return parsed


def _client_from_args(args: argparse.Namespace) -> AliyunTTSClient:
    return AliyunTTSClient(api_key=args.api_key, base_url=args.base_url, dotenv_path=args.dotenv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alibaba Cloud Model Studio TTS tools")
    parser.add_argument("--api-key", help=argparse.SUPPRESS)
    parser.add_argument("--base-url", help=argparse.SUPPRESS)
    parser.add_argument("--dotenv", type=Path, help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_config_options(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--api-key", help=argparse.SUPPRESS, default=argparse.SUPPRESS)
        command_parser.add_argument("--base-url", help=argparse.SUPPRESS, default=argparse.SUPPRESS)
        command_parser.add_argument("--dotenv", type=Path, help=argparse.SUPPRESS, default=argparse.SUPPRESS)

    synth = subparsers.add_parser("synthesize", help="synthesize text to an audio file")
    add_config_options(synth)
    synth.add_argument("--model", default=DEFAULT_MODEL)
    synth.add_argument("--voice", required=True)
    source = synth.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--script", type=Path)
    synth.add_argument("--out", type=Path, required=True)
    synth.add_argument("--format", choices=("mp3", "wav"), default="mp3")
    synth.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    synth.add_argument("--stream", action="store_true")
    synth.add_argument("--language-type")
    synth.add_argument("--extra-json")

    models_parser = subparsers.add_parser("models", help="list catalog and workspace permissions")
    add_config_options(models_parser)
    voice = subparsers.add_parser("voices", help="list custom voices")
    add_config_options(voice)
    voice.add_argument("--model", default="voice-enrollment")
    voice.add_argument("--target-model")
    voice.add_argument("--extra-json")

    enrollment = subparsers.add_parser("clone", help="enroll a custom voice")
    add_config_options(enrollment)
    enrollment.add_argument("--target-model", required=True)
    enrollment.add_argument("--prefix", required=True)
    audio_source = enrollment.add_mutually_exclusive_group(required=True)
    audio_source.add_argument("--audio-url")
    audio_source.add_argument("--audio", type=Path)
    enrollment.add_argument("--language-hints", nargs="*")
    enrollment.add_argument("--extra-json")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        client = _client_from_args(args)
        if args.command == "synthesize":
            text = args.text if args.text is not None else args.script.read_text(encoding="utf-8")
            result: Any = str(client.synthesize(
                text=text, voice=args.voice, out=args.out, model=args.model,
                format=args.format, sample_rate=args.sample_rate, stream=args.stream,
                language_type=args.language_type, extra=_json_arg(args.extra_json)))
        elif args.command == "models":
            result = client.models()
        elif args.command == "voices":
            result = client.voices(model=args.model, target_model=args.target_model,
                                   extra=_json_arg(args.extra_json))
        else:
            result = client.clone(target_model=args.target_model, prefix=args.prefix,
                                  audio_url=args.audio_url, audio=args.audio,
                                  language_hints=args.language_hints,
                                  extra=_json_arg(args.extra_json))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ConfigError, AliyunAPIError, ValueError, OSError, RuntimeError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
