# TODO - GoAccess Infra on molly

## Phase 1 - Bootstrap
- [x] Create standalone project layout under `srv/ops/goaccess` (copy to `/srv/ops/goaccess` on `molly`)
- [x] Add `README.md` and operational command skeleton
- [x] Define ownership/permissions guidance

## Phase 2 - Config + Validation (TDD)
- [x] Define `goaccess-sites.yaml` authoritative schema and sample `powergraph` site
- [x] Add tests for duplicate `site_id`
- [x] Add tests for duplicate `internal_port`
- [x] Add tests for missing `log_file`
- [x] Implement `bin/validate-sites.sh`

## Phase 3 - Compose + Reconcile (TDD)
- [x] Add compose render tests for enabled/disabled sites
- [x] Add caddy snippet render tests for enabled/disabled sites
- [x] Implement idempotent compose rendering logic
- [x] Implement `bin/reconcile-goaccess.sh` (`validate -> render -> compose up -> health checks`)

## Phase 4 - Web Routing
- [x] Add Caddy snippet for `webstats.gaudengalea.com` path routing
- [x] Generate Caddy snippet from `goaccess-sites.yaml`
- [x] Document safe Caddy validate/reload flow

## Phase 5 - Access Control
- [x] Document Cloudflare DNS + Access Application + single-identity policy
- [x] Document verification steps for unauthorized/authorized access behavior

## Phase 6 - Operationalization
- [x] Add runbook: add site, disable site, rotate logs, troubleshoot websocket, rollback
- [x] Add periodic health-check checklist
