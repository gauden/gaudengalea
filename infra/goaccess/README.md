# GoAccess Infra (VM-local)

Standalone infrastructure project for realtime GoAccess dashboards served at:
- HTML: `https://webstats.gaudengalea.com/<site_id>`
- WebSocket: `wss://webstats.gaudengalea.com/<site_id>/ws`

This mirror is prepared under `webstats/srv/ops/goaccess` so you can copy it to:
- `/srv/ops/goaccess` on VM `molly`

## Planning Docs
- `docs/PLAN.md`: phased implementation plan and contracts
- `docs/TODO.md`: canonical checklist and completion status
- `docs/IMPLEMENTATION-LOG-2026-03-01.md`: concrete timeline of issues/fixes that led to working state
- `docs/NEXT-APP-ONBOARDING.md`: copy/paste playbook for onboarding the next app

## Files
- `goaccess-sites.yaml`: authoritative site mapping
- `compose.yaml`: rendered Docker Compose file (do not hand-edit)
- `bin/add-site.sh`: helper to append a validated site entry to `goaccess-sites.yaml`
- `bin/validate-sites.sh`: schema + integrity checks
- `bin/reconcile-goaccess.sh`: idempotent reconcile entrypoint
- `caddy/webstats.caddy.snippet`: rendered host routing snippet for webstats
- `.gitignore`: excludes generated/transient files

## Schema (`goaccess-sites.yaml`)
Each site entry supports:
- `site_id`: URL slug (`powergraph`)
- `source_host`: observed hostname or comma-separated host list (`powergraph.gaudengalea.com` or `gaudengalea.com,www.gaudengalea.com`)
- `log_file`: absolute host path to Caddy JSON log file
- `container_name`: stable GoAccess service/container name
- `internal_port`: unique container listen port
- `enabled`: boolean

## Prerequisites on molly
- Docker + Compose plugin available
- Docker network `caddy_default` exists
- Dockerized Caddy container is running on `caddy_default`
- Caddy config host path mounted at `/home/ubuntu/apps/caddy/sites` (observed on `molly`)
- Caddy JSON logs available at configured `log_file` path(s) (observed: `/home/ubuntu/apps/caddy/data/access-powergraph.log`)

## Ownership and Permissions (recommended)
```bash
sudo mkdir -p /srv/ops/goaccess
sudo chown -R $USER:$USER /srv/ops/goaccess
sudo chmod -R u=rwX,go=rX /srv/ops/goaccess
chmod +x /srv/ops/goaccess/bin/*.sh
```

## Reconcile Flow
```bash
cd /srv/ops/goaccess
./bin/reconcile-goaccess.sh
```

What reconcile does:
1. Validates `goaccess-sites.yaml`
2. Renders `compose.yaml` from config
3. Renders `caddy/webstats.caddy.snippet` from config
4. Ensures per-site report directories exist under `/home/ubuntu/apps/caddy/data/goaccess/<site_id>`
5. Runs `docker compose up -d --remove-orphans`
6. Verifies each enabled site container is running and attached to `caddy_default`

Idempotency:
- Re-running without config changes keeps effective state stable.

