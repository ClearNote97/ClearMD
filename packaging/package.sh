#!/usr/bin/env bash
# The release files of one system (feature 006, 016, 018): the desktop app, the command line, the
# PySide6 window (a folder, ClearMD-Qt/), the flet window (a folder, ClearMD-Flet/), the Windows
# installer and the third-party notices.
# Usage: packaging/package.sh <dist folder> <windows|linux> <version>
# A version taken from a branch (refactor/modularity) has its "/" replaced by "-" in the names.
set -euo pipefail

dist="$1"
system="$2"
version="${3#refs/tags/}"
version="${version//\//-}"
mkdir -p release
uv run --no-default-groups --group build python packaging/notices.py > release/THIRD-PARTY-NOTICES.txt
# The Qt folder carries its licenses with it (LGPL: the license travels with the libraries).
cp LICENSE release/THIRD-PARTY-NOTICES.txt "$dist/ClearMD-Qt/"
cp LICENSE release/THIRD-PARTY-NOTICES.txt "$dist/ClearMD-Flet/"
if [[ "$system" == "windows" ]]; then
  cp "$dist/ClearMD.exe" "release/ClearMD-$version-windows.exe"
  cp "$dist/clearmd-cli.exe" "release/clearmd-cli-$version-windows.exe"
  # The installers (feature 017, ADR-0040; two editions since 037, ADR-0052) were compiled and
  # checked by the workflow, step "Installer". Their names carry their version, so they are copied
  # as they are: one light (ClearMD-Setup-<version>.exe) and one full (ClearMD-Setup-Full-...).
  shopt -s nullglob
  lights=("$dist"/installer/ClearMD-Setup-[0-9]*.exe)
  fulls=("$dist"/installer/ClearMD-Setup-Full-*.exe)
  shopt -u nullglob
  if [[ "${#lights[@]}" -ne 1 || "${#fulls[@]}" -ne 1 ]]; then
    echo "expected one ClearMD-Setup-<version>.exe and one ClearMD-Setup-Full-*.exe in $dist/installer, found ${#lights[@]} and ${#fulls[@]}" >&2
    exit 1
  fi
  cp "${lights[0]}" "${fulls[0]}" release/
  # The folder is the zip's top level. Python's zipfile is used (not a Git Bash zip) so it works
  # the same on every runner; the project is named explicitly because the folder is not in it.
  here="$(pwd)"
  (cd "$dist" && uv run --project "$here" --no-default-groups --group build \
    python -m zipfile -c "$here/release/ClearMD-Qt-$version-windows.zip" ClearMD-Qt)
  (cd "$dist" && uv run --project "$here" --no-default-groups --group build \
    python -m zipfile -c "$here/release/ClearMD-Flet-$version-windows.zip" ClearMD-Flet)
else
  mkdir -p "stage/ClearMD-$version-linux"
  cp "$dist/ClearMD" "$dist/clearmd-cli" LICENSE release/THIRD-PARTY-NOTICES.txt \
    "stage/ClearMD-$version-linux/"
  # -a keeps the folder's links (PyInstaller's onedir links its Qt libraries): no copies twice.
  cp -a "$dist/ClearMD-Qt" "$dist/ClearMD-Flet" "stage/ClearMD-$version-linux/"
  tar -C stage -czf "release/ClearMD-$version-linux.tar.gz" "ClearMD-$version-linux"
fi
ls -la release
