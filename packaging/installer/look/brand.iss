; Option 1 of the installer's look: ClearMD's pictures and colours through Inno Setup's own
; directives (6.7 or newer). Included inside [Setup] by clearmd.iss when Look is brand or painted.
;
; "dynamic" follows Windows: light or dark, like the apps. "hidebevels" drops the grey lines.
WizardStyle=modern dynamic hidebevels
; The Welcome page is off by default in Inno; it is where the tall picture shows.
DisableWelcomePage=no
; The page background: the apps' working area ("ground") in each theme (frontend/design/palette.py).
; Setting it also turns on Inno's built-in "windows11" style in light mode.
WizardBackColor=#F3F5F7
WizardBackColorDynamicDark=#18212A
; The tall picture beside the Welcome and Finished pages; one file per DPI, Inno picks the closest.
; Drawn by tests/gui/make_installer_images.py, never by hand.
WizardImageFile=images\wizard-202.png,images\wizard-269.png,images\wizard-336.png,images\wizard-430.png
WizardImageFileDynamicDark=images\wizard-dark-202.png,images\wizard-dark-269.png,images\wizard-dark-336.png,images\wizard-dark-430.png
WizardImageBackColor=#1B2733
WizardImageBackColorDynamicDark=#0F161C
#if Look == "painted"
; Option 2 paints the header with the rail's ink in both themes: the bright mark fits both.
WizardSmallImageFile=images\small-dark-58.png,images\small-dark-77.png,images\small-dark-97.png,images\small-dark-124.png
WizardSmallImageFileDynamicDark=images\small-dark-58.png,images\small-dark-77.png,images\small-dark-97.png,images\small-dark-124.png
WizardSmallImageBackColor=#1B2733
WizardSmallImageBackColorDynamicDark=#0F161C
#else
; The mark in the top corner instead of Inno's box and disc: teal in light, the bright tones in dark.
WizardSmallImageFile=images\small-58.png,images\small-77.png,images\small-97.png,images\small-124.png
WizardSmallImageFileDynamicDark=images\small-dark-58.png,images\small-dark-77.png,images\small-dark-97.png,images\small-dark-124.png
WizardSmallImageBackColor=none
#endif
