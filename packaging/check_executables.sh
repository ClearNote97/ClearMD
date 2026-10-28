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

"$dist/clearmd$suffix" "$work/in" --lang es
written=$(find "$work/ClearMD_Output/OutputMD" -name '*.md' | wc -l)
test -f "$work/ClearMD_Output/Resumen_ClearMD.md"
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
