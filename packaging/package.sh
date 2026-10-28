#!/usr/bin/env bash
# The release files of one system (feature 006): the desktop app, the command line and the
# third-party notices. Usage: packaging/package.sh <dist folder> <windows|linux> <version>
set -euo pipefail

dist="$1"
system="$2"
version="${3#refs/tags/}"
mkdir -p release
uv run --no-default-groups --group build python packaging/notices.py > release/THIRD-PARTY-NOTICES.txt
if [[ "$system" == "windows" ]]; then
  cp "$dist/ClearMD.exe" "release/ClearMD-$version-windows.exe"
  cp "$dist/clearmd-cli.exe" "release/clearmd-cli-$version-windows.exe"
else
  mkdir -p "stage/ClearMD-$version-linux"
  cp "$dist/ClearMD" "$dist/clearmd-cli" LICENSE release/THIRD-PARTY-NOTICES.txt \
    "stage/ClearMD-$version-linux/"
  tar -C stage -czf "release/ClearMD-$version-linux.tar.gz" "ClearMD-$version-linux"
fi
ls -la release
