#!/usr/bin/env bash
set -euo pipefail

workspace="$(pwd)"
echo "Video workspace: $workspace"

missing=()
for cmd in node npm ffmpeg; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    missing+=("$cmd")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Missing commands: ${missing[*]}"
  echo "Install the missing tools, then run ./doctor.sh again."
else
  echo "Required commands are available."
fi

mkdir -p assets projects outputs .codex-tmp

if [ ! -f .env.local ] && [ -f .env.example ]; then
  cp .env.example .env.local
  echo "Created .env.local from .env.example. Fill in your own API keys."
fi

echo "Setup complete. Run ./doctor.sh for a full environment report."
