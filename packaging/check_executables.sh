#!/usr/bin/env bash
# The built executables work (feature 006, ADR-0028): the command line converts a real batch,
# with the worker process, the detection by content and every converter; the window opens and
# closes by itself (--smoke). Usage: packaging/check_executables.sh <dist folder>
set -euo pipefail

dist="$(cd "$1" && pwd)"
suffix=""
if [[ "${OS:-}" == "Windows_NT" ]]; then suffix=".exe"; fi
here="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

mkdir -p "$work/in"
for name in sample.pdf sample.docx sample.xlsx sample.pptx sample.epub sample.ipynb sample.html \
    sample.csv sample.txt docx_without_extension; do
  cp "$here/tests/fixtures/documents/$name" "$work/in/"
done
cp "$here/tests/fixtures/tex/paper.tex" "$work/in/"
cp "$here/tests/fixtures/odt/report.odt" "$work/in/"
expected=$(ls "$work/in" | wc -l)

"$dist/clearmd-cli$suffix" "$work/in" --lang es --summary-pdf
written=$(find "$work/ClearMD_Output/OutputMD" -name '*.md' | wc -l)
test -f "$work/ClearMD_Output/Resumen_ClearMD.md"
test -f "$work/ClearMD_Output/Resumen_ClearMD.pdf"
if [[ "$written" -ne "$expected" ]]; then
  echo "expected $expected Markdown files, found $written" >&2
  exit 1
fi
echo "command line: $written of $expected converted"

if [[ "$(uname -s)" == "Linux" ]]; then
  HOME="$work" timeout 120 xvfb-run -a "$dist/ClearMD" --smoke
else
  HOME="$work" timeout 120 "$dist/ClearMD$suffix" --smoke
fi
echo "window: opened and closed"

# A light executable (feature 010): each program under this size (MB: millions of bytes), and
# none of the libraries it leaves out inside.
MAX_MB=50
for program in "$dist/ClearMD$suffix" "$dist/clearmd-cli$suffix"; do
  listing=$(cd "$here" && uv run --no-default-groups --group build pyi-archive_viewer -r "$program")
  if [[ -z "$listing" ]]; then
    echo "$program could not be listed" >&2
    exit 1
  fi
  heavy=$(echo "$listing" | grep -E "'(numpy|pandas|onnxruntime|magika)[./']" || true)
  if [[ -n "$heavy" ]]; then
    echo "$program holds a library it should leave out:" >&2
    echo "$heavy" | head -5 >&2
    exit 1
  fi
  size=$(( $(wc -c < "$program") / 1000 / 1000 ))
  if (( size >= MAX_MB )); then
    echo "$program is $size MB, over $MAX_MB MB" >&2
    exit 1
  fi
  echo "$(basename "$program"): $size MB"
done

# The PySide6 window (feature 016, ADR-0038): a folder, not one file. It starts the same way, holds
# no heavy library and no toolkit of the other windows, and its whole folder has a size cap of its
# own: measured 180 MB (Linux, 2026-11-05: the Qt libraries and ICU's data are most of it), capped at
# 225 MB (+25%). A bigger folder is a new library or a missed exclusion (packaging/clearmd_pyside.spec).
QT_MAX_MB=225
qt_dir="$dist/ClearMD-Qt"
if [[ -d "$qt_dir" ]]; then
  qt="$qt_dir/ClearMD-Qt$suffix"
  if [[ "$(uname -s)" == "Linux" ]]; then
    HOME="$work" timeout 120 xvfb-run -a "$qt" --smoke
  else
    HOME="$work" timeout 120 "$qt" --smoke
  fi
  echo "window (PySide6): opened and closed"
  listing=$(cd "$here" && uv run --no-default-groups --group build pyi-archive_viewer -r "$qt")
  if [[ -z "$listing" ]]; then
    echo "$qt could not be listed" >&2
    exit 1
  fi
  heavy=$(echo "$listing" | grep -E "'(numpy|pandas|onnxruntime|magika|tkinter|_tkinter|ttkbootstrap|tkinterdnd2|flet)[./']" || true)
  if [[ -n "$heavy" ]]; then
    echo "$qt holds a library it should leave out:" >&2
    echo "$heavy" | head -5 >&2
    exit 1
  fi
  size=$(find "$qt_dir" -type f -exec cat {} + | wc -c)
  size=$(( size / 1000 / 1000 ))
  if (( size >= QT_MAX_MB )); then
    echo "ClearMD-Qt folder is $size MB, over $QT_MAX_MB MB" >&2
    exit 1
  fi
  echo "ClearMD-Qt: $size MB (folder)"
fi
