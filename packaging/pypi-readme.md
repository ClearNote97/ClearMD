# ClearMD

**Prepare your documents for AI, 100 % on your computer.** ClearMD converts documents to clean
Markdown, splits a large file into parts that fit an AI, and merges several into one, without
uploading anything anywhere.

- **Convert to Markdown:** PDF, Word, PowerPoint, Excel, OpenDocument, LaTeX, web pages, CSV,
  EPUB, Jupyter notebooks, plain text, e-mails, Rich Text and subtitles.
- **Split:** a PDF into N parts, every N pages, or parts of about N words; Markdown at its
  headings; text and CSV between lines or rows; Excel by whole sheets.
- **Merge:** several documents into one Markdown, or several PDFs into one PDF.
- **Private:** ClearMD never uses the internet. Your files never leave your computer.

## Install

```bash
pipx install clearmd        # or: uv tool install clearmd
clearmd report.pdf notes.docx            # convert
clearmd big.pdf --split-words 30000      # split into parts that fit an AI
clearmd *.pdf --merge pdf                # merge into one PDF
clearmd --help
```

The desktop app is `clearmd-ttk`; the Qt and flet windows need their extras
(`pip install "clearmd[pyside]"`, `pip install "clearmd[flet]"`). Windows users can also
download the installer from the
[releases](https://github.com/ClearNote97/ClearMD/releases/latest).

## Learn more

- [Source, screenshots and documentation](https://github.com/ClearNote97/ClearMD)
- [What is new in each version](https://github.com/ClearNote97/ClearMD/blob/main/packaging/RELEASE_NOTES.md)
- [Security policy](https://github.com/ClearNote97/ClearMD/blob/main/SECURITY.md)

MIT License.
