# Implementation Plan - GoAccess Infra on molly

## Objective
Deploy a standalone VM-local infra project at `/srv/ops/goaccess` that serves per-site realtime dashboards at:
- `https://webstats.gaudengalea.com/<site_id>`
- `wss://webstats.gaudengalea.com/<site_id>/ws`

Protected by Cloudflare Access (single-identity allow policy), with existing app host blocks unaffected.

## Contracts
1. Authoritative config: `goaccess-sites.yaml`
2. Reconcile entrypoint: `bin/reconcile-goaccess.sh` (validate, render, apply, health-check)
3. URL contract:
- HTML: `/<site_id>`
- WS: `/<site_id>/ws`

## Architecture
- One GoAccess container per enabled site.
- No host port publishing.
- Read-only bind mount for each site log file.
- Containers attach to shared `caddy_default` network.
- Compose and Caddy snippet are generated from `goaccess-sites.yaml`.
- On `molly`, Caddy runs in Docker (`caddy` container), with config at `/home/ubuntu/apps/caddy/sites` and logs under `/home/ubuntu/apps/caddy/data`.

## Phases
1. Bootstrap
- Create project layout and standalone Git repo.
- Add README, TODO, and operational defaults.

2. Config + Validation (TDD)
- Define schema for site entries.
- Validate duplicate `site_id`, duplicate `internal_port`, invalid slug, missing log path.

3. Compose + Reconcile (TDD)
- Render `compose.yaml` idempotently.
- Run `docker compose up -d --remove-orphans`.
- Verify enabled containers are running and attached to `caddy_default`.

4. Web Routing
- Generate Caddy snippet for all enabled sites with path handlers for both HTML and WS.
- Preserve websocket upgrade behavior.

5. Access Control
- Cloudflare proxied DNS for `webstats.gaudengalea.com`.
- Cloudflare Access Application for `webstats.gaudengalea.com/*`.
- Policy allows only designated identity.

6. Operationalization
- Runbook for add/disable site, log rotation, WS troubleshooting, rollback.
- Periodic health checklist.

## Test Scenarios
- Validation failures for duplicates and missing log path.
- Rendering includes only enabled sites.
- Reconcile idempotency on unchanged config.
- Authorized/unauthorized access behavior through Cloudflare Access.
- Site isolation across multiple log sources.
