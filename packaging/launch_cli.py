"""The command line inside the executable (feature 006, ADR-0028): what ``clearmd`` runs."""

import sys

from clearmd.frontend.cli import main

if __name__ == "__main__":
    sys.exit(main())
