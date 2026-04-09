# Origin Deployment Setup

This repository deploys Astro static output from GitHub Actions to an origin host using a self-hosted runner on the origin.

## Branch Prerequisite
The workflow triggers on `main`. Rename the default branch from `master` to `main` before expecting automatic deployments.

## Runner Requirement on `molly`
The repository must have an online self-hosted runner on `molly` with labels:

- `self-hosted`
- `Linux`
- `ARM64`
- `molly`

## Required GitHub Repository Variables
Set these in repository settings -> Variables:

1. `CANONICAL_HOST`
- Example format: `<CANONICAL_HOST>`
2. `DEPLOY_ROOT`
- Example format: `<HOST_DATA_ROOT>/sites/<SITE_SLUG>`
3. `RELEASE_RETENTION`
- Example: `10`

## One-Time Origin Host Preparation
Run on origin host as a privileged account:

```bash
install -d -m 775 "<HOST_DATA_ROOT>/sites/<SITE_SLUG>/releases"
```

Ensure runner service account can write under:

- `<HOST_DATA_ROOT>/sites/<SITE_SLUG>/releases`
- `<HOST_DATA_ROOT>/sites/<SITE_SLUG>/current` (symlink update)

Ensure the self-hosted runner service account can write to those paths.

## Caddy Configuration Requirement
Caddy must serve from:

- `<CONTAINER_DATA_ROOT>/sites/<SITE_SLUG>/current`

and write access logs to:

- `<CADDY_ACCESS_LOG_PATH>`

## Deployment Behavior
On each push to `main`, the workflow:

1. Installs Node dependencies with `npm ci`.
2. Builds static output with Astro into `dist/`.
3. Writes `CNAME` from `CANONICAL_HOST`.
4. Copies files to a release directory:
- `<DEPLOY_ROOT>/releases/<TIMESTAMP>-<SHORT_SHA>`
5. Validates `index.html` exists.
6. Atomically updates:
- `<DEPLOY_ROOT>/current`
7. Prunes old releases beyond `RELEASE_RETENTION`.

## Development Machine Actions on `ulysses`
Before opening or updating a PR:

1. Run `npm ci`.
2. Run `uv run pytest`.
3. Run `npm run build`.
4. Validate:
- `/`
- `/blog`
- `/pub`
- `/lab`
- `/bio`
- `/feed`
5. Confirm the draft migration announcement post is not present in `dist/`.

## First Astro Rollout Checks on `molly`
After the first deployment:

1. Confirm the new release directory contains Astro output and `CNAME`.
2. Confirm `<DEPLOY_ROOT>/current` points to the new release.
3. Confirm Caddy serves the Astro build without changing the document root.
4. Confirm `/feed` responds with valid XML.
5. Keep at least one last-known-good Lektor release under `<DEPLOY_ROOT>/releases/` until the Astro site is validated in production.
