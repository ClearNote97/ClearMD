# -----------------------------------------------------------------------------
# DOCKERFILE - ClearMD (development environment)
# -----------------------------------------------------------------------------
# Python 3.14 (markitdown requires <3.15). 'slim-bookworm' = Debian 12 (glibc 2.36).
# Each GUI's graphics libraries are added in that GUI's phase (ADR-0008): Tk for 005.
FROM python:3.14.5-slim-bookworm

# Keep Debian from opening interactive prompts while installing packages.
ENV DEBIAN_FRONTEND=noninteractive

# Essential system packages:
# - git/openssh-client: version control.
# - ca-certificates: HTTPS (downloading dependencies).
# - curl: network utilities and diagnostics.
# No build-essential: every dependency ships wheels for 3.14 (ADR-0009).
# - libtk8.6, libxcursor1 (tkdnd), xvfb, xauth, fonts-dejavu-core: the ttkbootstrap GUI (feature 005,
#   ADR-0008/0026), run and screenshotted under a virtual display; never shown from the container.
# - libxkbcommon0, libegl1, libgl1, libfontconfig1, libdbus-1-3, libglib2.0-0, libxkbcommon-x11-0, the xcb
#   libraries: the Qt GUI (feature 016), tested offscreen and screenshotted under the same display.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    openssh-client \
    curl \
    libtk8.6 \
    libxcursor1 \
    xvfb \
    xauth \
    binutils \
    fonts-dejavu-core \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libegl1 \
    libgl1 \
    libfontconfig1 \
    libdbus-1-3 \
    libglib2.0-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-keysyms1 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-image0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 'uv', the package manager: binaries copied from Astral's official image.
COPY --from=ghcr.io/astral-sh/uv:0.11.13 /uv /uvx /bin/
# The uv cache lives in the container and the project on a bind mount: hardlinks cannot cross them.
ENV UV_LINK_MODE=copy

# -----------------------------------------------------------------------------
# NON-ROOT USER
# -----------------------------------------------------------------------------
# Same UID/GID as the host user (1000 by default on WSL/Ubuntu), so every file created inside the
# container -- by VS Code's git, by uv, by the tests -- belongs to the host user on the bind mount.
ARG USER_NAME=dev
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid ${USER_GID} ${USER_NAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} --create-home --shell /bin/bash ${USER_NAME}

# -----------------------------------------------------------------------------
# DYNAMIC WORKDIR
# -----------------------------------------------------------------------------
# The project name comes from docker-compose (from .env) and names the folder
# inside the container.
ARG APP_NAME=project_default
ENV PROJECT_NAME=${APP_NAME}

# Example: APP_NAME=ClearMD -> WORKDIR /workspaces/ClearMD
WORKDIR /workspaces/${PROJECT_NAME}
RUN chown ${USER_UID}:${USER_GID} /workspaces/${PROJECT_NAME}

USER ${USER_NAME}

# Keep the container running while you work.
CMD ["sleep", "infinity"]