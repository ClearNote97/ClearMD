# tests/support — Shared test helpers

Imported by `conftest.py` and by the tests (`from support import …`): the network guard of ADR-0005 (also
installed inside worker processes) and the paths of the generated fixtures.

`source_tree.py` measures every `.py` file for the size rule (ADR-0039); `size_ratchet.py` lists what was over
the rule when refactor R01 began (it may only shrink, and is empty when R01 ends).
