"""The PySide6 window inside the executable (feature 016, ADR-0038): what ``clearmd-pyside`` runs.

No splash: the folder starts fast (the splash is the one-file programs' cover while they unpack).
"""

import sys

from clearmd.frontend.pyside import main

if __name__ == "__main__":
    sys.exit(main())
