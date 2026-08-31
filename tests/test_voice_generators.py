import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_script(relative_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    def synthesize(self, **kwargs):
        self.calls.append(kwargs)
        output = Path(kwargs["out"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"ID3")
        return output


class VoiceGeneratorTests(unittest.TestCase):
    def test_tv_generator_uses_aliyun_and_writes_manifest(self):
        module = load_script("tools/generate_tv_voice.py", "generate_tv_voice")
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            with patch.object(module, "AliyunTTSClient", FakeClient):
                manifest = module.generate_all(
                    out_dir=output_dir,
                    model="qwen-audio-3.0-tts-flash",
                    voice="demo-voice",
                    sample_rate=24000,
                    extra={"volume": 60, "api_key": "should-not-leak"},
                )
            self.assertEqual(manifest["provider"], "aliyun-dashscope")
            self.assertEqual(manifest["voice"], "demo-voice")
            self.assertEqual(len(manifest["clips"]), 3)
            self.assertEqual(manifest["parameters"]["sample_rate"], 24000)
            self.assertEqual(manifest["clips"][0]["duration_s"], 30.0)
            self.assertNotIn("should-not-leak", json.dumps(manifest))
            saved = json.loads((output_dir / "voiceover-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["model"], "qwen-audio-3.0-tts-flash")
            self.assertTrue((output_dir / "guide-intro.srt").is_file())

    def test_commentary_generator_extracts_and_writes_aliyun_manifest(self):
        module = load_script(
            "projects/annual-meeting-commentary/tools/generate_aliyun_voiceover.py",
            "generate_aliyun_voiceover",
        )
        markdown = "## 旁白逐字稿草案\n### 01:00–02:00 · 第一章\n\n这是一句旁白。\n## 素材状态与核验要求\n"
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            script = output_dir / "edit-plan.md"
            script.write_text(markdown, encoding="utf-8")
            with patch.object(module, "AliyunTTSClient", FakeClient):
                manifest = module.generate_voiceover(
                    script=script,
                    out_dir=output_dir / "voiceover",
                    model="qwen-audio-3.0-tts-flash",
                    voice="demo-voice",
                    extra={"authorization": "should-not-leak"},
                )
            self.assertEqual(manifest["provider"], "aliyun-dashscope")
            self.assertEqual(manifest["chapters"][0]["voice"], "demo-voice")
            self.assertEqual(manifest["parameters"]["fallback_duration"], 30.0)
            self.assertNotIn("should-not-leak", json.dumps(manifest))
            self.assertTrue((output_dir / "voiceover" / "01-第一章.srt").is_file())

    def test_historical_commentary_entrypoint_reexports_aliyun_flow(self):
        module = load_script(
            "projects/annual-meeting-commentary/tools/generate_edge_voiceover.py",
            "generate_edge_voiceover_compat",
        )
        self.assertTrue(callable(module.generate_voiceover))
        source = (ROOT / "projects/annual-meeting-commentary/tools/generate_edge_voiceover.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("edge_tts", source)


if __name__ == "__main__":
    unittest.main()
