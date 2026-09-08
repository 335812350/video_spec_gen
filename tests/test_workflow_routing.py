import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / ".agents" / "skills" / "video-production-dispatcher" / "references" / "workflow-registry.md"
DISPATCHER = ROOT / ".agents" / "skills" / "video-production-dispatcher" / "SKILL.md"
PERSONAL = ROOT / ".agents" / "skills" / "video-spec-director-dev" / "SKILL.md"
TEMPLATE = ROOT / ".agents" / "skills" / "video-spec-director-dev" / "templates" / "video-spec-template.md"
LAYOUT = ROOT / ".agents" / "skills" / "video-spec-director-dev" / "references" / "project-layout.md"


class WorkflowRoutingTests(unittest.TestCase):
    def test_registry_covers_commentary_high_energy_and_generic_fallback(self):
        registry = REGISTRY.read_text(encoding="utf-8")
        self.assertIn("film-commentary", registry)
        self.assertIn(".agents/skills/movie-master-director/SKILL.md", registry)

        self.assertIn("`high-energy-clip`", registry)
        self.assertIn("`generic-video`", registry)
        self.assertIn(".agents/skills/high-energy-clip/SKILL.md", registry)
        self.assertIn(".agents/skills/high-energy-clip/SKILL.md`（v2）", registry)
        self.assertRegex(registry, r"未注册|未匹配|回退")

    def test_dispatcher_does_not_claim_unregistered_types_are_supported(self):
        dispatcher = DISPATCHER.read_text(encoding="utf-8")

        self.assertIn("workflow_version: \"2\"", dispatcher)

        self.assertRegex(dispatcher, r"未注册.*(?:说明|回退|确认)|(?:说明|回退|确认).*未注册")
        self.assertIn("一条主生产工作流", dispatcher)
        self.assertIn("production_mode", dispatcher)

    def test_dispatcher_routes_explicit_film_commentary_requests(self):
        dispatcher = DISPATCHER.read_text(encoding="utf-8")

        for phrase in ("影视解说", "电影解说", "影评式解说"):
            self.assertIn(phrase, dispatcher)
        self.assertIn("workflow_id: film-commentary", dispatcher)
        self.assertIn("production_mode: script-led", dispatcher)


    def test_personal_workflow_keeps_direct_call_compatibility(self):
        personal = PERSONAL.read_text(encoding="utf-8")

        self.assertIn("第二层", personal)
        self.assertIn("直接调用本 Skill 时保留原有 0-1 / 迭代行为", personal)
        self.assertIn("不重新选择顶层工作流", personal)
        self.assertNotIn("video-types/high-energy-clip.md", personal)

    def test_template_and_layout_define_workflow_identity(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        layout = LAYOUT.read_text(encoding="utf-8")

        for field in ("workflow_id", "workflow_version", "project_slug", "source_film_slug"):
            self.assertIn(field, template)
            self.assertIn(field, layout)
        self.assertIn("video_type", template)
        self.assertIn("production_mode", template)
        self.assertIn("video_type", layout)
        self.assertIn("production_mode", layout)

    def test_current_project_manifest_matches_spec_identity(self):
        manifest_path = ROOT / "projects" / "annual-meeting-high-energy-90s" / "project.json"
        spec_path = manifest_path.parent / "video-spec.md"
        if not manifest_path.exists() or not spec_path.exists():
            self.skipTest("current example project is not checked out")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        spec = spec_path.read_text(encoding="utf-8")

        self.assertEqual(manifest["id"], "annual-meeting-high-energy-90s")
        self.assertEqual(manifest["source_film_slug"], "annual-meeting")
        self.assertEqual(manifest["project_slug"], manifest["id"])
        self.assertEqual(manifest["video_type"], "high-energy-clip")
        self.assertEqual(manifest["production_mode"], "asset-led")
        self.assertIn("workflow_id", manifest)
        self.assertIn("workflow_version", manifest)
        self.assertRegex(spec, r"workflow_id.*high-energy-clip|工作流 ID.*high-energy-clip")
        self.assertRegex(spec, r"workflow_version.*1|工作流版本.*1")


if __name__ == "__main__":
    unittest.main()
