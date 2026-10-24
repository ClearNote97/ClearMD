# ADR-0003: PySide6-Essentials en vez de PyQt6

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

Una de las tres GUIs de ClearMD usa Qt. En Python hay dos bindings maduros de Qt 6, con la misma librería
por debajo y APIs casi idénticas, pero con licencias distintas (verificado en PyPI el 2026-10-24):

| Binding | Versión | Licencia |
|---|---|---|
| PyQt6 (Riverbank) | 6.11.0 | GPL-3.0-only, o licencia comercial de pago |
| PySide6 (The Qt Company) | 6.12.0 | LGPL-3.0-only o GPL-2.0/3.0 |

ClearMD se publica con licencia **MIT** (`LICENSE`) y se distribuye como ejecutable.

## Decisión

Usar **`PySide6-Essentials`**, no PyQt6, y no el metapaquete `PySide6`.

- PyQt6 obligaría a relicenciar toda la app como GPL o a pagar una licencia comercial. PySide6, bajo LGPL,
  es compatible con distribuir una app MIT.
- El metapaquete `PySide6` arrastra `PySide6_Addons`, `PySide6_WebEngine` y `PySide6_Pdf`, que ClearMD no usa.
  `PySide6-Essentials` trae solo los módulos base (wheel de ~82 MB en Windows y Linux).

## Consecuencias

- **Se gana:** licencia compatible con MIT, sin costo; ejecutable más liviano que con el metapaquete.
- **Se paga:** la LGPL exige que el usuario pueda reemplazar las librerías de Qt. Por eso el ejecutable de la
  GUI Qt se distribuye en modo carpeta (*onedir*) y no como un único `.exe` (*onefile*). Hay menos tutoriales
  de PySide6 que de PyQt, aunque la API es prácticamente la misma.

## Alternativas consideradas

- **PyQt6 con la app bajo GPL:** descartada; cambiaría la licencia de todo el proyecto por una sola GUI.
- **Metapaquete `PySide6`:** descartado por tamaño.
