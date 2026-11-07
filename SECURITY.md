# Security policy

ClearMD runs entirely on your computer: it opens no network connection, and your documents never
leave your machine. A security problem is still possible. Examples: a crafted document that makes
the converter run code, read files outside what you chose, or write outside the output folder.

## Supported versions

Only the [latest release](https://github.com/ClearNote97/ClearMD/releases/latest) receives fixes.

## Reporting a vulnerability

Please **do not open a public issue**. Report it privately through
[GitHub's private vulnerability reporting](https://github.com/ClearNote97/ClearMD/security/advisories/new)
(*Security → Report a vulnerability*). Include:

- the ClearMD version and your system (Windows or Linux);
- the steps to reproduce it, and a sample file if one is needed (strip anything private first);
- what happened and what you expected.

You will get an answer within 7 days. Once a fix is published, the advisory is made public with
credit to you, unless you prefer otherwise.

## Checking a download

Each release carries `SHA256SUMS.txt`, the SHA-256 checksum of every file in it. Compare it with the
file you downloaded:

```bash
sha256sum --check --ignore-missing SHA256SUMS.txt        # Linux
```

```powershell
Get-FileHash .\ClearMD-Setup-1.2.0.exe -Algorithm SHA256   # Windows: compare with the line in SHA256SUMS.txt
```
