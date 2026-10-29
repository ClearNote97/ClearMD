"""The desktop app inside the executable (feature 006, ADR-0028): what ``clearmd-ttk`` runs.

While Python loads, the splash says how far the start has gone (feature 007): the percentages
mark real stages (the toolkit and ClearMD imported, the window built), not a fine counter.
"""

try:
    import pyi_splash  # only inside the executable
except ImportError:
    pyi_splash = None

if pyi_splash is not None:
    pyi_splash.update_text("Loading… 30 %")

from clearmd.frontend.ttk import main  # noqa: E402 -- the heavy import, after the first step

if pyi_splash is not None:
    pyi_splash.update_text("Loading… 70 %")

if __name__ == "__main__":
    main()
