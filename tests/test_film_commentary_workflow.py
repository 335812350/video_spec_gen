import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
DOC = ROOT / "docs" / "film-commentary-workflow.md"
STATE_TEMPLATE = SKILLS_ROOT / "movie-master-director" / "templates" / "state.json"

CORE_SKILLS = (
    "movie-master-director",
    "movie-index",
    "movie-first-person-writer",
    "movie-voice-tts",
    "movie-direct",
    "movie-render-qa",
    "movie-second-review",
)


class FilmCommentaryWorkflowTests(unittest.TestCase):
    def test_core_skills_are_present_and_use_current_project_contract(self):
        for skill in CORE_SKILLS:
            path = SKILLS_ROOT / skill / "SKILL.md"
            self.assertTrue(path.is_file(), f"missing {path}")

        master = (SKILLS_ROOT / "movie-master-director" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_id: film-commentary", master)
        self.assertIn("projects/<project-slug>/edit-plan.md", master)
        self.assertIn("projects/<project-slug>/video-spec.md", master)
        self.assertIn("outputs/<project-slug>/render-vNNN.mp4", master)
        self.assertIn("DIRECTING", master)
        self.assertIn("SPEC_READY", master)
        self.assertIn("SPEC_CHECKED", master)
        self.assertNotIn("-> SAMPLE_READY", master)

    def test_movie_direct_requires_formal_scene_level_spec(self):
        direct = (SKILLS_ROOT / "movie-direct" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("不包含探索模式分支", direct)
        self.assertIn("每个正式 Scene 必须记录", direct)
        self.assertIn("剧情阶段的摘要表", direct)
        self.assertIn("8 个或少量连续 HyperFrames clip", direct)
        self.assertIn("正式 video-spec.md", direct)

    def test_film_commentary_overlay_rules_protect_the_film(self):
        master = (SKILLS_ROOT / "movie-master-director" / "SKILL.md").read_text(encoding="utf-8")
        direct = (SKILLS_ROOT / "movie-direct" / "SKILL.md").read_text(encoding="utf-8")
        captions = (SKILLS_ROOT / "captions-overlay" / "SKILL.md").read_text(encoding="utf-8")
        rail = (SKILLS_ROOT / "embedded-captions" / "references" / "rail.md").read_text(encoding="utf-8")
        render_qa = (SKILLS_ROOT / "movie-render-qa" / "SKILL.md").read_text(encoding="utf-8")

        for text in (master, captions, rail, render_qa):
            self.assertIn("text-shadow", text)
            self.assertIn("box-shadow", text)

        self.assertIn("阴影", direct)
        self.assertIn("模糊", direct)

        self.assertIn("rgba(...)", captions)
        self.assertIn("1--2px glyph stroke", captions)
        self.assertIn("影片覆盖层静态与视觉检查", render_qa)
        self.assertIn("Motion is minimal", rail)

    def test_render_qa_has_pre_render_blocking_gate(self):
        render_qa = (SKILLS_ROOT / "movie-render-qa" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("渲染前规格预检", render_qa)
        self.assertIn("Pre-render: PASS", render_qa)
        self.assertIn("Pre-render: BLOCKED", render_qa)
        self.assertIn("不得运行 HyperFrames render", render_qa)
        self.assertIn("standard 全片预览", DOC.read_text(encoding="utf-8"))

    def test_voice_skill_uses_aliyun_and_existing_transcription(self):
        voice = (SKILLS_ROOT / "movie-voice-tts" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("tools/aliyun_tts.py", voice)
        self.assertIn("npx hyperframes transcribe", voice)
        for unsupported_provider in ("Fish Audio", "MiniMax", "Volc", "Edge TTS"):
            self.assertNotIn(unsupported_provider, voice)

    def test_state_template_is_lightweight_and_has_no_hash_contract(self):
        state = json.loads(STATE_TEMPLATE.read_text(encoding="utf-8"))

        self.assertEqual(state["workflow_id"], "film-commentary")
        self.assertEqual(state["workflow_version"], "1")
        self.assertIn("current_stage", state)
        self.assertIn("next_action", state)
        self.assertIn("confirmed", state)
        self.assertNotIn("sha256", json.dumps(state).lower())

    def test_workflow_document_records_source_and_excluded_contracts(self):
        text = DOC.read_text(encoding="utf-8")

        self.assertIn("Apache License 2.0", text)
        self.assertIn("3d50c1745ef2bc37a86919c5492603cdc22e49bb", text)
        self.assertIn("不生成 `visual_edit.json`", text)
        self.assertIn("不建立全局 schema", text)


if __name__ == "__main__":
    unittest.main()
