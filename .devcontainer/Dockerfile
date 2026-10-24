# -----------------------------------------------------------------------------
# DOCKERFILE - ClearMD (development environment)
# -----------------------------------------------------------------------------
# Python 3.14 (markitdown requires <3.15). 'slim-bookworm' = Debian 12 (glibc 2.36).
# Each GUI's graphics libraries are added in that GUI's phase (ADR-0008).
FROM python:3.14.5-slim-bookworm

# Keep Debian from opening interactive prompts while installing packages.
ENV DEBIAN_FRONTEND=noninteractive

# Essential system packages:
# - git/openssh-client: version control.
# - ca-certificates: HTTPS (downloading dependencies).
# - curl: network utilities and diagnostics.
# No build-essential: every dependency ships wheels for 3.14 (ADR-0009).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    openssh-client \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 'uv', the package manager: binaries copied from Astral's official image.
COPY --from=ghcr.io/astral-sh/uv:0.11.13 /uv /uvx /bin/

# -----------------------------------------------------------------------------
# DYNAMIC WORKDIR
# -----------------------------------------------------------------------------
# The project name comes from docker-compose (from .env) and names the folder
# inside the container.
ARG APP_NAME=project_default
ENV PROJECT_NAME=${APP_NAME}

# Example: APP_NAME=ClearMD -> WORKDIR /workspaces/ClearMD
WORKDIR /workspaces/${PROJECT_NAME}

# Keep the container running while you work.
CMD ["sleep", "infinity"]