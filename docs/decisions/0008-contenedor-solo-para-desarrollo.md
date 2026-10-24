# ADR-0008: El contenedor es para desarrollo; los ejecutables salen de CI

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

El contrato de trabajo (`README_AGENTS.md`) ejecuta todo dentro de un Dev Container Linux. Dos hechos chocan
con una app de escritorio:

1. **Las GUIs necesitan una pantalla.** El contenedor no tiene; en WSL2 se puede reenviar la de WSLg, a costa
   de librerías gráficas extra y configuración en el compose.
2. **PyInstaller y `flet build` generan el ejecutable del sistema donde corren.** Un contenedor Linux nunca
   produce un `.exe` de Windows.

## Decisión

- El contenedor corre: núcleo, CLI, tests (las GUIs con `xvfb`, una pantalla virtual) y el build de Linux.
- Las GUIs se miran de forma puntual reenviando WSLg. Las librerías gráficas y la configuración de WSLg se
  agregan al `Dockerfile` y al compose **en la fase de cada GUI**, no antes.
- Los ejecutables de Windows y Linux se construyen en **GitHub Actions** con una matriz por sistema operativo y
  se publican en *Releases*. macOS queda fuera por ahora: la notarización exige una cuenta de Apple Developer
  de pago.

## Consecuencias

- **Se gana:** la imagen de desarrollo queda mínima (413 MB, ver ADR-0009); los binarios se construyen en un
  entorno limpio y reproducible para cada sistema.
- **Se paga:** para ver una GUI hace falta WSLg y algo de configuración; los ejecutables de Windows solo se
  prueban en CI o en una máquina Windows.

## Alternativas consideradas

- **GUI siempre dentro del contenedor:** descartada por ahora; más librerías y configuración desde el día uno,
  sin beneficio mientras se construyen el núcleo y la CLI.
- **Construir el `.exe` con Wine dentro del contenedor:** frágil y lento. Descartada.
