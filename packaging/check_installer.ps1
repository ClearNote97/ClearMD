# Checks the Windows installer (feature 017, ADR-0040) the way a user would use it: silent installs,
# the installed programs run, silent uninstalls, and nothing left behind. Run by the release
# workflow on Windows after the installer is built (.github/workflows/release.yml).
#
#   packaging\check_installer.ps1 -Installer dist\installer\ClearMD-Setup-0.12.0.exe -Version 0.12.0
#
# The sequence (each step asserts what it changed):
#   1. A silent install with no choice: the default is the classic app only (ttk).
#   2. A silent reinstall of all three parts, the PATH option ticked: every file, shortcut and the
#      PATH entry are there; the programs run; the command line converts a real batch.
#   3. A silent reinstall with only the modern app: the classic app's and the command line's files,
#      shortcuts and PATH entry are removed; the modern app still opens.
#   4. A silent uninstall that keeps the settings: nothing left, the settings file is untouched.
#   5. A silent install and uninstall with /REMOVESETTINGS: the settings folder is removed too.
# Any failed check stops the script with exit code 1 and prints "FAILED: <what>".

param(
  [Parameter(Mandatory)][string]$Installer,
  [Parameter(Mandatory)][string]$Version,
  # An older build of the same script (the workflow compiles it): installed first, then replaced.
  [Parameter(Mandatory)][string]$OldInstaller,
  [Parameter(Mandatory)][string]$OldVersion,
  [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

# Where the installer puts things for the current user (see packaging/installer/clearmd.iss).
$Install = Join-Path $env:LOCALAPPDATA 'Programs\ClearMD'
$SettingsFolder = Join-Path $env:LOCALAPPDATA 'ClearMD'
$StartMenu = Join-Path ([Environment]::GetFolderPath('Programs')) 'ClearMD'
$Desktop = [Environment]::GetFolderPath('Desktop')
$PathKey = 'HKCU:\Environment'
$MarkerKey = 'HKCU:\Software\ClearMD'
# The AppId is read from the script, so the check and the installer can never disagree about it.
$issText = Get-Content -Raw -Encoding utf8 (Join-Path $PSScriptRoot 'installer\clearmd.iss')
$appId = [regex]::Match($issText, 'AppId=\{\{([0-9A-Fa-f-]{36})\}').Groups[1].Value
if (-not $appId) { throw 'FAILED: the AppId was not found in packaging\installer\clearmd.iss' }
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{$appId}_is1"
$SettingsFile = Join-Path $SettingsFolder 'settings.toml'
$SettingsText = "language = `"en`"`ntheme = `"dark`"`n"

# The shortcut file name of each part, and what it must open.
$Shortcut = @{ ttk = 'ClearMD.lnk'; qt = 'ClearMD (Qt).lnk'; cli = 'ClearMD (command line).lnk' }
$Program = @{ ttk = 'ClearMD.exe'; qt = 'ClearMD-Qt\ClearMD-Qt.exe'; cli = 'clearmd-cli.exe' }

function Step([string]$Title) { Write-Host ""; Write-Host "== $Title" }

function Expect([bool]$Ok, [string]$What) {
  if (-not $Ok) { throw "FAILED: $What" }
  Write-Host "  ok: $What"
}

function Invoke-Setup([string[]]$Choice, [string]$Setup = $Installer) {
  $arguments = @($Choice) + '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER'
  $process = Start-Process -FilePath $Setup -ArgumentList $arguments -Wait -PassThru
  $label = if ($Choice.Count -gt 0) { $Choice -join ' ' } else { 'the default choice' }
  Expect ($process.ExitCode -eq 0) "the silent install ($label) exits with 0 (it was $($process.ExitCode))"
}

function Invoke-Uninstall([string[]]$Extra = @()) {
  $uninstaller = Join-Path $Install 'unins000.exe'
  Expect (Test-Path $uninstaller) 'the uninstaller is in the install folder'
  $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') + $Extra
  Start-Process -FilePath $uninstaller -ArgumentList $arguments -Wait | Out-Null
  # Inno's uninstaller copies itself to %TEMP% and continues there: the call above can return
  # before the files are gone, so wait for the folder to disappear (or give up).
  $deadline = (Get-Date).AddSeconds(240)
  while ((Test-Path $Install) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 2 }
  $left = if (Test-Path $Install) { (Get-ChildItem $Install -Recurse -Force | ForEach-Object FullName) -join ', ' } else { '' }
  Expect (-not (Test-Path $Install)) "the install folder is gone after the uninstall (left: $left)"
}

function Get-Shortcut([string]$Path) {
  (New-Object -ComObject WScript.Shell).CreateShortcut($Path)
}

function Test-OnUserPath {
  $userPath = (Get-ItemProperty -Path $PathKey -Name Path -ErrorAction SilentlyContinue).Path
  $entries = @($userPath -split ';' | ForEach-Object { $_.TrimEnd('\') })
  return $entries -contains $Install.TrimEnd('\')
}

# The files, shortcuts and registry entry for the parts chosen (a list of 'ttk', 'qt', 'cli').
function Assert-Layout([string[]]$Chosen) {
  $parts = 'ttk', 'qt', 'cli'
  foreach ($part in $parts) {
    $wanted = $Chosen -contains $part
    $exe = Join-Path $Install $Program[$part]
    $link = Join-Path $StartMenu $Shortcut[$part]
    $state = if ($wanted) { 'installed' } else { 'absent' }
    Expect ((Test-Path $exe) -eq $wanted) "$part program file is $state"
    Expect ((Test-Path $link) -eq $wanted) "$part Start menu shortcut is $state"
  }
  # The Qt folder keeps its own license (LGPL): it goes with the folder.
  Expect ((Test-Path (Join-Path $Install 'ClearMD-Qt')) -eq ($Chosen -contains 'qt')) 'the ClearMD-Qt folder matches the choice'
  # Always present, whatever the choice: the uninstaller, the license, the notices, the icon.
  foreach ($name in 'unins000.exe', 'LICENSE', 'THIRD-PARTY-NOTICES.txt', 'clearmd.ico') {
    Expect (Test-Path (Join-Path $Install $name)) "$name is in the install folder"
  }
  # The Start menu folder: one shortcut per part chosen, plus the uninstaller's.
  $links = @(Get-ChildItem $StartMenu -Filter '*.lnk' -ErrorAction SilentlyContinue).Count
  Expect ($links -eq $Chosen.Count + 1) "the Start menu has $($Chosen.Count + 1) shortcuts (found $links)"
  # The desktop: no shortcut, because no run here ticks the desktop task.
  $desk = @(Get-ChildItem $Desktop -Filter 'ClearMD*.lnk' -ErrorAction SilentlyContinue).Count
  Expect ($desk -eq 0) 'no desktop shortcut without the desktop task'
  # Registry: the Installed apps entry, with its name, version and publisher.
  Expect (Test-Path $UninstallKey) 'the Installed apps entry (HKCU uninstall key) is there'
  $entry = Get-ItemProperty -Path $UninstallKey
  Expect ($entry.DisplayName -eq 'ClearMD') "its DisplayName is ClearMD (it is '$($entry.DisplayName)')"
  Expect ($entry.DisplayVersion -eq $Version) "its DisplayVersion is $Version (it is '$($entry.DisplayVersion)')"
  Expect ($entry.Publisher -eq 'ClearNote97') "its Publisher is ClearNote97 (it is '$($entry.Publisher)')"
}

# A shortcut opens the right program: the classic and modern apps directly, the command line
# through the Windows command prompt, with the help shown and the program named.
function Assert-Targets([string[]]$Chosen) {
  foreach ($part in $Chosen) {
    $link = Get-Shortcut (Join-Path $StartMenu $Shortcut[$part])
    if ($part -eq 'cli') {
      Expect ($link.TargetPath -like '*\cmd.exe') 'the command line shortcut opens the command prompt (cmd.exe)'
      Expect ($link.Arguments -like '*clearmd-cli.exe*--help*') 'the command line shortcut shows the help and keeps the prompt open'
    } else {
      Expect ($link.TargetPath -eq (Join-Path $Install $Program[$part])) "the $part shortcut opens $($Program[$part])"
    }
  }
}

# The program opens its window and closes it by itself (--smoke, feature 006): a timeout means a hang.
function Invoke-Smoke([string]$Part) {
  $exe = Join-Path $Install $Program[$Part]
  $process = Start-Process -FilePath $exe -ArgumentList '--smoke' -WorkingDirectory (Split-Path $exe) -PassThru
  if (-not $process.WaitForExit(90000)) {
    $process.Kill()
    throw "FAILED: the $Part window did not close by itself with --smoke"
  }
  Expect ($process.ExitCode -eq 0) "the $Part window opened and closed by itself (exit $($process.ExitCode))"
}

# The installed command line converts a real batch of the repository's fixtures (as check_executables.sh).
function Invoke-CliBatch {
  $work = Join-Path ([IO.Path]::GetTempPath()) ("clearmd-check-" + [guid]::NewGuid().ToString('N'))
  $inputDir = Join-Path $work 'in'
  New-Item -ItemType Directory -Path $inputDir | Out-Null
  foreach ($name in 'sample.pdf', 'sample.docx', 'sample.xlsx', 'sample.pptx', 'sample.epub',
      'sample.ipynb', 'sample.html', 'sample.csv', 'sample.txt', 'docx_without_extension') {
    Copy-Item (Join-Path $Root "tests\fixtures\documents\$name") $inputDir
  }
  Copy-Item (Join-Path $Root 'tests\fixtures\tex\paper.tex') $inputDir
  Copy-Item (Join-Path $Root 'tests\fixtures\odt\report.odt') $inputDir
  $expected = @(Get-ChildItem $inputDir -File).Count
  & (Join-Path $Install 'clearmd-cli.exe') $inputDir --lang es --summary-pdf
  Expect ($LASTEXITCODE -eq 0) 'the installed command line exits with 0'
  $written = @(Get-ChildItem (Join-Path $work 'ClearMD_Output\OutputMD') -Recurse -Filter *.md -ErrorAction SilentlyContinue).Count
  Expect ($written -eq $expected) "the installed command line converted $written of $expected files"
  Expect (Test-Path (Join-Path $work 'ClearMD_Output\Resumen_ClearMD.md')) 'the summary Markdown is written'
  Expect (Test-Path (Join-Path $work 'ClearMD_Output\Resumen_ClearMD.pdf')) 'the summary PDF is written'
  Remove-Item $work -Recurse -Force
}

function Write-Settings {
  New-Item -ItemType Directory -Force -Path $SettingsFolder | Out-Null
  Set-Content -Path $SettingsFile -Value $SettingsText -Encoding utf8 -NoNewline
}

function Assert-Gone {
  Expect (-not (Test-Path $StartMenu)) 'the Start menu folder is gone'
  Expect (-not (Test-Path $UninstallKey)) 'the Installed apps entry is gone'
  Expect (-not (Test-Path $MarkerKey)) 'the PATH marker (HKCU\Software\ClearMD) is gone'
  Expect (-not (Test-OnUserPath)) 'the install folder is not on the user PATH'
  $desk = @(Get-ChildItem $Desktop -Filter 'ClearMD*.lnk' -ErrorAction SilentlyContinue).Count
  Expect ($desk -eq 0) 'no ClearMD desktop shortcut is left'
}

# AC-04: a newer version installed over an older one replaces it: one Installed apps entry (for the
# AppId, with the new version's name), the files of the chosen parts, and one uninstaller. Called
# with the install folder empty; leaves it empty again. Closing a running app is handled by the
# installer's CloseApplications (ADR-0040), not checked here.
function Assert-Upgrade {
  Step '0. An older version is installed, then the current one is installed over it'
  Invoke-Setup @() $OldInstaller
  Expect ((Get-ItemProperty -Path $UninstallKey).DisplayVersion -eq $OldVersion) "the older version $OldVersion is registered"
  Invoke-Setup @('/COMPONENTS=ttk,qt')
  $entries = @(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall' |
      Where-Object { $_.GetValue('DisplayName') -eq 'ClearMD' })
  Expect ($entries.Count -eq 1) "exactly one Installed apps entry for ClearMD after the upgrade (found $($entries.Count))"
  Expect ($entries[0].PSChildName -eq "{$appId}_is1") 'that entry is the one for the AppId'
  Expect ((Get-ItemProperty -Path $UninstallKey).DisplayVersion -eq $Version) "its DisplayVersion is the new version $Version"
  Expect (Test-Path (Join-Path $Install $Program['ttk'])) 'the classic app of the new version is installed'
  Expect (Test-Path (Join-Path $Install $Program['qt'])) 'the modern app of the new version is installed'
  $uninstallers = @(Get-ChildItem $Install -Filter 'unins*.exe').Count
  Expect ($uninstallers -eq 1) "one uninstaller in the install folder after the upgrade (found $uninstallers)"
  $links = @(Get-ChildItem $StartMenu -Filter '*.lnk').Count
  Expect ($links -eq 3) "the Start menu has no leftover shortcut from the older version (found $links, expected 3)"
  Invoke-Uninstall
  Assert-Gone
}

try {
  if (-not (Test-Path $Installer)) { throw "FAILED: the installer is missing: $Installer" }
  Write-Host ("installer: {0} ({1:N1} MB)" -f (Resolve-Path $Installer), ((Get-Item $Installer).Length / 1MB))
  Expect (-not (Test-Path $Install)) 'the machine starts with no ClearMD installed'
  # The settings folder is the runner's own: start from none, so the checks are exact.
  if (Test-Path $SettingsFolder) { Remove-Item $SettingsFolder -Recurse -Force }

  Assert-Upgrade

  Step '1. Silent install with no choice: the classic app only'
  Invoke-Setup @()
  Assert-Layout @('ttk')
  Assert-Targets @('ttk')
  Expect (-not (Test-OnUserPath)) 'the PATH is not changed without its option'
  Invoke-Smoke 'ttk'

  Step '2. Reinstall: all three parts, the PATH option ticked'
  Invoke-Setup @('/COMPONENTS=ttk,qt,cli', '/TASKS=addpath')
  Assert-Layout @('ttk', 'qt', 'cli')
  Assert-Targets @('ttk', 'qt', 'cli')
  Expect (Test-OnUserPath) 'the install folder is on the user PATH (the option was ticked)'
  Expect (Test-Path $MarkerKey) 'the installer remembers the PATH entry it added'
  Invoke-Smoke 'ttk'
  Invoke-Smoke 'qt'
  Invoke-CliBatch

  Step '3. Reinstall: only the modern app'
  Invoke-Setup @('/COMPONENTS=qt')
  Assert-Layout @('qt')
  Assert-Targets @('qt')
  Expect (-not (Test-OnUserPath)) 'the PATH entry is removed with the command line'
  Expect (-not (Test-Path $MarkerKey)) 'the PATH marker is removed with the command line'
  Invoke-Smoke 'qt'

  Step '4. Silent uninstall: nothing left, the settings are kept'
  Write-Settings
  Invoke-Uninstall
  Assert-Gone
  Expect (Test-Path $SettingsFile) 'the settings file is kept by a silent uninstall'
  Expect ((Get-Content -Raw -Encoding utf8 $SettingsFile) -eq $SettingsText) 'the settings file is unchanged'

  Step '5. Silent uninstall with /REMOVESETTINGS: the settings folder goes too'
  Invoke-Setup @()
  Write-Settings
  Invoke-Uninstall @('/REMOVESETTINGS')
  Assert-Gone
  Expect (-not (Test-Path $SettingsFolder)) 'the settings folder is removed with /REMOVESETTINGS'

  Write-Host ""
  Write-Host 'ALL INSTALLER CHECKS PASSED'
  exit 0
} catch {
  Write-Host $_.Exception.Message
  Write-Host 'INSTALLER CHECKS FAILED'
  exit 1
}
