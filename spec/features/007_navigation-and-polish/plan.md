# Plan — Feature 007: Navigation and window polish

> Criteria: [`spec.md`](./spec.md). Decisions: ADR-0026, ADR-0027, ADR-0029.

- **Presenter:** `page` and `go_to(page)`; `StateView.page` and `StateView.primary`
  (`Primary(label, enabled, hint)`), computed per page; editing allowed outside the work states and
  dropping the plan; `convert_more(keep)`; the version for the views.
- **ttk:** the rail (clickable steps, dimmed, smooth circles, compact mode, the version); one
  primary button per page bound to the presenter's `Primary`, the hint under it; the Convert page
  with a "ready" card and the progress; the convert-more dialog; `FileList` with a checkbox in the
  row picture, a header checkbox, faint separators (an image element), click-on-empty and Clear
  selection; redraws debounced on resize; a lower minimum size.
- **Splash:** the subtitle in the image; `pyi_splash.update_text` at each start-up stage.
- **Tests first;** screenshots; the acceptance file; reviews; v0.2.0.
