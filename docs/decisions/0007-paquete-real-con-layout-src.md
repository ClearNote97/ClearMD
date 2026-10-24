# ADR-0007: Paquete real con layout `src/` en vez de proyecto `--no-package`

- **Estado:** aceptada
- **Fecha:** 2026-10-24

## Contexto

En Estado 0, la plantilla genera el proyecto con `uv init --no-package --no-workspace` a partir de
`requirements.txt`. Eso sirve para scripts y análisis, pero ClearMD necesita:

- un núcleo importable por cuatro adaptadores (CLI y tres GUIs);
- un comando instalable (`clearmd`);
- empaquetarse como ejecutable y, eventualmente, publicarse en PyPI (el nombre `clearmd` está libre).

## Decisión

- `pyproject.toml` escrito a mano, con backend de build **`uv_build`** y layout `src/clearmd/`.
- Dependencias en `[project.dependencies]`; herramientas de desarrollo en el grupo `dev`
  (`[dependency-groups]`, PEP 735). Las GUIs y PyInstaller entrarán como extras o grupos en su fase.
- `requirements.txt` desaparece; `init.sh` solo hace `uv sync` (o `uv lock && uv sync` la primera vez).
- Cada subpaquete documenta su rol en el docstring de su `__init__.py`, en vez de un `README.md` por carpeta:
  un README dentro del paquete terminaría empaquetado en el wheel.

## Consecuencias

- **Se gana:** imports limpios (`from clearmd.core import ...`) sin manipular `PYTHONPATH`; el layout `src/`
  obliga a que los tests usen el paquete instalado, no archivos sueltos; el comando `clearmd` existe desde el
  primer commit.
- **Se paga:** se abandona el flujo Estado 0 → Estado N de la plantilla; quien conozca la plantilla debe leer
  este ADR para entender por qué no hay `requirements.txt`.
