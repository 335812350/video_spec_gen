"""Compatibility entry point for the migrated Alibaba Cloud voiceover flow.

The historical filename is retained so existing local commands keep working.
All implementation and output behavior now live in ``generate_aliyun_voiceover``.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_DIR.parents[1]
if str(PROJECT_DIR / "tools") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "tools"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generate_aliyun_voiceover import (  # noqa: E402
    OUTPUT_DIR,
    SCRIPT_PATH,
    extract_chapters,
    generate_voiceover,
    main,
    safe_name,
)

__all__ = [
    "OUTPUT_DIR",
    "SCRIPT_PATH",
    "extract_chapters",
    "generate_voiceover",
    "main",
    "safe_name",
]


if __name__ == "__main__":
    raise SystemExit(main())
