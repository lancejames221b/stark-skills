#!/bin/bash
# update-page.sh - Wrapper for notion-oauth.notion-update-page
# Usage:
#   update-page.sh insert PAGE_ID "selection..." /path/to/content.md
#   update-page.sh replace PAGE_ID /path/to/content.md
#   update-page.sh replace-range PAGE_ID "selection..." /path/to/content.md
#   update-page.sh props PAGE_ID '{"title":"New Title"}'
#
# Commands:
#   insert       - Insert content after a selection anchor
#   replace      - Replace ALL page content
#   replace-range - Replace a specific content range
#   props        - Update page properties

set -euo pipefail

if [ $# -lt 3 ]; then
    echo "Usage:" >&2
    echo "  $0 insert PAGE_ID \"selection...\" /path/to/content.md" >&2
    echo "  $0 replace PAGE_ID /path/to/content.md" >&2
    echo "  $0 replace-range PAGE_ID \"selection...\" /path/to/content.md" >&2
    echo "  $0 props PAGE_ID '{\"title\":\"New Title\"}'" >&2
    exit 1
fi

COMMAND="$1"
PAGE_ID="$2"

export PAGE_ID COMMAND

case "$COMMAND" in
    insert)
        if [ $# -lt 4 ]; then
            echo "Error: insert requires PAGE_ID, selection, and content file" >&2
            exit 1
        fi
        export SELECTION="$3"
        export CONTENT=$(cat "$4")
        ;;
    replace)
        export CONTENT=$(cat "$3")
        ;;
    replace-range)
        if [ $# -lt 4 ]; then
            echo "Error: replace-range requires PAGE_ID, selection, and content file" >&2
            exit 1
        fi
        export SELECTION="$3"
        export CONTENT=$(cat "$4")
        ;;
    props)
        export PROPS_JSON="$3"
        ;;
    *)
        echo "Error: Unknown command '$COMMAND'. Use: insert, replace, replace-range, props" >&2
        exit 1
        ;;
esac

python3 << 'PYEOF'
import json
import subprocess
import sys
import os

page_id = os.environ['PAGE_ID']
command = os.environ['COMMAND']

if command == 'insert':
    data = {
        "page_id": page_id,
        "command": "insert_content_after",
        "selection_with_ellipsis": os.environ['SELECTION'],
        "new_str": os.environ['CONTENT']
    }
elif command == 'replace':
    data = {
        "page_id": page_id,
        "command": "replace_content",
        "new_str": os.environ['CONTENT']
    }
elif command == 'replace-range':
    data = {
        "page_id": page_id,
        "command": "replace_content_range",
        "selection_with_ellipsis": os.environ['SELECTION'],
        "new_str": os.environ['CONTENT']
    }
elif command == 'props':
    data = {
        "page_id": page_id,
        "command": "update_properties",
        "properties": json.loads(os.environ['PROPS_JSON'])
    }
else:
    print(f"Unknown command: {command}", file=sys.stderr)
    sys.exit(1)

data_json = json.dumps(data)

cmd = [
    'mcporter', 'call', 'notion-oauth.notion-update-page',
    f'data={data_json}'
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("✓ Page updated successfully")
    if result.stdout:
        # Show truncated output
        output = result.stdout[:500]
        print(output)
    sys.exit(0)
except subprocess.CalledProcessError as e:
    print(f"✗ Error updating page:", file=sys.stderr)
    print(e.stderr[:500] if e.stderr else "No error details", file=sys.stderr)
    sys.exit(1)
PYEOF
