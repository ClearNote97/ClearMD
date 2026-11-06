; Option 2 of the installer's look: Pascal code that paints ClearMD's colours onto Inno's own
; controls, on top of option 1 (brand.iss). Included by clearmd.iss just before its [Code] when
; Look is painted. Windows draws the buttons and the check list itself: those stay native.

[CustomMessages]
english.CardTtkTitle=ClearMD (ttk) - The Classic App
english.CardTtkTag=RECOMMENDED · about 36 MB
english.CardTtkBody=The lightest: one program file. The first start takes a few seconds, while it unpacks itself.
english.CardQtTitle=ClearMD (Qt) - The Modern App
english.CardQtTag=about 130 MB
english.CardQtBody=Smoother, with sharper text on high-resolution screens, and it opens quickly. Its Qt libraries can be replaced (LGPL).
english.CardCliTitle=Command Line - For Advanced Users
english.CardCliTag=about 36 MB
english.CardCliBody=No window: you type clearmd-cli "C:\My documents". Good for many folders, scripts and automation.
spanish.CardTtkTitle=ClearMD (ttk) - La App Clásica
spanish.CardTtkTag=RECOMENDADA · unos 36 MB
spanish.CardTtkBody=La más liviana: un solo archivo. El primer inicio tarda unos segundos, mientras se descomprime.
spanish.CardQtTitle=ClearMD (Qt) - La App Moderna
spanish.CardQtTag=unos 130 MB
spanish.CardQtBody=Más suave, con texto más nítido en pantallas de alta resolución, y abre rápido. Sus bibliotecas de Qt se pueden reemplazar (LGPL).
spanish.CardCliTitle=Línea de Comandos - Para Usuarios Avanzados
spanish.CardCliTag=unos 36 MB
spanish.CardCliBody=Sin ventana: escribes clearmd-cli "C:\Mis documentos". Buena para muchas carpetas, scripts y automatización.

[Code]
// ---- ClearMD's colours (frontend/design/palette.py), light and dark ---------------------------

function Tone(Light, Dark: String): TColor;
begin
  // IsDarkInstallMode: true when Windows is dark ("dynamic" follows it).
  if IsDarkInstallMode then
    Result := StrToColor(Dark)
  else
    Result := StrToColor(Light);
end;

procedure OwnBackground(Control: TControl);
begin
  // A style (light "windows11" or the dark one) repaints every control; this tells it to leave
  // this control's background to us.
  Control.StyleElements := Control.StyleElements - [seClient];
end;

procedure Ink(Text: TNewStaticText; Colour: TColor; Size: Integer; Bold: Boolean);
begin
  // Only the letters' colour is taken from the style (seFont). The background must stay with it:
  // without the style's painter, Windows draws the text of a see-through label in black.
  Text.StyleElements := Text.StyleElements - [seFont];
  Text.Font.Color := Colour;
  if Size > 0 then Text.Font.Size := Size;
  if Bold then Text.Font.Style := [fsBold] else Text.Font.Style := [];
end;

function Block(Parent: TWinControl; Colour: TColor; Left, Top, Width, Height: Integer): TPanel;
begin
  // A flat rectangle of one colour: the header, the accent line, a card and its border.
  Result := TPanel.Create(WizardForm);
  Result.Parent := Parent;
  Result.BevelOuter := bvNone;
  Result.ParentBackground := False;
  OwnBackground(Result);
  Result.Color := Colour;
  Result.SetBounds(Left, Top, Width, Height);
end;

// ---- The header: the rail's ink, as the apps' side rail, with a teal line under it -------------

procedure PaintHeader;
var
  Panel: TPanel;
begin
  Panel := WizardForm.MainPanel;
  Panel.ParentBackground := False;
  OwnBackground(Panel);
  Panel.Color := Tone('#1B2733', '#0F161C');
  Ink(WizardForm.PageNameLabel, StrToColor('#F3F5F7'), 0, True);
  Ink(WizardForm.PageDescriptionLabel, StrToColor('#A9B4BE'), 0, False);
  // The teal line belongs to the inner pages (the header's own page), not to Welcome or Finished.
  Block(WizardForm.InnerPage, Tone('#0D9488', '#2DD4BF'), 0, Panel.Top + Panel.Height, Panel.Width, ScaleY(3));
end;

// ---- The Welcome and Finished pages: the title in the brand's teal ------------------------------

