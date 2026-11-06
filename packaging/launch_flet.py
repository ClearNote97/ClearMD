"""The flet window inside the executable (feature 018, ADR-0042): what ``clearmd-flet`` runs.

flet's window program travels in the folder, next to this program (``flet-client/flet/``,
fetched and checked by ``packaging/fetch_flet_client.py``, copied by ``clearmd_flet.spec``).
``FLET_VIEW_PATH`` points flet to it, so it never downloads one nor unpacks one into the user's
home folder. The working folder is the executable's own, so a ``build/`` folder where the user
started it cannot be taken for a flet build.
"""

import os
import sys
from pathlib import Path

from clearmd.frontend.flet import main

if __name__ == "__main__":
    folder = Path(sys.executable).resolve().parent
    os.environ["FLET_VIEW_PATH"] = str(folder / "flet-client" / "flet")
    os.chdir(folder)
    sys.exit(main())
