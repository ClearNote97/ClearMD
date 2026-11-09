; ClearMD's Windows installer and uninstaller (feature 017, ADR-0040).
;
; Inno Setup 6 compiles this script into ClearMD-Setup-<version>.exe:
;     iscc /DAppVersion=0.12.0 packaging\installer\clearmd.iss
; Everything the installer writes is listed below, one section per kind of thing.
; Every section says what it does and why. Read packaging/installer/README.md for the whole picture.
;
; The file is saved as UTF-8 with a byte order mark: Inno Setup needs it for the Spanish texts.

; ---------------------------------------------------------------------------------------------
; Constants for the rest of the script. ExpandConstant-style {#Name} is replaced at compile time.
#define Root "..\.."  ; this file's folder is packaging\installer; the repository is two levels up
#ifndef AppVersion
  ; The build passes the real version (/DAppVersion=...). This fallback is for a local test build.
  #define AppVersion "0.0.0-local"
#endif
; The look (feature 019, ADR-0041): "painted", the default, is ClearMD's pictures and colours
; (look\brand.iss) plus the header, titles and cards painted with code (look\painted.iss);
; "brand" is the pictures and colours alone; "plain" is Inno's own look. Inno Setup 6.7 or newer.
#ifndef Look
  #define Look "painted"
#endif
; The edition (feature 037, ADR-0052; doubts board 2026-11-09, D1): one script, two installers.
; "Light" is ClearMD-Setup-<version>.exe, the Classic App alone (what most people need); "Full" is
; ClearMD-Setup-Full-<version>.exe, every part. It must be chosen: there is no default.
; The AppId's GUID once more, for the code that reads its uninstall key (a test keeps them equal).
#define AppGuid "F1E42AD8-D7EA-44E8-9355-95FC07D06CA5"
#ifndef Edition
  #error Pass /DEdition=Light or /DEdition=Full
#endif
#if Edition != "Light" && Edition != "Full"
  #error Edition must be Light or Full
#endif

; ---------------------------------------------------------------------------------------------
[Setup]
; AppId identifies the program for Windows. It is FIXED: a newer installer with the same AppId
; replaces the older one in place (same folder, same "Installed apps" entry). Never change it.
; The double braces are Inno's way of writing one literal "{" (the GUID's own braces).
AppId={{F1E42AD8-D7EA-44E8-9355-95FC07D06CA5}
AppName=ClearMD
AppVersion={#AppVersion}
AppVerName=ClearMD {#AppVersion}
AppPublisher=ClearNote97
AppPublisherURL=https://github.com/ClearNote97/ClearMD
; Per user, no administrator: the program goes to the user's own folder, so no UAC prompt.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\ClearMD
; The Start menu folder is "ClearMD"; the wizard does not ask for a folder name.
DefaultGroupName=ClearMD
DisableProgramGroupPage=yes
; The license page (MIT). The user must accept it to continue.
LicenseFile={#Root}\LICENSE
; The icon of the installer window, and the icon of the entry in "Installed apps" (below).
SetupIconFile={#Root}\src\clearmd\frontend\assets\logo\clearmd.ico
UninstallDisplayIcon={app}\clearmd.ico
UninstallDisplayName=ClearMD
; Where the installer is written, and its file name: ClearMD-Setup-<version>.exe.
OutputDir=..\..\dist\installer
#if Edition == "Full"
OutputBaseFilename=ClearMD-Setup-Full-{#AppVersion}
#else
OutputBaseFilename=ClearMD-Setup-{#AppVersion}
#endif
Compression=lzma2
SolidCompression=yes
#if Look == "plain"
WizardStyle=modern
#else
  #include "look\brand.iss"
#endif
; Windows 10 or newer (the Python runtime inside the programs needs it).
MinVersion=10.0
; If ClearMD is open when the installer starts, Windows' Restart Manager lists it and asks the
; user to close it first (AC-04: the installer says so). It does not restart the apps afterwards.
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no
; Tells Windows the environment variables (the PATH option below) may have changed, so new
; terminals see them. Without it a PATH change only shows after a sign-out.
ChangesEnvironment=yes

; ---------------------------------------------------------------------------------------------
[Languages]
; The wizard speaks the system's language when it is English or Spanish; English otherwise.
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

; ---------------------------------------------------------------------------------------------
[Messages]
; Titles are written in Title Case (every word capitalised except connectors): Inno's English
; titles already are; these two Spanish ones are not, so they are replaced here.
spanish.WelcomeLabel1=Bienvenido al Asistente de Instalación de [name]
spanish.FinishedHeadingLabel=Completando la Instalación de [name]
#if Edition == "Light"
; The light edition says where the other apps are (doubts board D1).
english.FinishedLabel=Setup has finished installing [name] on your computer. It can be opened from its shortcut.%n%nWant the Modern App or the Mobile-Style App? They are in ClearMD-Setup-Full-{#AppVersion}.exe, on the same download page.
spanish.FinishedLabel=El programa terminó de instalar [name] en tu equipo. Puedes abrirlo desde su acceso directo.%n%n¿Quieres la App Moderna o la App Estilo Móvil? Están en ClearMD-Setup-Full-{#AppVersion}.exe, en la misma página de descarga.
#endif

; ---------------------------------------------------------------------------------------------
[CustomMessages]
; Our own texts, one line per message, in each language. In the Pascal code they are read with
; CustomMessage('Name'); in the other sections with {cm:Name}.
english.TypeTtk=Only the classic app (recommended: the lightest)
english.TypeQt=Only the modern app
english.TypeFlet=Only the mobile-style app
english.TypeCli=Only the command line
english.TypeFull=Everything: the three apps and the command line
english.TypeCustom=Custom: I choose each part
spanish.TypeTtk=Solo la app clásica (recomendada: la más liviana)
spanish.TypeQt=Solo la app moderna
spanish.TypeFlet=Solo la app estilo móvil
spanish.TypeCli=Solo la línea de comandos
spanish.TypeFull=Todo: las tres apps y la línea de comandos
spanish.TypeCustom=Personalizada: elijo cada parte

english.CompTtk=Classic App (Recommended)
english.CompQt=Modern App
english.CompFlet=Mobile-Style App
english.CompCli=Command Line (For Advanced Users)
spanish.CompTtk=App Clásica (Recomendada)
spanish.CompQt=App Moderna
spanish.CompFlet=App Estilo Móvil
spanish.CompCli=Línea de Comandos (Para Usuarios Avanzados)

english.TaskDesktop=A desktop shortcut for each part I chose
spanish.TaskDesktop=Un acceso directo en el escritorio para cada parte que elegí
english.TaskAddPath=Add the command line to my PATH, so that clearmd-cli works in any terminal (this changes your user's PATH; the uninstaller removes it)
spanish.TaskAddPath=Añadir la línea de comandos a mi PATH, para que clearmd-cli funcione en cualquier terminal (esto cambia el PATH de tu usuario; el desinstalador lo quita)

english.CompareCaption=What Each Part Is
spanish.CompareCaption=Qué Es Cada Parte
english.CompareDescription=Read this, then choose on the next page. You can run the installer again later to change your choice.
spanish.CompareDescription=Léelo y elige en la página siguiente. Puedes volver a ejecutar el instalador más adelante para cambiar tu elección.
english.CompareTtk=The Classic App (RECOMMENDED for most people: the lightest). One program file of about 37 MB. The first start takes a few seconds, because the program unpacks itself. Simpler drawing. Made with Tk.
spanish.CompareTtk=La App Clásica (RECOMENDADA para la mayoría: la más liviana). Un solo archivo de unos 37 MB. El primer inicio tarda unos segundos, porque el programa se descomprime solo. Dibujo más sencillo. Hecha con Tk.
english.CompareQt=The Modern App: it looks smoother, with sharper text and controls on high-resolution screens, and it opens quickly. The price is space: a folder of about 130 MB. Made with Qt, whose libraries can be replaced (LGPL).
english.CompareFlet=The Mobile-Style App: drawn like phone apps, smooth, and it opens quickly; files are added with its two buttons (it cannot receive files dragged onto it). A folder of about 120 MB. Made with Flutter (flet).
spanish.CompareFlet=La App Estilo Móvil: dibujada como las apps de teléfono, suave, y abre rápido; los archivos se añaden con sus dos botones (no recibe archivos arrastrados). Una carpeta de unos 120 MB. Hecha con Flutter (flet).
spanish.CompareQt=La App Moderna: se ve más suave, con texto y controles más nítidos en pantallas de alta resolución, y abre rápido. El costo es el espacio: una carpeta de unos 130 MB. Hecha con Qt, cuyas bibliotecas se pueden reemplazar (LGPL).
english.CompareCli=The Command Line: no window. You type a command, for example clearmd-cli "C:\My documents". Good for many folders, scripts and automation. Needs typing. About 36 MB.
spanish.CompareCli=La Línea de Comandos: sin ventana. Escribes un comando, por ejemplo clearmd-cli "C:\Mis documentos". Buena para muchas carpetas, scripts y automatización. Requiere escribir. Unos 36 MB.
english.CompareAll=All of them do exactly the same conversions, with the same results.
spanish.CompareAll=Todas hacen exactamente las mismas conversiones, con los mismos resultados.

english.NeedOneComponent=Choose at least one part: the classic app, the modern app, the mobile-style app or the command line.
spanish.NeedOneComponent=Elige al menos una parte: la app clásica, la app moderna, la app estilo móvil o la línea de comandos.

english.ShortcutQt=ClearMD Modern App
english.ShortcutFlet=ClearMD Mobile-Style App
english.ShortcutCli=ClearMD Command Line
spanish.ShortcutQt=ClearMD App Moderna
spanish.ShortcutFlet=ClearMD App Estilo Móvil
spanish.ShortcutCli=ClearMD Línea de Comandos

english.LightHasOtherParts=You also have other parts of ClearMD installed (the Modern App, the Mobile-Style App or the Command Line). This file updates only the Classic App, so nothing was changed. To update everything, download and run ClearMD-Setup-Full-%1.exe from the same page.
spanish.LightHasOtherParts=También tienes instaladas otras partes de ClearMD (la App Moderna, la App Estilo Móvil o la Línea de Comandos). Este archivo actualiza solo la App Clásica, así que no se cambió nada. Para actualizar todo, descarga y ejecuta ClearMD-Setup-Full-%1.exe desde la misma página.

english.RemoveSettings=Also delete ClearMD's settings in%n%n%1%n%nYour documents and your ClearMD_Output folders are never touched.
spanish.RemoveSettings=¿Borrar también la configuración de ClearMD en%n%n%1%n%nTus documentos y tus carpetas ClearMD_Output nunca se tocan.

; ---------------------------------------------------------------------------------------------
[Types]
; A "type" is a ready-made choice on the first wizard page. The first one (the classic app, the
; lightest) is the default: a silent install with no /TYPE or /COMPONENTS installs only that one.
Name: "ttkonly"; Description: "{cm:TypeTtk}"
#if Edition == "Full"
Name: "qtonly"; Description: "{cm:TypeQt}"
Name: "fletonly"; Description: "{cm:TypeFlet}"
Name: "clionly"; Description: "{cm:TypeCli}"
Name: "full"; Description: "{cm:TypeFull}"
Name: "custom"; Description: "{cm:TypeCustom}"; Flags: iscustom
#endif

; ---------------------------------------------------------------------------------------------
[Components]
; A "component" is one part of the program. Only the chosen components get files and shortcuts.
; Types: the types in which the component is ticked. The classic app is ticked by "ttkonly" (the
; default) and "custom"; the modern app and the command line are ticked only by their own type and
; by "full". In "custom" the user ticks what he wants; the components not in its list start unticked.
#if Edition == "Full"
Name: "ttk"; Description: "{cm:CompTtk}"; Types: ttkonly full custom
Name: "qt"; Description: "{cm:CompQt}"; Types: qtonly full
Name: "flet"; Description: "{cm:CompFlet}"; Types: fletonly full
Name: "cli"; Description: "{cm:CompCli}"; Types: clionly full
#else
; The light edition has one part, always installed: its page of choices is skipped ([Code]).
Name: "ttk"; Description: "{cm:CompTtk}"; Types: ttkonly; Flags: fixed
#endif

; ---------------------------------------------------------------------------------------------
[Tasks]
; Tasks are yes/no questions. "unchecked" means off unless the user ticks it: nothing that
; changes the user's desktop or environment happens by default.
Name: "desktopicon"; Description: "{cm:TaskDesktop}"; Flags: unchecked
; Only shown when the command line is chosen: it changes the user's PATH (see [Code]).
#if Edition == "Full"
Name: "addpath"; Description: "{cm:TaskAddPath}"; Components: cli; Flags: unchecked
#endif

; ---------------------------------------------------------------------------------------------
[Files]
; What is copied, from the build folder (dist\ at the repository root) to the install folder.
; The icon and the license are always installed, whatever is chosen: "Installed apps" and the
; license travel with the program. Each program only with its component.
Source: "{#Root}\src\clearmd\frontend\assets\logo\clearmd.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Root}\dist\installer\THIRD-PARTY-NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion
; The classic app: a folder since 2.11 (ADR-0053), its program and its _internal\ files, so it
; does not unpack itself at every start. The one-file ClearMD.exe stays the portable download.
Source: "{#Root}\dist\ClearMD-Classic\*"; DestDir: "{app}"; Components: ttk; Flags: ignoreversion recursesubdirs createallsubdirs
#if Edition == "Full"
; The modern app: a folder. Its Qt libraries stay plain files (LGPL: the user may replace them).
; recursesubdirs + createallsubdirs copy the whole tree, keeping its folders.
Source: "{#Root}\dist\ClearMD-Qt\*"; DestDir: "{app}\ClearMD-Qt"; Components: qt; Flags: ignoreversion recursesubdirs createallsubdirs
; The license and notices travel with the Qt libraries too (the LGPL asks for it).
Source: "{#Root}\LICENSE"; DestDir: "{app}\ClearMD-Qt"; Components: qt; Flags: ignoreversion
Source: "{#Root}\dist\installer\THIRD-PARTY-NOTICES.txt"; DestDir: "{app}\ClearMD-Qt"; Components: qt; Flags: ignoreversion
; The flet app: a folder too, with flet's window program inside (flet-client\, ADR-0042).
Source: "{#Root}\dist\ClearMD-Flet\*"; DestDir: "{app}\ClearMD-Flet"; Components: flet; Flags: ignoreversion recursesubdirs createallsubdirs
; The command line: one console program.
Source: "{#Root}\dist\clearmd-cli.exe"; DestDir: "{app}"; Components: cli; Flags: ignoreversion
#endif

; ---------------------------------------------------------------------------------------------
[Icons]
; Shortcuts. {group} is the Start menu folder "ClearMD"; {autodesktop} is the desktop.
; The classic and modern apps open directly.
Name: "{group}\ClearMD"; Filename: "{app}\ClearMD.exe"; Components: ttk
#if Edition == "Full"
Name: "{group}\{cm:ShortcutQt}"; Filename: "{app}\ClearMD-Qt\ClearMD-Qt.exe"; WorkingDir: "{app}\ClearMD-Qt"; Components: qt
Name: "{group}\{cm:ShortcutFlet}"; Filename: "{app}\ClearMD-Flet\ClearMD-Flet.exe"; WorkingDir: "{app}\ClearMD-Flet"; Components: flet
; The command line must NOT open clearmd-cli.exe directly: a console program started by a double
; click closes at once. Instead it opens cmd.exe (the Windows command prompt) in the user's
; Documents folder, shows the help, and leaves the prompt open to use the program.
; Quoting: in an Inno string every double quote is written twice (""). The command cmd runs is:
;   "C:\...\clearmd-cli.exe" --help & echo. & echo Type: clearmd-cli "<folder or file>"
; wrapped in one more pair of quotes after /k (cmd's rule for /k).
Name: "{group}\{cm:ShortcutCli}"; Filename: "{cmd}"; Parameters: "/k """"{app}\clearmd-cli.exe"" --help & echo. & echo Type: clearmd-cli ""<folder or file>"""""; WorkingDir: "{userdocs}"; Components: cli
#endif
; The uninstaller in the Start menu. Inno would create it anyway; naming it here keeps it explicit.
Name: "{group}\{cm:UninstallProgram,ClearMD}"; Filename: "{uninstallexe}"
; Desktop shortcuts: only when the task is ticked, and only for the components chosen.
Name: "{autodesktop}\ClearMD"; Filename: "{app}\ClearMD.exe"; Components: ttk; Tasks: desktopicon
#if Edition == "Full"
Name: "{autodesktop}\{cm:ShortcutQt}"; Filename: "{app}\ClearMD-Qt\ClearMD-Qt.exe"; WorkingDir: "{app}\ClearMD-Qt"; Components: qt; Tasks: desktopicon
Name: "{autodesktop}\{cm:ShortcutFlet}"; Filename: "{app}\ClearMD-Flet\ClearMD-Flet.exe"; WorkingDir: "{app}\ClearMD-Flet"; Components: flet; Tasks: desktopicon
Name: "{autodesktop}\{cm:ShortcutCli}"; Filename: "{cmd}"; Parameters: "/k """"{app}\clearmd-cli.exe"" --help & echo. & echo Type: clearmd-cli ""<folder or file>"""""; WorkingDir: "{userdocs}"; Components: cli; Tasks: desktopicon
#endif

; ---------------------------------------------------------------------------------------------
[InstallDelete]
; Runs before the new files are copied. Re-running the installer with a different choice must
; remove what an earlier install put in place for the parts that are now NOT chosen (Inno does
; not do that by itself). Each entry is removed only when its component is unticked (Check:).
; The folders named here are ClearMD's own; nothing else in the install folder is named.
Type: files; Name: "{app}\ClearMD.exe"; Check: NotTtk
Type: filesandordirs; Name: "{app}\_internal"; Check: NotTtk
Type: files; Name: "{group}\ClearMD.lnk"; Check: NotTtk
Type: files; Name: "{autodesktop}\ClearMD.lnk"; Check: NotTtk
#if Edition == "Full"
; Never in the light edition: it refuses to run over the other parts instead ([Code], D1).
Type: filesandordirs; Name: "{app}\ClearMD-Qt"; Check: NotQt
Type: filesandordirs; Name: "{app}\ClearMD-Flet"; Check: NotFlet
Type: files; Name: "{app}\clearmd-cli.exe"; Check: NotCli
#endif
; The other parts' shortcuts, under every name they have had (2.8.1's and today's, in both
; languages), always: [Icons] then creates only the chosen ones, in this install's language
; (doubts board 2026-11-09, D2). Their folders keep their Check: above.
Type: files; Name: "{group}\ClearMD (Qt).lnk"
Type: files; Name: "{autodesktop}\ClearMD (Qt).lnk"
Type: files; Name: "{group}\ClearMD (flet).lnk"
Type: files; Name: "{autodesktop}\ClearMD (flet).lnk"
Type: files; Name: "{group}\ClearMD (command line).lnk"
Type: files; Name: "{autodesktop}\ClearMD (command line).lnk"
Type: files; Name: "{group}\ClearMD Modern App.lnk"
Type: files; Name: "{autodesktop}\ClearMD Modern App.lnk"
Type: files; Name: "{group}\ClearMD Mobile-Style App.lnk"
Type: files; Name: "{autodesktop}\ClearMD Mobile-Style App.lnk"
Type: files; Name: "{group}\ClearMD Command Line.lnk"
Type: files; Name: "{autodesktop}\ClearMD Command Line.lnk"
Type: files; Name: "{group}\ClearMD App Moderna.lnk"
Type: files; Name: "{autodesktop}\ClearMD App Moderna.lnk"
Type: files; Name: "{group}\ClearMD App Estilo Móvil.lnk"
Type: files; Name: "{autodesktop}\ClearMD App Estilo Móvil.lnk"
Type: files; Name: "{group}\ClearMD Línea de Comandos.lnk"
Type: files; Name: "{autodesktop}\ClearMD Línea de Comandos.lnk"

; ---------------------------------------------------------------------------------------------
; [UninstallDelete] is not used: the apps write nothing into the install folder (PyInstaller's
; one-file program unpacks into the temporary folder, not here). If that ever changes, add an
; entry here so the uninstaller removes it too.

; ---------------------------------------------------------------------------------------------
#if Look == "painted"
  #include "look\painted.iss"
#endif
[Code]
// The Pascal Script part: the logic Inno's sections cannot express alone. Comments use //.

const
  PathKey = 'Environment';                  // HKCU\Environment: the user's own PATH
  MarkerKey = 'Software\ClearMD';           // remembers the PATH entry this installer added
  MarkerValue = 'PathEntry';

var
  ComparePage: TWizardPage;                 // the page that explains the three parts

// ---- Choices, read by [InstallDelete] (Check:) -------------------------------------------------

function NotTtk: Boolean;
begin
  // True when the classic app is NOT chosen: its old files are then removed before copying.
  Result := not WizardIsComponentSelected('ttk');
end;

#if Edition == "Full"
function NotQt: Boolean;
begin
  Result := not WizardIsComponentSelected('qt');
end;

function NotFlet: Boolean;
begin
  Result := not WizardIsComponentSelected('flet');
end;

function NotCli: Boolean;
begin
  Result := not WizardIsComponentSelected('cli');
end;
#endif

// ---- The wizard -------------------------------------------------------------------------------

procedure InitializeWizard;
var
  Memo: TNewMemo;
  Body: String;
begin
#if Edition == "Light"
  // One part only: no page that compares the parts (the full edition has it).
  #if Look == "painted"
  PaintWizard;
  #endif
  Exit;
#endif
  // A page of its own, between "Where to install" and "Components": the explanation is read
  // before the choice. It is skipped in a silent install (there is nothing to read then).
  ComparePage := CreateCustomPage(wpSelectDir, CustomMessage('CompareCaption'), CustomMessage('CompareDescription'));
#if Look == "painted"
  // Option 2: one card per part instead of the plain text, and ClearMD's colours (look\painted.iss).
  PaintCompareCards(ComparePage);
  PaintWizard;
  Exit;
#endif
  Memo := TNewMemo.Create(WizardForm);
  Memo.Parent := ComparePage.Surface;
  Memo.Align := alClient;
  Memo.ReadOnly := True;
  Memo.WordWrap := True;
  Memo.ScrollBars := ssVertical;
  Body := CustomMessage('CompareTtk') + #13#10 + #13#10 + CustomMessage('CompareQt') + #13#10 + #13#10 +
    CustomMessage('CompareFlet') + #13#10 + #13#10 +
    CustomMessage('CompareCli') + #13#10 + #13#10 + CustomMessage('CompareAll');
  Memo.Text := Body;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
#if Edition == "Full"
  // At least one part must be chosen: an installer with nothing in it would be pointless.
  if CurPageID = wpSelectComponents then
    if not (WizardIsComponentSelected('ttk') or WizardIsComponentSelected('qt') or WizardIsComponentSelected('flet') or WizardIsComponentSelected('cli')) then
    begin
      MsgBox(CustomMessage('NeedOneComponent'), mbError, MB_OK);
      Result := False;
    end;
#endif
end;

#if Edition == "Light"
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  // The light edition has one fixed part: its page of choices says nothing.
  Result := PageID = wpSelectComponents;
end;

function InitializeSetup: Boolean;
var
  Parts: String;
begin
  // Never over the other parts (doubts board 2026-11-09, D1): someone who has the Modern App, the
  // Mobile-Style App or the Command Line is told which file updates everything, and nothing is
  // changed. Silent: the same, with an exit code that is not 0.
  Result := True;
  if RegQueryStringValue(HKA, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{' + '{#AppGuid}' + '}_is1',
      'Inno Setup: Selected Components', Parts) then
    if (Pos('qt', Parts) > 0) or (Pos('flet', Parts) > 0) or (Pos('cli', Parts) > 0) then
    begin
      SuppressibleMsgBox(FmtMessage(CustomMessage('LightHasOtherParts'), ['{#AppVersion}']), mbInformation, MB_OK, IDOK);
      Result := False;
    end;
end;
#endif

// ---- The PATH option (the command line only) --------------------------------------------------
// The user's PATH is a list of folders separated by ";". The installer adds its folder once, and
// remembers that it did (a marker in HKCU\Software\ClearMD). The uninstaller and a re-install
// without the option remove exactly that one entry, and only when the marker says it was added
// by this installer: a folder that was on the PATH before is never removed.

function SplitPath(Path: String): TStringList;
var
  Position: Integer;
  Entry: String;
begin
  Result := TStringList.Create;
  while Path <> '' do
  begin
    Position := Pos(';', Path);
    if Position = 0 then
    begin
      Entry := Path;
      Path := '';
    end
    else
    begin
      Entry := Copy(Path, 1, Position - 1);
      Path := Copy(Path, Position + 1, Length(Path) - Position);
    end;
    if Entry <> '' then Result.Add(Entry);
  end;
end;

function SameFolder(A, B: String): Boolean;
begin
  // "C:\X\" and "C:\X" are the same folder for the PATH.
  Result := SameText(RemoveBackslash(A), RemoveBackslash(B));
end;

function JoinPath(List: TStringList): String;
var
  I: Integer;
begin
  Result := '';
  for I := 0 to List.Count - 1 do
  begin
    if I > 0 then Result := Result + ';';
    Result := Result + List.Strings[I];
  end;
end;

procedure AddOwnPathEntry;
var
  OldPath, NewPath, Dir: String;
  List: TStringList;
  I: Integer;
  Present: Boolean;
begin
  Dir := ExpandConstant('{app}');
  OldPath := '';
  RegQueryStringValue(HKEY_CURRENT_USER, PathKey, 'Path', OldPath);
  List := SplitPath(OldPath);
  Present := False;
  for I := 0 to List.Count - 1 do
    if SameFolder(List.Strings[I], Dir) then Present := True;
  if not Present then
  begin
    // Appended at the end, so nothing already on the PATH changes its place or meaning.
    List.Add(Dir);
    NewPath := JoinPath(List);
    // Expandable string: the PATH is stored that way by Windows.
    RegWriteExpandStringValue(HKEY_CURRENT_USER, PathKey, 'Path', NewPath);
    // Remember that this installer added it (not if it was already there).
    RegWriteStringValue(HKEY_CURRENT_USER, MarkerKey, MarkerValue, Dir);
  end;
  List.Free;
end;

procedure RemoveOwnPathEntry;
var
  Marker, OldPath: String;
  List: TStringList;
  I: Integer;
begin
  // Nothing to do unless this installer added the entry.
  if not RegQueryStringValue(HKEY_CURRENT_USER, MarkerKey, MarkerValue, Marker) then Exit;
  OldPath := '';
  RegQueryStringValue(HKEY_CURRENT_USER, PathKey, 'Path', OldPath);
  List := SplitPath(OldPath);
  // Walk backwards so that deleting an entry does not shift the ones still to be looked at.
  for I := List.Count - 1 downto 0 do
    if SameFolder(List.Strings[I], Marker) then List.Delete(I);
  RegWriteExpandStringValue(HKEY_CURRENT_USER, PathKey, 'Path', JoinPath(List));
  List.Free;
  RegDeleteValue(HKEY_CURRENT_USER, MarkerKey, MarkerValue);
  RegDeleteKeyIfEmpty(HKEY_CURRENT_USER, MarkerKey);
end;

// ---- Install: runs after the files are copied -------------------------------------------------

procedure SpeakTheWizardsLanguage;
var
  Folder, FileName: String;
begin
  // A first install in Spanish opens the app in Spanish (audit 2026-11-08, C-1): the person
  // already chose the language in this wizard. English stays the default elsewhere (ADR-0017),
  // and a settings file that exists is never touched.
  if ActiveLanguage <> 'spanish' then Exit;
  Folder := ExpandConstant('{localappdata}\ClearMD');
  FileName := Folder + '\settings.toml';
  if FileExists(FileName) then Exit;
  ForceDirectories(Folder);
  SaveStringToFile(FileName, 'language = "es"' + #13#10, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    SpeakTheWizardsLanguage;
#if Edition == "Full"
    // The PATH follows the choice on every install: added when the option is ticked, removed when
    // it is not (a re-install without the command line must not leave its folder on the PATH).
    if WizardIsComponentSelected('cli') and WizardIsTaskSelected('addpath') then
      AddOwnPathEntry
    else
      RemoveOwnPathEntry;
#endif
  end;
end;

// ---- Uninstall --------------------------------------------------------------------------------

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Folder: String;
  Remove: Boolean;
begin
  if CurUninstallStep = usUninstall then
    RemoveOwnPathEntry;   // before the files go: the PATH is ClearMD's to undo

  if CurUninstallStep = usPostUninstall then
  begin
    // The settings folder is the user's, not the program's: it is kept unless the user says
    // otherwise. Silent uninstall: kept, unless the command was run with /REMOVESETTINGS.
    // Only this one folder is ever deleted; the documents and ClearMD_Output folders are not in it.
    Folder := ExpandConstant('{localappdata}\ClearMD');
    if DirExists(Folder) then
    begin
      if UninstallSilent then
        Remove := Pos('/REMOVESETTINGS', Uppercase(GetCmdTail)) > 0
      else
        Remove := MsgBox(FmtMessage(CustomMessage('RemoveSettings'), [Folder]), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
      if Remove then DelTree(Folder, True, True, True);
    end;
  end;
end;
