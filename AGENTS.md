# Project Constitution

## Purpose
This repository must not contain secrets or sensitive infrastructure details. All versioned content must be safe to publish.

## Non-Negotiable Security Invariants
1. Never commit API tokens, SSH keys, passwords, private certificates/keys, cookies, or session files.
2. Never commit private network details (Tailnet names, internal hostnames, private/public management IPs), unless replaced with placeholders.
3. Never commit unredacted Cloudflare/OCI/Tailscale settings, account IDs, zone IDs, or access policy IDs.
4. Never commit command output/history that contains sensitive values.

## Documentation Redaction Standard
1. Versioned operations documentation must use placeholders only.
2. Canonical placeholder format is `<UPPER_SNAKE_CASE>`.
3. Use placeholders such as:
- `<PRIMARY_DOMAIN>`
- `<CANONICAL_HOST>`
- `<ORIGIN_PUBLIC_IP>`
- `<SSH_USER>`
- `<SSH_HOST>`
- `<CF_ZONE_ID>`
- `<CF_API_TOKEN>`
- `<TLS_CERT_PATH>`
- `<TLS_KEY_PATH>`
4. Real examples are not allowed in committed docs, screenshots, logs, or snippets.

## Operational Secrets Handling
1. Store secrets only in approved secure stores:
- GitHub Actions Secrets
- Cloudflare token/secret storage
- OCI/Tailscale control planes
- local password manager
- local untracked private notes
2. Do not track `.env` files that contain real secrets.
3. Never paste secret material into issues, commit messages, or PR descriptions.

## Pre-Commit and PR Hygiene
1. Before commit, scan staged changes for:
- `token`
- `secret`
- `key`
- `tailscale`
- `cloudflare`
- `oracle`
- IPv4/IPv6 literals
2. Reject the commit if any sensitive value appears.
3. Infra/docs PRs must include a redaction review checklist result.

## Incident Response for Accidental Exposure
1. Immediately rotate/revoke affected credentials.
2. Remove exposed values from repository history when required.
3. Record incident details only in private channels, not in this repository.

