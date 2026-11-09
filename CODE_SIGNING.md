# Code signing policy

Free code signing provided by [SignPath.io](https://about.signpath.io/), certificate by [SignPath Foundation](https://signpath.org/).

## What is signed

The Windows programs of each [release](https://github.com/ClearNote97/ClearMD/releases): the
installers `ClearMD-Setup-<version>.exe` and `ClearMD-Setup-Full-<version>.exe`, and the programs
inside every download (the three apps and `clearmd-cli`). The installers' uninstaller is not
signed yet. They are built from this repository's source by GitHub Actions
([`release.yml`](./.github/workflows/release.yml)) and sent to SignPath from that same run; nothing
built elsewhere is signed. The Linux archive is not signed.

## Team roles

- **Authors:** [ClearNote97](https://github.com/ClearNote97) (the author), trusted to change the
  source code. Changes written with an AI agent are reviewed by the author before they are merged.
- **Reviewers:** [ClearNote97](https://github.com/ClearNote97). Every change proposed by someone
  else (a pull request) is reviewed before it is merged.
- **Approvers:** [ClearNote97](https://github.com/ClearNote97). Each signing request of a release
  is approved by hand.

## Privacy policy

This program will not transfer any information to other networked systems unless specifically
requested by the user or the person installing or operating it. ClearMD never uses the internet:
it reads the documents chosen by the user and writes Markdown next to them, on the same computer.

The open source libraries inside ClearMD (listed in each release's `THIRD-PARTY-NOTICES.txt`)
read files only; none of them is a third-party service, and none sends data anywhere.

## Uninstall

Installed with `ClearMD-Setup-<version>.exe`: remove it from Windows' *Installed apps* (it asks before deleting
the settings, and never touches documents). Without the installer, ClearMD installs nothing: delete the executable,
and optionally its settings folder
(`%LOCALAPPDATA%\ClearMD` on Windows, `~/.config/ClearMD` on Linux). See the README.
