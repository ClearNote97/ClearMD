# Photographs every page of one installer, in light or dark Windows (feature 019, the look).
# Buttons are pressed by their Alt shortcuts (Alt+N is Next), never Enter: the text boxes eat it.
# Runs on the CI's Windows desktop: it drives the wizard with the keyboard, as a person would,
# installs into a folder of its own, then runs the uninstaller and photographs its dialogs too.
param(
    [Parameter(Mandatory)] [string] $Setup,
    [Parameter(Mandatory)] [string] $Out,
    [ValidateSet("light", "dark")] [string] $Theme = "light",
    [ValidateSet("english", "spanish")] [string] $Lang = "english"
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class Win {
    public delegate bool EnumProc(IntPtr h, IntPtr p);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    // The top-most visible window whose title contains the text (EnumWindows walks the z-order).
    public static IntPtr Find(string text) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((h, p) => {
            if (!IsWindowVisible(h)) return true;
            var s = new StringBuilder(256);
            GetWindowText(h, s, 256);
            if (s.ToString().Contains(text)) { found = h; return false; }
            return true;
        }, IntPtr.Zero);
        return found;
    }
}
"@
[void][Win]::SetProcessDPIAware()

# Windows' own switch between light and dark apps; Inno's "dynamic" reads it when it starts.
$personalize = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
New-Item -Path $personalize -Force | Out-Null
$light = [int]($Theme -eq "light")
Set-ItemProperty -Path $personalize -Name AppsUseLightTheme -Value $light -Type DWord
Set-ItemProperty -Path $personalize -Name SystemUsesLightTheme -Value $light -Type DWord

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$script:count = 0

function Window {
    for ($i = 0; $i -lt 40; $i++) {
        $h = [Win]::Find("ClearMD")
        if ($h -ne [IntPtr]::Zero) { return $h }
        Start-Sleep -Milliseconds 250
    }
    throw "No ClearMD window"
}

function Shot([string] $name) {
    Start-Sleep -Milliseconds 900
    $h = Window
    [void][Win]::SetForegroundWindow($h)
    Start-Sleep -Milliseconds 300
    $r = New-Object Win+RECT
    [void][Win]::GetWindowRect($h, [ref]$r)
    $w = $r.Right - $r.Left; $hh = $r.Bottom - $r.Top
    $bitmap = New-Object System.Drawing.Bitmap $w, $hh
    $g = [System.Drawing.Graphics]::FromImage($bitmap)
    $g.CopyFromScreen($r.Left, $r.Top, 0, 0, $bitmap.Size)
    $script:count++
    $file = Join-Path $Out ("{0:D2}-{1}.png" -f $script:count, $name)
    $bitmap.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bitmap.Dispose()
    "  $file"
}

function Press([string] $keys) {
    [void][Win]::SetForegroundWindow((Window))
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait($keys)
}

# The Next button's shortcut: Alt+N in English ("&Next"), Alt+S in Spanish ("&Siguiente").
$next = if ($Lang -eq "spanish") { "%s" } else { "%n" }
$dir = Join-Path $env:RUNNER_TEMP ("look-" + [IO.Path]::GetFileNameWithoutExtension($Setup) + "-$Theme-$Lang")
"$Setup ($Theme) -> $Out"
$process = Start-Process -FilePath $Setup -ArgumentList "/LANG=$Lang", "/DIR=`"$dir`"" -PassThru
Start-Sleep -Seconds 3
# The plain look has no Welcome page (Inno's default); the others show it, with the tall picture.
if ($Setup -notmatch "plain") { Shot "welcome"; Press $next }
# Accept the license. In Spanish Alt+A is both "&Acepto" and "&Atrás" (Back): there the
# "&No acepto" button is focused with Alt+N and the arrow key moves to "Acepto", choosing it.
if ($Lang -eq "spanish") { Shot "license"; Press "%n"; Press "{UP}"; Press $next } else { Shot "license"; Press "%a"; Press $next }
Shot "folder"; Press $next
Shot "compare"; Press $next
Shot "components"; Press $next
Shot "tasks"; Press $next
Shot "ready"; Press "%i"
# Installing: the classic app alone (the default) takes a few seconds.
for ($i = 0; $i -lt 60 -and -not (Test-Path (Join-Path $dir "unins000.exe")); $i++) { Start-Sleep -Milliseconds 500 }
Start-Sleep -Seconds 3
Shot "finished"; Press "%f"
$process.WaitForExit(30000) | Out-Null

# The uninstaller, as from "Installed apps": its question, then its last message.
$uninstall = Start-Process -FilePath (Join-Path $dir "unins000.exe") -PassThru
Start-Sleep -Seconds 3
Shot "uninstall-confirm"; Press "{ENTER}"
Start-Sleep -Seconds 4
# Its last message may carry a title without "ClearMD"; then the foreground window is taken.
try { Shot "uninstall-done"; Press "{ENTER}" } catch { "  (no last message found: $_)"; [System.Windows.Forms.SendKeys]::SendWait("{ENTER}") }
$uninstall.WaitForExit(30000) | Out-Null
# unins000.exe hands over to a copy of itself in the temporary folder: wait until the program's
# folder is gone, so the next run starts clean (with an earlier install, Inno skips the folder page).
for ($i = 0; $i -lt 60 -and (Test-Path (Join-Path $dir "unins000.exe")); $i++) { Start-Sleep -Milliseconds 500 }
Start-Sleep -Seconds 2
exit 0
