# infra/ — Infraestructura (imágenes y config de servicios)

Definiciones de infraestructura que no son código de aplicación: imágenes propias y configuración
de los servicios del `docker-compose`.

| Carpeta | Rol |
|---|---|
| `db/` | Imagen propia de PostgreSQL 18 con las extensiones de gobernanza (pgaudit, pg_cron). |

> El `docker-compose.yml` (raíz) referencia estas piezas. La orquestación de despliegue real
> (k8s/CI) va aparte; aquí vive solo lo necesario para levantar el entorno de la plantilla.
