# TODO - Astro + Pages CMS Migration

## Phase 1 - Branch Safety and Scaffolding
- [x] Create feature branch from clean `main` rollback point.
- [x] Replace legacy TODO with migration-specific phases.
- [x] Scaffold Astro project files and deterministic package lockfile.
- [x] Preserve current rollback path by keeping Lektor files until Astro parity is confirmed.

## Phase 2 - Content Conversion Pipeline
- [x] Add tested conversion tooling for `content/**/contents.lr` -> Astro content collections.
- [x] Convert blog, publications, lab, bio, home, and feed content into Astro-managed files.
- [x] Preserve nested blog series routes and colocated media assets.
- [x] Add a draft migration announcement blog post excluded from production output.

## Phase 3 - Astro Rendering Parity
- [x] Port layout, metadata, navigation, footer, and asset loading into Astro layouts/components.
- [x] Recreate blog index ordering, series navigation, and section listings.
- [x] Recreate publications listing with pagination.
- [x] Recreate homepage recent-items aggregation and Atom feed generation.
- [x] Update tooling attribution from Lektor/Python to Astro/Pages CMS where appropriate.

## Phase 4 - CMS and CI/CD
- [x] Add hosted Pages CMS configuration in `.pages.yml`.
- [x] Wire CMS fields to Astro content schemas, including `draft`.
- [x] Replace Lektor build steps in GitHub Actions with Astro build and deploy output.
- [x] Update local/deployment documentation for `ulysses` and `molly`.

## Phase 5 - Validation and Cleanup
- [x] Run tests for conversion tooling.
- [x] Run Astro build and route/feed validation locally.
- [x] Confirm draft exclusion and static asset resolution.
- [x] Remove obsolete Lektor files once parity is confirmed.
- [x] Review changed files for sensitive data and deployment safety.

## Phase 6 - Astro Dependabot Remediation (2026-04-22)
- [x] Inspect npm manifests for the Astro alert.
- [x] Apply minimal compatible Astro patch-line upgrade.
- [x] Validate npm audit, Astro build, and existing tests.
- [x] Review dependency diff for unnecessary churn.

## Phase 7 - npm Vulnerability Remediation (2026-05-15)
- [x] Inspect npm dependency graph for `fast-xml-builder` and `devalue`.
- [x] Apply the minimal lockfile/package update needed for patched versions.
- [x] Validate with npm audit and production build.
- [x] Review changed files for sensitive data and dependency churn.
