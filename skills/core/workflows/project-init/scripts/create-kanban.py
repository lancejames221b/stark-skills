#!/usr/bin/env python3
"""
create-kanban.py — Create a Notion Kanban database with correct canonical columns.

Usage:
  python3 create-kanban.py --parent-page-id PAGE_UUID --project-name "Project Name"

Outputs (on success):
  DATABASE_ID=<uuid>
  DATABASE_URL=<url>

Canonical columns (in order):
  Backlog → Todo → In Progress → Blocked → In Review → Done → Canceled

Properties:
  Name (title), Status (select), Priority (select), Labels (multi-select),
  Due Date (date), Thread (url), Notes (rich_text)

DO NOT run any UPDATE/ALTER steps after creation. This script creates correctly
the first time using the full DDL schema.
"""

import argparse
import json
import subprocess
import sys


# ── Canonical DDL ──────────────────────────────────────────────────────────────
# Status columns in correct Kanban order.
# Colors: gray=backlog, blue=todo, yellow=in-progress, red=blocked,
#         orange=in-review, green=done, default=canceled
DDL_TEMPLATE = (
    'CREATE TABLE "{project_name} Kanban" ('
    '"Name" TITLE, '
    '"Status" SELECT('
    "'Backlog':gray, "
    "'Todo':blue, "
    "'In Progress':yellow, "
    "'Blocked':red, "
    "'In Review':orange, "
    "'Done':green, "
    "'Canceled':default"
    '), '
    '"Priority" SELECT('
    "'Urgent':red, "
    "'High':orange, "
    "'Normal':yellow, "
    "'Low':gray"
    '), '
    '"Labels" MULTI_SELECT('
    "'frontend', 'backend', 'infra', 'api', 'design', 'security', 'voice', 'discord'"
    '), '
    '"Due Date" DATE, '
    '"Thread" URL, '
    '"Notes" RICH_TEXT'
    ')'
)


def build_parent_json(page_id: str) -> str:
    """Build the parent JSON object for mcporter."""
    return json.dumps({"page_id": page_id})


def run_mcporter(schema: str, parent_json: str) -> dict:
    """
    Call mcporter to create the Notion database.
    Returns parsed JSON response dict, or raises on error.
    """
    cmd = [
        "mcporter", "call", "notion-oauth.notion-create-database",
        f"schema={schema}",
        f"parent={parent_json}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"mcporter exited {result.returncode}:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    raw = result.stdout.strip()
    if not raw:
        raise RuntimeError(f"mcporter returned empty output.\nSTDERR: {result.stderr}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse mcporter response as JSON: {exc}\nRaw: {raw[:500]}")


def extract_id_and_url(response: dict) -> tuple[str, str]:
    """
    Extract DATABASE_ID and DATABASE_URL from the Notion API response.
    Handles both direct API responses and mcporter-wrapped responses.
    """
    # mcporter may wrap the result under 'result' or 'data'
    data = response
    for key in ("result", "data"):
        if key in response and isinstance(response[key], dict):
            data = response[key]
            break

    # Extract ID
    db_id = data.get("id") or data.get("database_id") or ""
    if not db_id:
        raise RuntimeError(f"No 'id' found in response. Keys: {list(data.keys())}")

    # Normalize UUID format (add dashes if bare hex)
    db_id = db_id.strip()

    # Extract URL — Notion returns 'url' field
    db_url = data.get("url") or data.get("database_url") or ""
    if not db_url:
        # Build URL from ID if not returned
        bare_id = db_id.replace("-", "")
        db_url = f"https://www.notion.so/{bare_id}"

    return db_id, db_url


def main():
    parser = argparse.ArgumentParser(
        description="Create a Notion Kanban database with canonical columns."
    )
    parser.add_argument(
        "--parent-page-id",
        required=True,
        help="UUID of the Notion page to create the database inside.",
    )
    parser.add_argument(
        "--project-name",
        required=True,
        help="Project name (used as database title prefix).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the DDL and parent JSON without calling mcporter.",
    )
    args = parser.parse_args()

    project_name = args.project_name.strip()
    parent_page_id = args.parent_page_id.strip()

    if not project_name:
        print("ERROR: --project-name cannot be empty.", file=sys.stderr)
        sys.exit(1)
    if not parent_page_id:
        print("ERROR: --parent-page-id cannot be empty.", file=sys.stderr)
        sys.exit(1)

    schema = DDL_TEMPLATE.format(project_name=project_name)
    parent_json = build_parent_json(parent_page_id)

    if args.dry_run:
        print("=== DRY RUN ===")
        print(f"Schema: {schema}")
        print(f"Parent: {parent_json}")
        sys.exit(0)

    try:
        response = run_mcporter(schema, parent_json)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        db_id, db_url = extract_id_and_url(response)
    except RuntimeError as exc:
        print(f"ERROR: Could not extract DB info: {exc}", file=sys.stderr)
        print(f"Full response: {json.dumps(response, indent=2)}", file=sys.stderr)
        sys.exit(1)

    # Output in KEY=VALUE format for easy shell parsing
    print(f"DATABASE_ID={db_id}")
    print(f"DATABASE_URL={db_url}")


if __name__ == "__main__":
    main()
