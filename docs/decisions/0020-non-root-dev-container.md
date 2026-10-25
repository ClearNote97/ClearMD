# ADR-0020: The development container runs as a non-root user with the host's UID

- **Status:** accepted
- **Date:** 2026-10-25

## Context

The template's dev container runs as `root` "for simplicity". With the project on a bind mount, every file
created inside the container belongs to root on the host: VS Code's git (running in the container) left root-owned
objects in `.git`, and git on the host then failed with *insufficient permission for adding an object*. The same
happened to `.venv`, generated fixtures and test outputs. Root inside the container is also more privilege than
development needs.

## Decision

- The `Dockerfile` creates a user `dev` with `USER_UID`/`USER_GID` (default 1000, the usual first WSL user;
  passed by `docker-compose.yml` from `.env`) and switches to it with `USER`.
- `devcontainer.json` uses `"remoteUser": "dev"` and `"updateRemoteUserUID": true`, so VS Code also aligns the
  UID if the host user is not 1000.
- `UV_LINK_MODE=copy`: the uv cache (in the container) and `.venv` (on the bind mount) are on different file
  systems, where hardlinks fail.

## Consequences

- **Gains:** files in the project always belong to the host user; git works from both sides; `docker exec`
  runs as `dev` too; less privilege.
- **Costs:** installing system packages inside a running container needs `--user root`; the container has to be
  rebuilt once; a host user with a UID other than 1000 sets `USER_UID`/`USER_GID` in `.env`.

## Alternatives considered

- **Keep root and fix ownership by hand (`chown`):** rejected; it hides the cause and breaks again silently.
