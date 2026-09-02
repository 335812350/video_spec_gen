import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.high_energy_analyzer import (
    build_candidate_windows,
    detect_scene_boundaries,
    extract_audio_bins,
    load_transcript,
    AnalysisError,
    analyze_file,
    build_parser,
    probe_media,
    score_features,
    validate_selection,
)


class HighEnergyAnalyzerTests(unittest.TestCase):
    def test_score_features_prefers_combined_visual_and_audio_signals(self):
        explosive = score_features(
            {
                "cut_density": 0.9,
                "audio_peak": 0.9,
                "visual_change": 0.8,
                "dialogue_signal": 0.2,
            }
        )
        loud_only = score_features(
            {
                "cut_density": 0.1,
                "audio_peak": 1.0,
                "visual_change": 0.0,
                "dialogue_signal": 0.0,
            }
        )

        self.assertGreater(explosive, loud_only)
        self.assertGreaterEqual(explosive, 0.0)
        self.assertLessEqual(explosive, 100.0)

    def test_build_candidate_windows_returns_contiguous_ranked_candidates(self):
        shots = [
            {"id": "shot-001", "source_in": 0.0, "source_out": 1.0, "score": 20.0},
            {"id": "shot-002", "source_in": 1.0, "source_out": 2.0, "score": 95.0},
            {"id": "shot-003", "source_in": 2.0, "source_out": 3.0, "score": 90.0},
            {"id": "shot-004", "source_in": 3.0, "source_out": 4.0, "score": 30.0},
        ]

        candidates = build_candidate_windows(shots, target_duration_s=2.0, max_candidates=2)

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["source_segments"], ["shot-002", "shot-003"])
        self.assertEqual(candidates[0]["source_in"], 1.0)
        self.assertEqual(candidates[0]["source_out"], 3.0)
        self.assertEqual(candidates[0]["estimated_duration_s"], 2.0)
        self.assertGreaterEqual(candidates[0]["energy_score"], candidates[1]["energy_score"])

    def test_build_candidate_windows_allows_unfixed_duration_review(self):
        self.assertEqual(
            build_candidate_windows(
                [{"id": "shot-001", "source_in": 0.0, "source_out": 1.0}],
                target_duration_s=None,
            ),
            [],
        )

    def test_analyze_cli_allows_omitting_target_duration(self):
        args = build_parser().parse_args([
            "analyze", "--input", "movie.mp4", "--out", "analysis.json",
        ])
        self.assertIsNone(args.target_duration)

    def test_analyze_without_target_marks_duration_pending(self):
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "movie.mp4"
            output = Path(temp_dir) / "analysis.json"
            source.write_bytes(b"source")
            with patch(
                "tools.high_energy_analyzer.probe_media",
                return_value={"duration_s": 4.0, "width": 1920, "height": 1080},
            ), patch(
                "tools.high_energy_analyzer.detect_scene_boundaries",
                return_value=([0.0, 2.0, 4.0], []),
            ), patch(
                "tools.high_energy_analyzer.extract_audio_bins",
                return_value=([], []),
            ), patch(
                "tools.high_energy_analyzer.load_transcript",
                return_value=([], ["word_level_transcript_not_provided"]),
            ), patch(
                "tools.high_energy_analyzer._sha256",
                return_value="hash",
            ), patch(
                "tools.high_energy_analyzer._tool_version",
                return_value="test",
            ):
                payload = analyze_file(source, None, output)

            self.assertEqual(payload["candidates"], [])
            self.assertEqual(payload["duration"]["mode"], "content_driven_pending")
            self.assertTrue(payload["duration"]["decision_required"])
            self.assertIn(
                "duration_not_fixed_content_review_required",
                payload["warnings"],
            )

    def test_validate_selection_rejects_source_overrun_timeline_gap_and_duration_drift(self):
        result = validate_selection(
            {
                "target_duration_s": 4.0,
                "order_policy": "chronological",
                "segments": [
                    {
                        "segment_id": "seg-001",
                        "source_in": 8.0,
                        "source_out": 10.0,
                        "timeline_start": 0.0,
                        "timeline_end": 2.0,
                        "playback_rate": 1.0,
                        "audio_playback_rate": 0.9,
                    },
                    {
                        "segment_id": "seg-002",
                        "source_in": 3.0,
                        "source_out": 4.0,
                        "timeline_start": 3.0,
                        "timeline_end": 4.0,
                        "playback_rate": 1.0,
                        "audio_playback_rate": 1.0,
                    },
                ],
            },
            source_duration_s=9.0,
        )

        self.assertFalse(result["ok"])
        self.assertIn("source_range_out_of_bounds", result["errors"])
        self.assertIn("timeline_gap", result["errors"])
        self.assertIn("target_duration_mismatch", result["errors"])
        self.assertIn("picture_audio_rate_mismatch", result["errors"])
        self.assertIn("chronological_order_violation", result["errors"])

    def test_validate_selection_requires_explicit_reuse_and_accepts_explicit_reorder(self):
        selection = {
            "target_duration_s": 2.0,
            "order_policy": "reordered",
            "allow_reuse": True,
            "segments": [
                {
                    "segment_id": "seg-002",
                    "source_in": 2.0,
                    "source_out": 3.0,
                    "timeline_start": 0.0,
                    "timeline_end": 1.0,
                    "playback_rate": 1.0,
                    "audio_playback_rate": 1.0,
                },
                {
                    "segment_id": "seg-002",
                    "source_in": 2.0,
                    "source_out": 3.0,
                    "timeline_start": 1.0,
                    "timeline_end": 2.0,
                    "playback_rate": 1.0,
                    "audio_playback_rate": 1.0,
                },
            ],
        }

        result = validate_selection(selection, source_duration_s=3.0)

        self.assertTrue(result["ok"])
        self.assertEqual(result["computed_duration_s"], 2.0)

    def test_missing_ffmpeg_scene_detection_is_explicitly_degraded(self):
        with patch("tools.high_energy_analyzer.shutil.which", return_value=None):
            boundaries, warnings = detect_scene_boundaries(Path("movie.mp4"), 12.0)

        self.assertEqual(boundaries, [0.0, 12.0])
        self.assertIn("ffmpeg_missing_scene_detection_skipped", warnings)

    def test_missing_ffprobe_is_a_clear_hard_failure(self):
        with patch("tools.high_energy_analyzer.shutil.which", return_value=None):
            with self.assertRaisesRegex(AnalysisError, "ffprobe is required"):
                probe_media(Path("movie.mp4"))

    def test_missing_audio_is_explicitly_degraded(self):
        with patch("tools.high_energy_analyzer.shutil.which", return_value=None):
            bins, warnings = extract_audio_bins(Path("movie.mp4"))

        self.assertEqual(bins, [])
        self.assertIn("ffmpeg_missing_audio_analysis_skipped", warnings)

    def test_missing_transcript_is_explicitly_degraded(self):
        words, warnings = load_transcript(None)

        self.assertEqual(words, [])
        self.assertIn("word_level_transcript_not_provided", warnings)

    def test_transcript_words_contribute_dialogue_signal(self):
        from tools.high_energy_analyzer import _shot_features

        features = _shot_features(
            0.0,
            2.0,
            [],
            [{"text": "go", "start": 0.2, "end": 0.5}, {"text": "now", "start": 1.0, "end": 1.2}],
        )

        self.assertGreater(features["dialogue_signal"], 0.0)


if __name__ == "__main__":
    unittest.main()
