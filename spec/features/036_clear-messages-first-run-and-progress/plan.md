# Plan — Feature 036

- **Wording by channel** (`i18n`: `[terminal]` overlay, `Catalog.for_terminal`; the CLI loads it).
  The window's catalog keeps no `--option`; a test bans options and library names from it.
- **Causes** (`markitdown_adapter`: the OLE signature of an encrypted .docx/.pptx is
  PASSWORD_PROTECTED; `ErrorCode.EMPTY_FILE` for an empty text, CSV or Markdown split;
  `scanning.unsupported_reason`: `OLD_OFFICE`, `IMAGE`).
- **Progress** (`services/conversion/progress.py` → `child` sends `Progress` → `processes.
  wait_for_response` resets the clock and calls `CancelToken.progress` → `execution` emits
  `ConversionProgress` → the presenter's progress line).
- **Excel** (`splitting.split_cost(format_id)`, `split_memory`, checked in `planning`).
- **Installer** (`packaging/installer/clearmd.iss`, `check_installer.ps1`, `release.yml`,
  `package.sh`), as the doubts board decides; verified by a manual run of the release workflow
  on the branch before tagging.
