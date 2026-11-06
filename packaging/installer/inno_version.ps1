# The installer's look (ADR-0041) needs Inno Setup 6.7 or newer: older compilers reject its
# directives. ISCC.exe carries no version in its file details (0.0.0.0) and its banner says only
# "Inno Setup 6", so the version is read where Inno's own installer records it: its entry in
# "Installed apps" (the registry). Exit 1 when it is older than 6.7 or cannot be found.
$keys = @(
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1"
)
$found = $keys | Where-Object { Test-Path $_ } | ForEach-Object { (Get-ItemProperty $_).DisplayVersion } | Select-Object -First 1
if (-not $found) { "Inno Setup: no entry in Installed apps"; exit 1 }
"Inno Setup version: $found"
$number = [version]($found -replace '[^0-9.].*$', '')
if ($number -lt [version]"6.7") { "Inno Setup 6.7 or newer is needed (found $found)"; exit 1 }
exit 0
