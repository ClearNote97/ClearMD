# src/backend — Lógica de aplicación

El servidor: expone la API y orquesta la lógica de negocio.

| Carpeta | Rol |
|---|---|
| `api/` | Rutas/endpoints (capa de entrada HTTP). |
| `schemas/` | Esquemas de request/response (validación y serialización). |
| `services/` | Servicios de dominio reutilizables. |
| `use_cases/` | Casos de uso: orquestan servicios para cumplir una intención concreta. |
