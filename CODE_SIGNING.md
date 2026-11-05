# Code signing policy

Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by [SignPath Foundation](https://signpath.org/).

## What is signed

The Windows executables of each [release](https://github.com/ClearNote97/ClearMD/releases):
`ClearMD-<version>-windows.exe` (the desktop app) and `clearmd-cli-<version>-windows.exe` (the
command line). They are built from this repository's source by GitHub Actions
([`release.yml`](./.github/workflows/release.yml)) and sent to SignPath from that same run; nothing
built elsewhere is signed. The Linux archive is not signed.

## Team roles

- **Committers and reviewers:** [ClearNote97](https://github.com/ClearNote97) (the author).
  Changes written with an AI agent are reviewed by the author before they are merged.
- **Approvers:** [ClearNote97](https://github.com/ClearNote97). Each signing request of a release
  is approved by hand.

## Privacy policy

This program will not transfer any information to other networked systems unless specifically
requested by the user or the person installing or operating it. ClearMD never uses the internet:
it reads the documents chosen by the user and writes Markdown next to them, on the same computer.
