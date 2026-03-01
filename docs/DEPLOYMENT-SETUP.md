# Origin Deployment Setup

This repository deploys static output from GitHub Actions to an origin host using a self-hosted runner on the origin.

## Branch Prerequisite
The workflow triggers on `main`. Rename the default branch from `master` to `main` before expecting automatic deployments.

## Runner Requirement
The repository must have an online self-hosted runner with labels:

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

1. Builds static output with Lektor.
2. Writes `CNAME` from `CANONICAL_HOST`.
3. Copies files to a release directory:
- `<DEPLOY_ROOT>/releases/<TIMESTAMP>-<SHORT_SHA>`
4. Validates `index.html` exists.
5. Atomically updates:
- `<DEPLOY_ROOT>/current`
6. Prunes old releases beyond `RELEASE_RETENTION`.
