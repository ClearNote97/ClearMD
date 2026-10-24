# -----------------------------------------------------------------------------
# DOCKERFILE - ClearNote_Dev (Entorno de Desarrollo)
# -----------------------------------------------------------------------------
# Usamos una imagen base de Python moderna (3.14 alpha/experimental o estable)
# La variante 'slim-bookworm' ofrece un balance perfecto entre peso y estabilidad (Debian 12).
FROM python:3.14.5-slim-bookworm

# Evita que Debian abra diálogos interactivos durante la instalación de paquetes.
ENV DEBIAN_FRONTEND=noninteractive

# Instalación de paquetes esenciales del sistema:
# - build-essential: Compiladores necesarios para librerías de Python (como psycopg2 o cryptography).
# - git/openssh-client: Para control de versiones y conexión a repositorios privados.
# - ca-certificates: Para conexiones seguras HTTPS.
# - curl: Herramienta de red para auditoría, healthchecks y descarga de archivos.
# - postgresql-client: cliente psql para consultas ad-hoc y para correr run-admin.sh desde app-dev.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    openssh-client \
    curl \
    postgresql-client \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalación de 'uv': el gestor de paquetes de alto rendimiento (Escrito en Rust).
# Copiamos los binarios directamente desde la imagen oficial de Astral Sh.
COPY --from=ghcr.io/astral-sh/uv:0.11.13 /uv /uvx /bin/

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DINÁMICA DEL WORKDIR
# -----------------------------------------------------------------------------
# Recibimos el nombre del proyecto desde docker-compose (viene del .env).
# Esto crea la carpeta física dentro del contenedor con el nombre correcto.
ARG APP_NAME=project_default
ENV PROJECT_NAME=${APP_NAME}

# Establecemos el directorio de trabajo dinámicamente.
# Ejemplo: si APP_NAME=ClearNote_Dev, el WORKDIR será /workspaces/ClearNote_Dev
WORKDIR /workspaces/${PROJECT_NAME}

# Comando por defecto para mantener el contenedor encendido mientras trabajas.
# Impide que el contenedor se apague inmediatamente después de iniciarse.
CMD ["sleep", "infinity"]