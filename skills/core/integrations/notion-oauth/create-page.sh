#!/bin/bash
# create-page.sh - Wrapper for notion-oauth.notion-create-pages
# Usage: create-page.sh "Title" "parent-page-id" [content-file]
#
# Constructs proper JSON schema and calls mcporter with correct nested structure.
# Returns page ID on success.

set -euo pipefail

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 \"Title\" \"parent-page-id\" [content-file]" >&2
    echo "" >&2
    echo "Arguments:" >&2
    echo "  Title          - Page title (required)" >&2
    echo "  parent-page-id - Parent page UUID (required)" >&2
    echo "  content-file   - Path to markdown content file (optional)" >&2
    echo "" >&2
    echo "Examples:" >&2
    echo "  $0 \"My New Page\" \"<UUID>\"" >&2
    echo "  $0 \"Project Notes\" \"<UUID>\" /tmp/notes.md" >&2
    exit 1
fi

TITLE="$1"
PARENT_ID="$2"
CONTENT_FILE="${3:-}"

# Read content if file provided
CONTENT=""
if [ -n "$CONTENT_FILE" ]; then
    if [ ! -f "$CONTENT_FILE" ]; then
        echo "Error: Content file not found: $CONTENT_FILE" >&2
        exit 1
    fi
    CONTENT=$(cat "$CONTENT_FILE")
fi

# Use Python to construct proper JSON and call mcporter
# This avoids shell escaping issues with special characters
export TITLE PARENT_ID CONTENT

python3 << 'PYEOF'
import json
import subprocess
import sys
import os
import re

# Get args from environment
title = os.environ['TITLE']
parent_id = os.environ['PARENT_ID']
content = os.environ.get('CONTENT', '')

# Construct proper nested schema
pages = [{
    "properties": {
        "title": title
    }
}]

# Add content if provided
if content:
    pages[0]["content"] = content

parent = {
    "page_id": parent_id
}

# Convert to JSON strings
pages_json = json.dumps(pages)
parent_json = json.dumps(parent)

# Call mcporter with proper schema
cmd = [
    'mcporter', 'call', 'notion-oauth.notion-create-pages',
    f'pages={pages_json}',
    f'parent={parent_json}'
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    output = result.stdout
    
    # Try to extract page ID from output
    # Output format includes: "id": "page-uuid"
    match = re.search(r'"id":\s*"([0-9a-f-]+)"', output)
    if match:
        page_id = match.group(1)
        print(f"✓ Page created successfully")
        print(f"Page ID: {page_id}")
        print(f"URL: https://www.notion.so/{page_id.replace('-', '')}")
    else:
        print("✓ Page created (could not extract ID from output)")
        print(output)
    
    sys.exit(0)
    
except subprocess.CalledProcessError as e:
    print(f"✗ Error creating page:", file=sys.stderr)
    print(e.stderr, file=sys.stderr)
    sys.exit(1)
    
except Exception as e:
    print(f"✗ Unexpected error: {e}", file=sys.stderr)
    sys.exit(1)

PYEOF
