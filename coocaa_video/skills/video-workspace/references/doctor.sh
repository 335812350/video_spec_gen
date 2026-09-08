#!/usr/bin/env bash
set +e

echo "Video workspace doctor"

for cmd in node npm ffmpeg; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "%-10s OK\n" "$cmd"
  else
    printf "%-10s MISSING\n" "$cmd"
  fi
done

if command -v node >/dev/null 2>&1; then
  node --version
fi
if command -v npm >/dev/null 2>&1; then
  npm --version
fi
if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -version | head -n 1
fi

echo
echo "Directory layout:"
for dir in assets projects outputs; do
  if [ -d "$dir" ]; then
    printf "%-10s OK\n" "$dir"
  else
    printf "%-10s MISSING\n" "$dir"
  fi
done

echo
echo "Next steps:"
echo "1. Put source media under assets/<film-slug>/."
echo "2. Fill required keys in .env.local."
echo "3. Ask Codex to generate or revise video-spec.md."
echo "4. Put task-scoped temporary files in .codex-tmp/<project-slug>/ and clean them up after the task."
