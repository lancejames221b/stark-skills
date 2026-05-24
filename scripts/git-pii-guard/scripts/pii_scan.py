#!/usr/bin/env python3
"""
pii_scan.py — Scan text/files/git diffs for PII and credentials.
Exit 0 = clean. Exit 1 = violations found.

Usage:
  pii_scan.py --diff          # scan git staged diff (pre-commit hook mode)
  pii_scan.py --file FILE     # scan a specific file
  pii_scan.py --text TEXT     # scan a string
  pii_scan.py --report        # print full match details (default: summary only)
"""

import re
import sys
import argparse
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Pattern registry
# Each entry: (name, regex, severity)
# severity: "block" = fail commit, "warn" = print but allow
# ---------------------------------------------------------------------------
PATTERNS = [
    # Credentials & tokens
    ("api_key",         r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}',      "block"),
    ("password_assign", r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{4,}["\']',           "block"),
    ("secret_assign",   r'(?i)(secret|token|auth[_-]?token)\s*[=:]\s*["\'][^"\']{8,}["\']',   "block"),
    ("pgpassword",      r'PGPASSWORD\s*=\s*["\']?[^\s"\']{4,}',                               "block"),
    ("bearer_token",    r'(?i)bearer\s+[A-Za-z0-9\-._~+/]{20,}',                              "block"),

    # Private keys
    ("private_key",     r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY',                        "block"),

    # Cloud credentials
    ("aws_key",         r'(?i)(AKIA|AIPA|ASIA)[A-Z0-9]{16}',                                  "block"),
    ("gcp_service_acct",r'"type"\s*:\s*"service_account"',                                    "block"),

    # Internal IPs (RFC-1918 ranges)
    ("internal_ip",     r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b', "warn"),

    # Tailscale IPs (100.64.0.0/10)
    ("tailscale_ip",    r'\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b',     "warn"),

    # Email addresses
    ("email",           r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b',            "warn"),

    # US phone numbers
    ("phone_us",        r'\b(\+1[\s\-]?)?\(?\d{3}\)?[\s\-]\d{3}[\s\-]\d{4}\b',               "warn"),

    # Database connection strings
    ("db_connstr",      r'(?i)(postgres|mysql|mongodb|redis)://[^\s"\'<>]{8,}',               "block"),

    # Generic high-entropy strings (long base64/hex blobs) — heuristic
    ("high_entropy",    r'(?<![A-Za-z0-9/+])[A-Za-z0-9/+=]{40,}(?![A-Za-z0-9/+=])',         "warn"),
]

# File extensions to skip entirely (binary / generated)
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz",
    ".pyc", ".pyo", ".so", ".dll", ".exe",
    ".lock",   # package lock files (full of hashes)
}

# Paths to always skip
SKIP_PATHS = {
    "package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock",
    ".git",
}


def should_skip(path: str) -> bool:
    p = Path(path)
    if p.suffix.lower() in SKIP_EXTENSIONS:
        return True
    for part in p.parts:
        if part in SKIP_PATHS:
            return True
    return False


def scan_text(text: str, source: str = "<text>") -> list[dict]:
    """Return list of violation dicts."""
    violations = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for name, pattern, severity in PATTERNS:
            for m in re.finditer(pattern, line):
                violations.append({
                    "source": source,
                    "line": line_no,
                    "pattern": name,
                    "severity": severity,
                    "match": m.group(0)[:120],   # truncate for safety
                    "context": line.strip()[:160],
                })
    return violations


def get_staged_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--cached", "--unified=0"],
        capture_output=True, text=True
    )
    return result.stdout


def parse_diff_chunks(diff: str) -> list[tuple[str, str]]:
    """Return list of (filename, added_lines_text) from a unified diff."""
    chunks = []
    current_file = None
    added_lines = []

    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            if current_file and added_lines:
                chunks.append((current_file, "\n".join(added_lines)))
            current_file = line[6:]
            added_lines = []
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])  # strip leading +

    if current_file and added_lines:
        chunks.append((current_file, "\n".join(added_lines)))

    return chunks


def format_violation(v: dict, verbose: bool = False) -> str:
    icon = "🚫" if v["severity"] == "block" else "⚠️ "
    loc = f"{v['source']}:{v['line']}"
    msg = f"{icon} [{v['pattern']}] {loc}"
    if verbose:
        msg += f"\n   match:   {v['match']}\n   context: {v['context']}"
    return msg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff",   action="store_true", help="Scan git staged diff")
    parser.add_argument("--file",   help="Scan a file")
    parser.add_argument("--text",   help="Scan a string")
    parser.add_argument("--report", action="store_true", help="Verbose output")
    args = parser.parse_args()

    all_violations = []

    if args.diff:
        diff = get_staged_diff()
        for filename, added in parse_diff_chunks(diff):
            if should_skip(filename):
                continue
            all_violations.extend(scan_text(added, source=filename))

    elif args.file:
        if should_skip(args.file):
            print(f"Skipped (binary/lock): {args.file}")
            sys.exit(0)
        text = Path(args.file).read_text(errors="replace")
        all_violations.extend(scan_text(text, source=args.file))

    elif args.text:
        all_violations.extend(scan_text(args.text, source="<stdin>"))

    else:
        parser.print_help()
        sys.exit(0)

    if not all_violations:
        print("✅  No PII/credentials detected.")
        sys.exit(0)

    blocks = [v for v in all_violations if v["severity"] == "block"]
    warns  = [v for v in all_violations if v["severity"] == "warn"]

    print(f"\n{'='*60}")
    print(f"PII/Credential scan: {len(blocks)} blocking, {len(warns)} warnings")
    print(f"{'='*60}")

    for v in all_violations:
        print(format_violation(v, verbose=args.report))

    if blocks:
        print(f"\n🚫  Commit BLOCKED — {len(blocks)} credential/PII pattern(s) found.")
        print("    Remove the sensitive values and try again.")
        print("    Use <REDACTED> or environment variables instead.\n")
        sys.exit(1)
    else:
        print(f"\n⚠️   {len(warns)} warning(s) — review before pushing.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
