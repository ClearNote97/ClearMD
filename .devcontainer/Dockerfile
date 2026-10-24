# -----------------------------------------------------------------------------
# DOCKERFILE - ClearMD (Entorno de Desarrollo)
# -----------------------------------------------------------------------------
# Python 3.14 (markitdown exige <3.15). 'slim-bookworm' = Debian 12 (glibc 2.36).
# Las librerías gráficas de cada GUI se agregan en la fase de esa GUI (ADR-0008).
FROM python:3.14.5-slim-bookworm

# Evita que Debian abra diálogos interactivos durante la instalación de paquetes.
ENV DEBIAN_FRONTEND=noninteractive

# Paquetes esenciales del sistema:
# - git/openssh-client: control de versiones.
# - ca-certificates: conexiones HTTPS (descarga de dependencias).
# - curl: utilidades de red y diagnóstico.
# Sin build-essential: todas las dependencias publican wheels para 3.14 (ADR-0009).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    openssh-client \
    curl \
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
# Ejemplo: si APP_NAME=ClearMD, el WORKDIR será /workspaces/ClearMD
WORKDIR /workspaces/${PROJECT_NAME}

# Comando por defecto para mantener el contenedor encendido mientras trabajas.
# Impide que el contenedor se apague inmediatamente después de iniciarse.
CMD ["sleep", "infinity"]