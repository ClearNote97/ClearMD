# src/clearmd/backend/services/worker — Worker process (ADR-0015)

- `protocol.py` — the messages that cross the pipe (picklable dataclasses).
- `child.py` — the worker: ignores Ctrl+C, builds its converter registry **once** from a `module:function`
  path (the real one, or a fake in the tests), says `Ready`, and converts one file after another.
- `processes.py` — watching the worker: kill its children, read its memory, and the two polling loops (start-up and
  response) that enforce the limits; they receive `stop` and `crashed` from the supervisor.
- `supervisor.py` — `WorkerRunner`, the `ConversionRunner` the use cases see. It watches the worker every
  0.1 s: cancellation, time limit, memory limit (psutil), unexpected death. The time limit starts when a file
  is sent, never during the worker's start-up, which has its own generous limit. On any of them it kills the worker;
  the next file starts a new one.

Two more guards from the security review of feature 001: on POSIX the worker gets a hard OS memory cap
(`RLIMIT_AS` = the limit + 2 GiB for libraries' virtual reservations), so one huge allocation fails at once
instead of swapping the machine (Windows: a Job Object in feature 006); and stopping the worker also kills
any process a converter started.
