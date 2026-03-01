# Next App Onboarding Playbook (Molly)

Use this playbook to add another app to webstats with minimal guesswork.

## Inputs You Need
- `SITE_ID`: URL slug for webstats path (example: `myapp`)
- `SOURCE_HOST`: app hostname observed in logs (example: `myapp.gaudengalea.com`)
- `LOG_FILE`: host path to Caddy JSON log file (example: `/home/ubuntu/apps/caddy/data/access-myapp.log`)
- `CONTAINER_NAME`: stable GoAccess container name (example: `myapp-goaccess`)
- `INTERNAL_PORT`: unique container port (example: `7891`)

## Step 1 - Edit Config on Ulysses
Use helper to append a validated site entry:

```bash
cd /Users/gauden/dev/webstats/srv/ops/goaccess
./bin/add-site.sh \
  --site-id myapp \
  --source-host myapp.gaudengalea.com \
  --log-file /home/ubuntu/apps/caddy/data/access-myapp.log \
  --container-name myapp-goaccess \
  --internal-port 7891 \
  --enabled true
```

Rules:
- `site_id` must be unique and slug-safe.
- `internal_port` must be unique across sites.
- `log_file` must exist on Molly host.
- Use `--allow-missing-log` only if the log path will be created later.

Dry-run preview:

```bash
./bin/add-site.sh \
  --site-id myapp \
  --source-host myapp.gaudengalea.com \
  --log-file /home/ubuntu/apps/caddy/data/access-myapp.log \
  --container-name myapp-goaccess \
  --internal-port 7891 \
  --dry-run
```

## Step 2 - Sync to Molly
Run from `ulysses`:

```bash
rsync -av --delete /Users/gauden/dev/webstats/srv/ops/goaccess/ ubuntu@molly.calliope-ray.ts.net:/srv/ops/goaccess/
```

## Step 3 - Reconcile on Molly

```bash
set -euo pipefail
cd /srv/ops/goaccess
./bin/validate-sites.sh ./goaccess-sites.yaml
./bin/reconcile-goaccess.sh
```

This will:
- generate compose
- generate caddy snippet
- create `/home/ubuntu/apps/caddy/data/goaccess/<site_id>`
- start/refresh GoAccess containers

## Step 4 - Publish Caddy Routing

```bash
cp /srv/ops/goaccess/caddy/webstats.caddy.snippet /home/ubuntu/apps/caddy/sites/webstats.caddy.snippet
grep -q "import /etc/caddy/webstats.caddy.snippet" /home/ubuntu/apps/caddy/sites/Caddyfile || \
  echo "import /etc/caddy/webstats.caddy.snippet" >> /home/ubuntu/apps/caddy/sites/Caddyfile

docker exec caddy caddy validate --config /etc/caddy/Caddyfile
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## Step 5 - Verify Origin and Access

Origin (from Molly):

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  --resolve webstats.gaudengalea.com:443:127.0.0.1 \
  https://webstats.gaudengalea.com/myapp/
```

Expected: `200`

Public unauthenticated (from anywhere):

```bash
curl -I https://webstats.gaudengalea.com/myapp/
```

Expected: `302` to Cloudflare Access login (or `403` depending policy flow).

## Step 6 - Browser Validation
1. Open incognito `https://webstats.gaudengalea.com/myapp/`.
2. Complete Access login.
3. Confirm dashboard loads and live counters update.

## Cloudflare One-Time Requirements (if not already done)
1. DNS `A/AAAA/CNAME` for `webstats.gaudengalea.com` must be proxied (orange cloud).
2. Access application exists for `webstats.gaudengalea.com/*`.
3. Access allow policy restricts to your identity.

## Troubleshooting Quick Reference
1. `Directory does not exist` in GoAccess logs
- Check output mount `/home/ubuntu/apps/caddy/data/goaccess/<site_id>` exists.

2. `400` at `/myapp/ws` seen in browser as document request
- Ignore if request is navigation (`Sec-Fetch-Mode: navigate`), not websocket handshake.

3. Websocket fails after login
- Confirm GoAccess cmd includes `--ws-url=wss://webstats.gaudengalea.com:443/<site_id>/ws`.
- Confirm browser WS request does not target `:7890` publicly.

4. No Access challenge on public URL
- Check Access app exists and path is `/*`.
- Ensure policy is attached to application (reusable policy alone is not enough).

5. Stale HTML served
- Remove report file and restart site container:

```bash
rm -f /home/ubuntu/apps/caddy/data/goaccess/myapp/index.html
docker restart myapp-goaccess
```
