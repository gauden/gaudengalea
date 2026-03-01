# Implementation Log - 2026-03-01 (Molly)

## Scope
Set up standalone GoAccess infra project served at:
- `https://webstats.gaudengalea.com/<site_id>/`
- `wss://webstats.gaudengalea.com/<site_id>/ws`

Protected by Cloudflare Access (single identity policy).

## Final Working Architecture
1. One GoAccess container per enabled site, attached to `caddy_default`.
2. GoAccess parses Caddy JSON logs and writes static HTML to host-mounted path:
   - `/home/ubuntu/apps/caddy/data/goaccess/<site_id>/index.html`
3. Caddy serves static HTML for `/<site_id>*` from `/data/goaccess/<site_id>`.
4. Caddy proxies only `/<site_id>/ws*` to GoAccess container.
5. Cloudflare Access protects `webstats.gaudengalea.com/*`.

## Environment Reality Discovered on Molly
- Caddy runs in Docker container `caddy`.
- Caddy host config path: `/home/ubuntu/apps/caddy/sites` -> container `/etc/caddy`.
- Caddy logs path: `/home/ubuntu/apps/caddy/data` -> container `/data`.
- Log file used for Powergraph: `/home/ubuntu/apps/caddy/data/access-powergraph.log`.

## Main Issues Encountered and Fixes
1. Missing `/srv` write access from local coding environment
- Fix: build mirror under `ulysses:/Users/gauden/dev/webstats/srv/ops/goaccess` and sync to Molly.

2. GoAccess crash: `Directory does not exist: /srv/report`
- Cause: container image did not have writable `/srv/report`.
- Fix: switched output to host-mounted report directory (`/report/index.html` with host bind mount).

3. Origin 400s on `/powergraph` and `/powergraph/`
- Cause: GoAccess endpoint behavior when proxied directly for HTML.
- Fix: split responsibilities:
  - Caddy serves static `index.html`.
  - Caddy proxies only websocket path.

4. Cloudflare Access policy existed but no Access application
- Symptom: no auth challenge, public returned `200`.
- Fix: create Access app for `webstats.gaudengalea.com/*` and attach `only-me` policy.

5. WS auth/connect failure after Access login
- Symptom: browser showed unable to authenticate websocket.
- Root cause: GoAccess-generated client attempted `wss://webstats.gaudengalea.com:7890/...`.
- Fix: force ws URL to `wss://webstats.gaudengalea.com:443/<site_id>/ws`.

6. Browser/test confusion from huge terminal output
- Cause: `curl` without `-I`/`-o /dev/null` dumped full HTML JS bundle.
- Fix: use focused checks (`-I`, `-w '%{http_code}'`, targeted `grep`).

## Final Validation Signals
- Reconcile succeeds and health checks pass.
- Origin check returns `200`:
  - `curl -sS -o /dev/null -w '%{http_code}\n' --resolve webstats.gaudengalea.com:443:127.0.0.1 https://webstats.gaudengalea.com/powergraph/`
- Public unauthenticated check returns `302` to Cloudflare Access login.
- Authenticated browser session shows realtime dashboard and live metrics.

## Concrete Config Values in Working State
- Docker network: `caddy_default`
- Site ID: `powergraph`
- Container name: `powergraph-goaccess`
- Internal port: `7890`
- Log file: `/home/ubuntu/apps/caddy/data/access-powergraph.log`
- WS URL emitted by GoAccess: `wss://webstats.gaudengalea.com:443/powergraph/ws`

## Operational Notes
- If websocket appears broken, first confirm browser is not requesting `:7890` publicly.
- If HTML appears stale, regenerate by removing `index.html` and restarting site container.
- Keep Caddy snippet generated from `goaccess-sites.yaml` as source-of-truth.