procedure PaintTitles;
begin
  Ink(WizardForm.WelcomeLabel1, Tone('#0F766E', '#5EEAD4'), 0, True);
  Ink(WizardForm.FinishedHeadingLabel, Tone('#0F766E', '#5EEAD4'), 0, True);
  WizardForm.AdjustLabelHeight(WizardForm.WelcomeLabel1);
  WizardForm.AdjustLabelHeight(WizardForm.FinishedHeadingLabel);
end;

// ---- The comparison page: one card per part, like the apps' cards -------------------------------

function Card(Page: TWizardPage; Top: Integer; Title, Tag, Body: String; Recommended: Boolean): Integer;
var
  Border, Face: TPanel;
  TitleText, TagText, BodyText: TNewStaticText;
  Pad, Accent, Width: Integer;
begin
  Pad := ScaleX(10);
  Accent := 0;
  if Recommended then Accent := ScaleX(4);
  Width := Page.SurfaceWidth;
  // The border is a panel one pixel larger than the card's face; the recommended card gets a
  // teal edge on the left, as the current step has in the apps.
  Border := Block(Page.Surface, Tone('#DCE2E7', '#2E3B47'), 0, Top, Width, ScaleY(60));
  if Recommended then Block(Border, Tone('#0F766E', '#2DD4BF'), 0, 0, Accent, ScaleY(60));
  Face := Block(Border, Tone('#FFFFFF', '#202B36'), Accent + 1, 1, Width - Accent - 2, ScaleY(58));

  TagText := TNewStaticText.Create(WizardForm);
  TagText.Parent := Face;
  TagText.Caption := Tag;
  TagText.AutoSize := True;
  if Recommended then
    Ink(TagText, Tone('#0F766E', '#5EEAD4'), 0, True)
  else
    Ink(TagText, Tone('#5B6672', '#A3AEB8'), 0, False);
  TagText.Top := Pad;
  TagText.Left := Face.Width - TagText.Width - Pad;

  TitleText := TNewStaticText.Create(WizardForm);
  TitleText.Parent := Face;
  TitleText.Caption := Title;
  TitleText.AutoSize := True;
  Ink(TitleText, Tone('#1B2733', '#E6EBEF'), 0, True);
  TitleText.SetBounds(Pad, Pad, TagText.Left - 2 * Pad, TitleText.Height);

  BodyText := TNewStaticText.Create(WizardForm);
  BodyText.Parent := Face;
  BodyText.AutoSize := False;
  BodyText.WordWrap := True;
  BodyText.Caption := Body;
  Ink(BodyText, Tone('#5B6672', '#A3AEB8'), 0, False);
  BodyText.SetBounds(Pad, TitleText.Top + TitleText.Height + ScaleY(4), Face.Width - 2 * Pad, ScaleY(30));
  BodyText.AdjustHeight;

  // The card grows to its text.
  Face.Height := BodyText.Top + BodyText.Height + Pad;
  Border.Height := Face.Height + 2;
  if Recommended then Border.Controls[0].Height := Border.Height;
  Result := Top + Border.Height + ScaleY(8);
end;

procedure PaintCompareCards(Page: TWizardPage);
var
  Top: Integer;
  Note: TNewStaticText;
begin
  Top := Card(Page, 0, CustomMessage('CardTtkTitle'), CustomMessage('CardTtkTag'), CustomMessage('CardTtkBody'), True);
  Top := Card(Page, Top, CustomMessage('CardQtTitle'), CustomMessage('CardQtTag'), CustomMessage('CardQtBody'), False);
  Top := Card(Page, Top, CustomMessage('CardCliTitle'), CustomMessage('CardCliTag'), CustomMessage('CardCliBody'), False);
  Note := TNewStaticText.Create(WizardForm);
  Note.Parent := Page.Surface;
  Note.AutoSize := False;
  Note.WordWrap := True;
  Note.Caption := CustomMessage('CompareAll');
  Ink(Note, Tone('#0F766E', '#5EEAD4'), 0, False);
  Note.SetBounds(0, Top, Page.SurfaceWidth, ScaleY(16));
  Note.AdjustHeight;
end;

// ---- The check list of parts: the card's colour, the chosen ones in bold ------------------------

procedure PaintComponents;
begin
  OwnBackground(WizardForm.ComponentsList);
  WizardForm.ComponentsList.StyleElements := WizardForm.ComponentsList.StyleElements - [seFont];
  WizardForm.ComponentsList.Color := Tone('#FFFFFF', '#202B36');
  WizardForm.ComponentsList.Font.Color := Tone('#1B2733', '#E6EBEF');
end;

procedure PaintWizard;
begin
  PaintHeader;
  PaintTitles;
  PaintComponents;
end;
