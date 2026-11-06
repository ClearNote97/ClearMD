"""The licenses of everything bundled in the executables (feature 006): printed to stdout.

Each installed distribution's name, version, declared license and license files, as its own
package metadata states them. Run in the build environment:
``uv run --no-default-groups --group build python packaging/notices.py``.
"""

import sys
from importlib.metadata import Distribution, distributions

# setuptools and packaging ship (PyInstaller bundles what its hooks import): they are listed.
BUILD_ONLY = {"pyinstaller", "pyinstaller-hooks-contrib", "altgraph"}
# The Qt window's folder (ClearMD-Qt/, ADR-0038): PySide6 and Qt are LGPL, so their libraries are
# plain files there, replaceable by other builds of the same libraries (the LGPL asks for it).
QT_NOTE = (
    "The Qt window (the folder ClearMD-Qt/) bundles PySide6 and Qt under the GNU Lesser General "
    "Public License, version 3 (LGPL-3.0, https://www.gnu.org/licenses/lgpl-3.0.html); ClearMD "
    "takes the LGPL option the packages offer. Its Qt libraries are plain files in that folder: "
    "you can replace them with other builds of the same libraries."
)
# The flet window's folder (ClearMD-Flet/, ADR-0042): flet's window program is a Flutter app; its
# own notices (Flutter, Skia and the libraries it bundles) travel inside it.
FLET_NOTE = (
    "The flet window (the folder ClearMD-Flet/) bundles flet's window program, version 1.0.5, "
    "from https://github.com/flet-dev/flet (Apache-2.0), built with Flutter (BSD-3-Clause). The "
    "licenses of Flutter and the libraries it bundles are in that folder, in "
    "flet-client/flet/data/flutter_assets/NOTICES.Z (a compressed text file)."
)
# Installed with markitdown, left out of the executables (packaging/clearmd.spec, ADR-0032).
NOT_SHIPPED = {"magika", "onnxruntime", "numpy", "pandas", "flatbuffers", "coloredlogs",
               "humanfriendly", "sympy", "mpmath", "protobuf", "click"}  # fmt: skip


def describe(distribution: Distribution) -> str:
    metadata = distribution.metadata
    name, version = metadata["Name"], distribution.version
    declared = metadata.get("License-Expression") or metadata.get("License") or ""
    classifiers = [
        c.split(" :: ")[-1] for c in metadata.get_all("Classifier") or [] if "License" in c
    ]
    lines = [f"{name} {version}", f"License: {declared or ', '.join(classifiers) or 'see below'}"]
    for file in distribution.files or ():
        parts = {part.lower() for part in file.parts}
        if "licenses" in parts or file.name.upper().startswith(("LICENSE", "COPYING", "NOTICE")):
            path = file.locate()
            text = _decoded(path.read_bytes()) if path.is_file() else ""
            if text.strip():
                lines += ["", f"--- {file.name} ---", text.strip()]
    return "\n".join(lines)


def _decoded(data: bytes) -> str:
    """License files are mostly UTF-8; a few older ones are Latin-1 (a © byte)."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def main() -> int:
    found = sorted(distributions(), key=lambda d: d.metadata["Name"].lower())
    left_out = BUILD_ONLY | NOT_SHIPPED
    bundled = [d for d in found if d.metadata["Name"].lower() not in left_out]
    print("ClearMD bundles the following open-source software. Thank you to their authors.\n")
    print(QT_NOTE + "\n")
    print(FLET_NOTE + "\n")
    separator = "\n\n" + "=" * 78 + "\n\n"
    print(separator.join(describe(d) for d in bundled))
    return 0


if __name__ == "__main__":
    sys.exit(main())
