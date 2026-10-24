# tests/ — Verificación (el gate)

Nada se da por bueno sin pasar por aquí. Todo bug corregido lleva primero un test que lo reproduce.
Cubrir siempre: **happy path + edge cases + estado vacío**.

| Carpeta | Rol |
|---|---|
| `backend/` | Tests de la API, servicios y casos de uso. |
| `frontend/` | Tests de la interfaz. |
| `database/` | Tests de modelos, repositorios, migraciones y gobernanza. |
| `analytics/` | Tests de la lógica analítica. |
| `acceptance/` | Tests de aceptación **por feature**, contra el `spec.md` correspondiente. |
| `utils/` | Tests de las utilidades de `src/utils` (Polars). |
