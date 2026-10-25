#!/bin/sh
# Rebuild the LibreOffice-made fixtures (needs LibreOffice; feature 003, T01).
# LibreOffice compiles each StarMath formula to its own MathML and writes its own styles,
# manifest and pictures: these files are what a real user's .odt looks like.
set -e
cd "$(dirname "$0")"
soffice --headless --convert-to odt --outdir . report.fodt