## Caddy Integration
1. Copy `caddy/webstats.caddy.snippet` to `/home/ubuntu/apps/caddy/sites/webstats.caddy.snippet`.
2. Add `import /etc/caddy/webstats.caddy.snippet` to `/home/ubuntu/apps/caddy/sites/Caddyfile` if missing.
3. Keep existing app host blocks unchanged.
4. Validate and reload Caddy in-container:
```bash
docker exec caddy caddy validate --config /etc/caddy/Caddyfile
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### Client IP accuracy behind Cloudflare
Use trusted proxy handling in Caddy global options so Cloudflare-provided client IP is trusted.
Example (adjust to your installed Caddy capabilities):
```caddyfile
{
  servers {
    trusted_proxies static 173.245.48.0/20 103.21.244.0/22 103.22.200.0/22 103.31.4.0/22 141.101.64.0/18 108.162.192.0/18 190.93.240.0/20 188.114.96.0/20 197.234.240.0/22 198.41.128.0/17 162.158.0.0/15 104.16.0.0/13 104.24.0.0/14 172.64.0.0/13 131.0.72.0/22
  }
}
```

## Cloudflare Setup
1. DNS: create proxied `A/AAAA/CNAME` for `webstats.gaudengalea.com`.
2. Access Application:
- Domain: `webstats.gaudengalea.com`
- Path: `/*`
3. Access policy:
- Action: Allow
- Identity: only your account/email

## Verification Checklist
- Validation:
  - duplicate `site_id` rejected
  - duplicate `internal_port` rejected
  - missing `log_file` path rejected
- Realtime:
  - `/<site_id>` loads
  - `/<site_id>/ws` upgrades, counters move when traffic is generated
- Security:
  - unauthenticated request blocked by Cloudflare Access
  - authorized identity allowed
- Isolation:
  - each site reflects only its configured log file
- Idempotency:
  - running reconcile twice with no changes produces no drift

## Runbook
### Add a site
1. Add a new site entry with helper:
```bash
./bin/add-site.sh \
  --site-id myapp \
  --source-host myapp.gaudengalea.com \
  --log-file /home/ubuntu/apps/caddy/data/access-myapp.log \
  --container-name myapp-goaccess \
  --internal-port 7891 \
  --enabled true
```
2. Validate config:
```bash
./bin/validate-sites.sh ./goaccess-sites.yaml
```
3. Alternative if log file does not exist yet:
```bash
./bin/add-site.sh ... --allow-missing-log
```
Then create/enable log file and re-run validation.
4. Run reconcile (this regenerates compose + Caddy snippet).
5. Merge updated snippet into active Caddy config.
6. Validate Caddy and reload.
7. Verify HTML + WebSocket endpoint.

### Disable a site
1. Set `enabled: false` in `goaccess-sites.yaml`.
2. Run reconcile (`--remove-orphans` removes disabled container).
3. Merge updated generated snippet into Caddy config.
4. Reload Caddy.

### Rotate logs
1. Rotate the source Caddy log file per your existing logrotate policy.
2. Ensure new file path matches `log_file` in config.
3. Run reconcile if path changed.

### Troubleshoot WebSocket
1. Check Cloudflare Access auth state.
2. Confirm Caddy path handler order (`/ws` matcher before generic site matcher).
3. Check container running and in `caddy_default`.
4. Confirm `ws-url` emitted by compose uses `wss://webstats.gaudengalea.com/<site_id>/ws`.
5. Confirm HTML file exists at `/home/ubuntu/apps/caddy/data/goaccess/<site_id>/index.html`.

### Rollback
1. Revert Git commit in `/srv/ops/goaccess`.
2. Re-run reconcile.
3. Restore prior Caddy config and reload.

## Periodic Health Checks
```bash
cd /srv/ops/goaccess
./bin/validate-sites.sh
./bin/reconcile-goaccess.sh

docker compose -f compose.yaml ps
```
- Confirm each enabled container is running.
- Confirm `https://webstats.gaudengalea.com/<site_id>` renders after Cloudflare Access login.

## Deploy to Molly
Copy this mirror to VM path and apply:
```bash
rsync -av --delete /Users/gauden/dev/webstats/srv/ops/goaccess/ ubuntu@molly.calliope-ray.ts.net:/srv/ops/goaccess/

ssh ubuntu@molly.calliope-ray.ts.net '
  set -euo pipefail
  cd /srv/ops/goaccess
  chmod +x bin/*.sh
  ./bin/validate-sites.sh ./goaccess-sites.yaml
  ./bin/reconcile-goaccess.sh
  cp caddy/webstats.caddy.snippet /home/ubuntu/apps/caddy/sites/webstats.caddy.snippet
  grep -q \"import /etc/caddy/webstats.caddy.snippet\" /home/ubuntu/apps/caddy/sites/Caddyfile || echo \"import /etc/caddy/webstats.caddy.snippet\" >> /home/ubuntu/apps/caddy/sites/Caddyfile
  docker exec caddy caddy validate --config /etc/caddy/Caddyfile
  docker exec caddy caddy reload --config /etc/caddy/Caddyfile
'
```

If GoAccess cannot read log file:
```bash
sudo chmod 644 /home/ubuntu/apps/caddy/data/access-powergraph.log
```
