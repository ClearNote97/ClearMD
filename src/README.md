# src/ — Implementación (arquitectura limpia)

El código. Separado por responsabilidad; las dependencias apuntan hacia el dominio, no al revés.

| Carpeta | Rol |
|---|---|
| `backend/` | API, servicios, casos de uso, esquemas (lógica de aplicación). |
| `frontend/` | Interfaz de usuario (vistas, componentes, estado, servicios). |
| `database/` | Modelos, repositorios, migraciones y **gobernanza** (`admin/`). |
| `analytics/` | Código de analítica: ML, estadística, tracking de experimentos. |
| `utils/` | Utilidades transversales (limpieza, formateo) — **Polars-first**. |
