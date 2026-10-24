# src/backend/api — Endpoints (capa de entrada)

Rutas HTTP. Delgadas: validan entrada, llaman a `use_cases/`/`services/` y serializan la salida.
La lógica de negocio **no** vive aquí. Registrar cada router nuevo en el router principal.
