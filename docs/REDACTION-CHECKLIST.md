# Redaction Checklist

Run this before committing infra or operations documentation changes.

1. Confirm no real tokens, passwords, keys, cookies, or session files are in staged files.
2. Confirm no real hostnames, Tailnet names, internal labels, or management IPs are present.
3. Confirm no real account IDs, zone IDs, policy IDs, or tenant identifiers are present.
4. Confirm all environment-specific values use `<UPPER_SNAKE_CASE>` placeholders.
5. Confirm command examples do not embed real credentials or real network topology.
6. Confirm screenshots/log snippets are redacted or excluded.
7. Run a staged diff scan for keywords and IP literals before commit.
8. If uncertain, stop and redact further before pushing.

