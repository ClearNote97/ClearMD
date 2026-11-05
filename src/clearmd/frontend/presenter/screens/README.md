# presenter/screens — What each step shows

Pure functions: `(catalog, data…) -> view model`. They read nothing from the presenter and
change nothing; the display pushes what they return to the view.

| Module | What |
|---|---|
| `choose.py` | Choose: the input rows, the output choice, how a path is shown and compared |
| `review.py` | Review: the plan's rows, summary and figures |
| `convert.py` | Convert: the progress of the file being converted |
| `results.py` | Results: the batch's rows, figures and result folders |
| `primary.py` | The page's primary action: its text, whether it is enabled, why not |
