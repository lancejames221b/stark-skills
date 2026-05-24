---
name: git-pii-guard
description: Scan git commits for PII, credentials, API keys, and passwords before they are pushed. Automatically gates commits via a pre-commit hook. Use when installing PII scanning on a repo, manually scanning a file or diff for credentials, or when a commit is blocked by the hook and remediation is needed. Triggers on "scan for PII", "check for credentials", "install PII guard", "pii hook", or when a commit is blocked by a PII check.
---

# git-pii-guard

Blocks git commits containing credentials, API keys, passwords, internal IPs, and other PII. Uses a pre-commit hook that scans the staged diff before every commit.

## Scripts

- `scripts/pii_scan.py` — Core scanner. Runs pattern matching against text, files, or git diffs.
- `scripts/install_hook.sh` — Installs the pre-commit hook into a target git repo.

## Install the hook into a repo

```bash
bash ~/dev/skills/git-pii-guard/scripts/install_hook.sh /path/to/repo
# defaults to current directory if no path given
```

Backs up any existing pre-commit hook before overwriting.

## Scan manually

```bash
# Scan a file
python3 ~/dev/skills/git-pii-guard/scripts/pii_scan.py --file path/to/file --report

# Scan staged diff (same as what the hook runs)
python3 ~/dev/skills/git-pii-guard/scripts/pii_scan.py --diff --report

# Scan a string
python3 ~/dev/skills/git-pii-guard/scripts/pii_scan.py --text 'some text to scan'
```

## What it catches

**Blocking (commit refused):**
- Passwords and secrets in assignments (`PASSWORD=`, `SECRET=`, `TOKEN=`, etc.)
- `PGPASSWORD=` env var
- Bearer tokens
- API keys
- Private key headers (`-----BEGIN ... PRIVATE KEY`)
- AWS access key IDs (`AKIA...`)
- GCP service account JSON
- Database connection strings

**Warnings (commit allowed, flagged):**
- Internal IPs (RFC-1918: 10.x, 172.16-31.x, 192.168.x)
- Tailscale IPs (100.64.0.0/10)
- Email addresses
- US phone numbers
- High-entropy strings (potential undetected secrets)

## Currently installed repos

- `~/dev/docs` — <ORG_NAME> docs repo (installed 2026-03-11)
- `~/dev` — Main workspace repo (installed 2026-03-11)

## When a commit is blocked

1. Read the scanner output — it shows which pattern matched and on which line
2. Remove or replace the sensitive value with `<REDACTED>` or an env var reference
3. Re-stage the file and retry the commit

## Adding more repos

Run `install_hook.sh` for each new repo. The hook path to `pii_scan.py` is hardcoded at install time — if the skill moves, reinstall the hooks.

## Bypassing (emergency only)

```bash
git commit --no-verify -m "message"
```

Use only for false positives. Log the bypass reason in the commit message.
