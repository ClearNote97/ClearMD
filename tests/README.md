# tests/ — Verificación (el gate)

Nada se da por bueno sin pasar por aquí. Todo bug corregido lleva primero un test que lo reproduce.
Cubrir siempre: **happy path + edge cases + estado vacío**. Se corre dentro del contenedor:
`uv run pytest`.

| Carpeta | Rol |
|---|---|
| `unit/` | Tests unitarios del paquete `clearmd` (núcleo, conversores, presenter, CLI). |
| `acceptance/` | Tests de aceptación **por feature**, contra el `spec.md` correspondiente. |
| `fixtures/` | Documentos de muestra pequeños (pdf, docx, tex, odt, html…) usados por los tests. |
