# presenter/chrome — What every window decides the same way

Pure functions, no toolkit (ADR-0039): each GUI draws what they return; its timers and widgets
stay its own.

| Module | What |
|---|---|
| `header.py` | The page's header: step counter (and state), title, subtitle or the scan's count |
| `secondary.py` | The action bar's second button (Cancel, Back, Convert more) and Convert's ready line |
| `primary_gate.py` | The primary action's pause after a page change (F-1) |
| `close_policy.py` | Closing while converting: cancel, wait for the summary, then close |
