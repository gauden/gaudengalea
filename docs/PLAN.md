# Deployment Plan (Redacted)

## Goal
Migrate static hosting from Pages to a Caddy origin via CI deployment, with safe atomic releases and rollback support.

## Architecture
CI build -> rsync deploy -> atomic symlink switch -> Caddy serve -> Cloudflare proxy

## Branching and CI Trigger
1. Deploy only on pushes to `main`.
2. Disable Pages publishing workflow.
3. Use one production deployment concurrency group.

## Server Layout (Placeholder Paths)
1. Release root:
- `<HOST_DATA_ROOT>/sites/<SITE_SLUG>/releases/<RELEASE_ID>/`
2. Live symlink:
- `<HOST_DATA_ROOT>/sites/<SITE_SLUG>/current`
3. Caddy container path:
- `<CONTAINER_DATA_ROOT>/sites/<SITE_SLUG>/current`
4. Keep latest `<RELEASE_RETENTION_COUNT>` releases.

## CI/CD Flow
1. Checkout repository.
2. Install runtime and static-site build dependencies.
3. Build static output to `<BUILD_OUTPUT_DIR>`.
4. Write `CNAME` containing `<CANONICAL_HOST>`.
5. Rsync build output to `<SSH_USER>@<SSH_HOST>:<HOST_DATA_ROOT>/sites/<SITE_SLUG>/releases/<RELEASE_ID>/`.
6. Validate release content exists (for example, `index.html`).
7. Atomically update `current` symlink to new release.
8. Prune old releases beyond retention threshold.
9. Optionally purge edge cache via provider API token stored in CI secret store.

## DNS/TLS Cutover
1. Ensure certificate/key are configured at:
- `<TLS_CERT_PATH>`
- `<TLS_KEY_PATH>`
2. Set DNS records (proxied) for:
- `<PRIMARY_DOMAIN>` -> `<ORIGIN_PUBLIC_IP>`
- `<CANONICAL_HOST>` -> `<ORIGIN_PUBLIC_IP>`
3. Enforce canonical redirect:
- `<PRIMARY_DOMAIN>` -> `https://<CANONICAL_HOST>{uri}`
4. Verify provider SSL mode is strict origin verification.

## GoAccess Post-Cutover
Use private ops notes for concrete values. Versioned docs must remain placeholder-only.

1. Add site entry in GoAccess config with placeholders:
- `site_id: <GOACCESS_SITE_ID>`
- `source_host: <PRIMARY_DOMAIN>,<CANONICAL_HOST>`
- `log_file: <CADDY_ACCESS_LOG_PATH>`
- `container_name: <GOACCESS_CONTAINER_NAME>`
- `internal_port: <GOACCESS_INTERNAL_PORT>`
- `enabled: true`
2. Sync GoAccess ops project to host.
3. Reconcile:
- validate config
- render compose + Caddy snippet
- start/refresh GoAccess containers
4. Publish generated snippet into active Caddy config.
5. Validate and reload Caddy.
6. Verify dashboard and websocket path:
- `https://<WEBSTATS_HOST>/<GOACCESS_SITE_ID>/`

## Rollback
1. Identify prior release under `<HOST_DATA_ROOT>/sites/<SITE_SLUG>/releases/`.
2. Repoint `current` symlink to last known good release.
3. Reload Caddy if required by local process policy.
4. Validate HTTP response and static asset availability.

## Validation Checklist
1. `https://<PRIMARY_DOMAIN>/` redirects to `https://<CANONICAL_HOST>/`.
2. `https://<CANONICAL_HOST>/` returns `200`.
3. `https://<CANONICAL_HOST>/blog` returns `200`.
4. `https://<CANONICAL_HOST>/pub` returns `200`.
5. `https://<CANONICAL_HOST>/lab` returns `200`.
6. `https://<CANONICAL_HOST>/bio` returns `200`.
7. `https://<CANONICAL_HOST>/feed` returns `200` and valid feed XML.
8. GoAccess endpoint requires access policy and loads after authentication.

## Security/Redaction Appendix
1. Never commit real credentials, topology, or account identifiers.
2. Keep all sensitive values in secret stores or local untracked private notes.
3. Use placeholders in docs, commands, logs, and examples.
4. If accidental exposure occurs, rotate/revoke first, then clean history, and report privately.

