# presenter/intents — What the user can ask for

Small classes built from the session, the display, the backend and the background work.
None of them holds the presenter; the presenter forwards each public intent to one of them.

| Module | What |
|---|---|
| `inputs.py` | Add, remove and clear the inputs; choose where the results go |
| `analysis.py` | Compute the plan off the UI thread; the scan's count; cancel |
| `conversion.py` | Convert the plan, the file timer, the batch's end; cancel |
| `results.py` | Open the result folders; convert more |
| `preferences.py` | Start, apply and save the settings; the welcome |
| `reset.py` | Dropping the plan and the result: an edit, an unexpected error |
