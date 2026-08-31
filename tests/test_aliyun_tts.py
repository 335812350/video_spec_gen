import base64
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.aliyun_tts import (
    AliyunTTSClient,
    ConfigError,
    DEFAULT_BASE_URL,
    endpoint_for_model,
    load_config,
)


class FakeResponse:
    def __init__(self, payload=None, *, content=b"", sse_lines=None, status=200):
        self.status = status
        self._payload = payload
        self._content = content
        self._sse_lines = sse_lines

    def read(self):
        if self._payload is not None:
            return json.dumps(self._payload).encode("utf-8")
        return self._content

    def iter_lines(self):
        return iter(self._sse_lines or ())

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, *, headers, body=None, timeout=60):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body})
        return self.responses.pop(0)


class AliyunTTSTests(unittest.TestCase):
    def client(self, transport):
        return AliyunTTSClient(api_key="explicit-secret", transport=transport)

    def test_load_config_uses_explicit_key_then_environment_then_dotenv(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env.local"
            env_file.write_text(
                "DASHSCOPE_API_KEY=file-secret\nDASHSCOPE_BASE_URL=https://file.example/api/v1\n",
                encoding="utf-8",
            )
            with patch.dict("os.environ", {
                "DASHSCOPE_API_KEY": "environment-secret",
                "DASHSCOPE_BASE_URL": "https://environment.example/api/v1",
            }, clear=False):
                config = load_config(api_key="explicit-secret", dotenv_path=env_file)
                self.assertEqual(config.api_key, "explicit-secret")
                self.assertEqual(config.base_url, "https://environment.example/api/v1")
            with patch.dict("os.environ", {}, clear=True):
                config = load_config(dotenv_path=env_file)
                self.assertEqual(config.api_key, "file-secret")
                self.assertEqual(config.base_url, "https://file.example/api/v1")

    def test_load_config_uses_documented_default_base_url(self):
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / ".env.local"
            config_file.write_text("DASHSCOPE_API_KEY=from-file\n", encoding="utf-8")
            with patch.dict("os.environ", {}, clear=True):
                self.assertEqual(load_config(dotenv_path=config_file).base_url, DEFAULT_BASE_URL)

    def test_missing_api_key_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ConfigError, "DASHSCOPE_API_KEY"):
                load_config(dotenv_path=Path(directory) / "missing.env")

    def test_model_routing_uses_model_family_endpoints(self):
        self.assertTrue(endpoint_for_model("qwen-audio-3.0-tts-flash").endswith(
            "/services/audio/tts/SpeechSynthesizer"))
        self.assertTrue(endpoint_for_model("cosyvoice-v3-flash").endswith(
            "/services/audio/tts/SpeechSynthesizer"))
        self.assertTrue(endpoint_for_model("qwen3-tts-flash").endswith(
            "/services/aigc/multimodal-generation/generation"))
        with self.assertRaisesRegex(ValueError, "unsupported"):
            endpoint_for_model("qwen-plus")

    def test_synthesize_downloads_url_and_writes_atomically(self):
        transport = FakeTransport([
            FakeResponse({"output": {"audio": {"url": "https://audio.example/result.mp3"}}}),
            FakeResponse(content=b"ID3-VOICE"),
        ])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "voice.mp3"
            result = self.client(transport).synthesize(
                text="你好", voice="longanhuan_v3.6", out=output,
                model="qwen-audio-3.0-tts-flash", format="mp3", sample_rate=24000)
            self.assertEqual(result, output)
            self.assertEqual(output.read_bytes(), b"ID3-VOICE")
            self.assertEqual(transport.calls[0]["method"], "POST")
            self.assertTrue(transport.calls[0]["url"].endswith(
                "/services/audio/tts/SpeechSynthesizer"))
            self.assertEqual(transport.calls[0]["headers"]["Authorization"],
                             "Bearer explicit-secret")
            self.assertEqual(transport.calls[0]["body"]["input"], {
                "text": "你好", "voice": "longanhuan_v3.6", "format": "mp3",
                "sample_rate": 24000})

    def test_synthesize_stream_decodes_sse_audio_data(self):
        first = base64.b64encode(b"ID3-").decode()
        second = base64.b64encode(b"STREAM").decode()
        transport = FakeTransport([FakeResponse(sse_lines=[
            f"data: {json.dumps({'output': {'audio': {'data': first}}})}".encode(),
            b"",
            f"data: {json.dumps({'output': {'audio': {'data': second}}})}".encode()])])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "stream.mp3"
            self.client(transport).synthesize(
                text="流式", voice="longanhuan_v3.6", out=output, stream=True)
            self.assertEqual(output.read_bytes(), b"ID3-STREAM")
            self.assertEqual(transport.calls[0]["headers"]["X-DashScope-SSE"], "enable")

    def test_qwen3_tts_uses_multimodal_payload_and_extra_json(self):
        raw = base64.b64encode(b"WAVE").decode()
        transport = FakeTransport([FakeResponse({"output": {"audio": {"data": raw}}})])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "voice.wav"
            self.client(transport).synthesize(
                text="你好", voice="Cherry", out=output, model="qwen3-tts-flash",
                format="wav", sample_rate=16000, language_type="Chinese",
                extra={"parameters": {"volume": 60}})
            call = transport.calls[0]
            self.assertTrue(call["url"].endswith(
                "/services/aigc/multimodal-generation/generation"))
            self.assertEqual(call["body"]["input"], {
                "text": "你好", "voice": "Cherry", "language_type": "Chinese"})
            self.assertEqual(call["body"]["parameters"], {
                "format": "wav", "sample_rate": 16000, "volume": 60})
            self.assertEqual(output.read_bytes(), b"WAVE")

    def test_voice_is_required_and_format_is_restricted(self):
        api = self.client(FakeTransport([]))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "voice is required"):
                api.synthesize(text="text", voice="", out=Path(directory) / "a.mp3")
            with self.assertRaisesRegex(ValueError, "mp3 or wav"):
                api.synthesize(text="text", voice="voice", out=Path(directory) / "a.ogg",
                                format="ogg")

    def test_extra_json_nested_objects_are_validated(self):
        api = self.client(FakeTransport([]))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "parameters must be a JSON object"):
                api.synthesize(
                    text="text", voice="voice", out=Path(directory) / "a.mp3",
                    model="qwen3-tts-flash", extra={"parameters": None})
            with self.assertRaisesRegex(ValueError, "input must be a JSON object"):
                api.synthesize(
                    text="text", voice="voice", out=Path(directory) / "b.mp3",
                    extra={"input": []})

    def test_models_queries_catalog_and_permissions_without_leaking_key(self):
        transport = FakeTransport([
            FakeResponse({"output": {"models": [{"model": "qwen3-tts-flash"}], "total": 1}}),
            FakeResponse({"output": {"permissions": [{"model": "qwen3-tts-flash"}], "total": 1}})])
        result = self.client(transport).models()
        self.assertEqual(result["catalog"]["output"]["models"][0]["model"], "qwen3-tts-flash")
        self.assertEqual(result["permissions"]["output"]["permissions"][0]["model"],
                         "qwen3-tts-flash")
        self.assertNotIn("explicit-secret", json.dumps(result))
        self.assertTrue(all("explicit-secret" not in call["url"] for call in transport.calls))
        self.assertTrue(all("models" in call["url"] for call in transport.calls))

    def test_voices_uses_customization_list_action(self):
        transport = FakeTransport([FakeResponse({"output": {"voices": [{"voice_id": "demo"}]}})])
        result = self.client(transport).voices(model="voice-enrollment")
        self.assertEqual(result["output"]["voices"][0]["voice_id"], "demo")
        body = transport.calls[0]["body"]
        self.assertEqual(body["model"], "voice-enrollment")
        self.assertEqual(body["input"]["action"], "list_voice")

    def test_clone_rejects_local_qwen_audio_and_large_files(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "sample.wav"
            audio.write_bytes(b"audio")
            api = self.client(FakeTransport([]))
            with self.assertRaisesRegex(ValueError, "audio-url"):
                api.clone(audio=audio, target_model="qwen-audio-3.0-tts-flash", prefix="demo")
            large = Path(directory) / "large.wav"
            with large.open("wb") as handle:
                handle.truncate(10 * 1024 * 1024 + 1)
            with self.assertRaisesRegex(ValueError, "10 MB"):
                api.clone(audio=large, target_model="qwen3-tts-flash", prefix="demo")

    def test_clone_rejects_local_audio_with_invalid_header(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "sample.wav"
            audio.write_bytes(b"not-a-wav")
            with self.assertRaisesRegex(ValueError, "header"):
                self.client(FakeTransport([])).clone(
                    audio=audio, target_model="qwen3-tts-flash", prefix="demo"
                )

    def test_clone_runs_optional_ffprobe_quality_validation(self):
        transport = FakeTransport([FakeResponse({"output": {"voice_id": "demo_voice"}})])
        with tempfile.TemporaryDirectory() as directory, patch(
            "tools.aliyun_tts.subprocess.run",
            return_value=SimpleNamespace(
                stdout='{"streams":[{"codec_type":"audio","duration":"1.2","sample_rate":"24000","channels":1}]}'
            ),
        ) as probe:
            audio = Path(directory) / "sample.wav"
            audio.write_bytes(b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 56)
            self.client(transport).clone(audio=audio, target_model="qwen3-tts-flash", prefix="demo")
            probe.assert_called_once()

    def test_clone_qwen_tts_local_audio_uses_data_uri_and_target_model(self):
        transport = FakeTransport([FakeResponse({"output": {"voice_id": "demo_voice"}})])
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "sample.wav"
            audio.write_bytes(b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 56)
            result = self.client(transport).clone(
                audio=audio, target_model="qwen3-tts-flash", prefix="demo")
            self.assertEqual(result["output"]["voice_id"], "demo_voice")
            body = transport.calls[0]["body"]
            self.assertEqual(body["model"], "qwen-voice-enrollment")
            self.assertEqual(body["input"]["action"], "create")
            self.assertEqual(body["input"]["target_model"], "qwen3-tts-flash")
            self.assertEqual(body["input"]["preferred_name"], "demo")
            self.assertNotIn("prefix", body["input"])
            self.assertTrue(body["input"]["audio"]["data"].startswith("data:audio/wav;base64,"))

    def test_audio_url_download_does_not_forward_api_key(self):
        transport = FakeTransport([
            FakeResponse({"output": {"audio": {"url": "https://audio.example/result.mp3"}}}),
            FakeResponse(content=b"ID3-VOICE"),
        ])
        with tempfile.TemporaryDirectory() as directory:
            self.client(transport).synthesize(
                text="你好", voice="demo", out=Path(directory) / "voice.mp3")
        self.assertEqual(transport.calls[1]["method"], "GET")
        self.assertNotIn("Authorization", transport.calls[1]["headers"])
        self.assertNotIn("Content-Type", transport.calls[1]["headers"])

    def test_clone_url_uses_voice_enrollment_model_and_url(self):
        transport = FakeTransport([FakeResponse({"output": {"voice_id": "demo_voice"}})])
        result = self.client(transport).clone(
            audio_url="https://audio.example/reference.wav",
            target_model="cosyvoice-v3-flash", prefix="demo")
        self.assertEqual(result["output"]["voice_id"], "demo_voice")
        body = transport.calls[0]["body"]
        self.assertEqual(body["model"], "voice-enrollment")
        self.assertEqual(body["input"]["action"], "create_voice")
        self.assertEqual(body["input"]["url"], "https://audio.example/reference.wav")

    def test_clone_requires_exactly_one_audio_source(self):
        api = self.client(FakeTransport([]))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            api.clone(target_model="qwen3-tts-flash", prefix="demo")


if __name__ == "__main__":
    unittest.main()
