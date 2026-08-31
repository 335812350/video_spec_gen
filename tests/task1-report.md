# Task 1: Alibaba Cloud TTS Core

## Status

Implemented `tools/aliyun_tts.py` and offline standard-library tests in
`tests/test_aliyun_tts.py`. No network calls or cloud credentials are used by
the test suite.

## Covered behavior

- `.env.local` configuration with explicit key > environment > file precedence.
- Beijing Workspace default base URL and actionable missing-key errors.
- Qwen-Audio/CosyVoice and Qwen3-TTS endpoint routing.
- Non-streaming URL/data responses, SSE base64 chunks, immediate URL download,
  and atomic output writes.
- Model catalog/permission queries and customization voice listing.
- Voice enrollment using URL or Qwen-TTS local Data URI, including model-family,
  source, extension, empty-file, and 10 MB size validation.
- CLI subcommands: `synthesize`, `models`, `voices`, and `clone`.

## Verification

```text
python -m unittest discover -s tests -p 'test_aliyun_tts.py' -v
python -m py_compile tools/aliyun_tts.py tests/test_aliyun_tts.py
```

The implementation uses only Python standard-library modules. A real smoke test
is intentionally deferred until the user supplies a valid `DASHSCOPE_API_KEY`.

## Concerns

- The voice customization API requires account permissions and model-specific
  audio requirements; the client validates local transport constraints but does
  not claim to replace Alibaba's server-side review.
- The CLI accepts `--extra-json` as a JSON object and merges it into the native
  request while keeping stable model/text/voice/format/sample-rate arguments
  authoritative.
