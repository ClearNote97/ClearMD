# src/clearmd/backend/services/worker — Worker process (ADR-0015)

- `protocol.py` — the messages that cross the pipe (picklable dataclasses).
- `child.py` — the worker: ignores Ctrl+C, builds its converter registry **once** from a `module:function`
  path (the real one, or a fake in the tests) and converts one file after another.
- `supervisor.py` — `WorkerRunner`, the `ConversionRunner` the use cases see. It watches the worker every
  0.1 s: cancellation, time limit, memory limit (psutil), unexpected death. On any of them it kills the worker;
  the next file starts a new one.
