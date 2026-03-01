# TODO - Origin Deployment Migration

## Phase 1 - Planning and Safety
- [x] Define deployment target architecture (CI build + rsync + atomic release switch).
- [x] Confirm redaction and no-secrets policy is in place for versioned docs.
- [x] Confirm deployment configuration uses secrets/variables, not inline credentials.

## Phase 2 - Workflow Implementation
- [x] Replace GitHub Pages publishing workflow with origin deployment workflow.
- [x] Switch trigger branch to `main`.
- [x] Add required setting validation and self-hosted runner deployment logic in workflow.
- [x] Add atomic release deployment and retention pruning logic.

## Phase 3 - Documentation and Handoff
- [x] Add setup guide for repository variables and secrets.
- [x] Add implementation TODO tracker and complete all phases.
- [x] Validate repository diff for sensitive data leakage in new/changed files.

## Phase 4 - Dependabot Remediation (2026-03-01)
- [x] Inspect `pyproject.toml` and `uv.lock` for vulnerable transitive dependencies.
- [x] Apply minimal compatible lockfile upgrades for reachable advisories.
- [x] Validate static build and repository tests after upgrades.
- [x] Document fixed vs deferred alerts and residual risk.
