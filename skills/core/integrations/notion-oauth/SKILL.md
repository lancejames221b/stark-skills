---
name: notion
description: Notion API for creating and managing pages, databases, and blocks.
category: integrations
runtimes: [claude]
pii_safe: true
---

# Notion OAuth MCP — Full Reference

Use `mcporter call notion-oauth.<tool>` for all Notion operations. **ALWAYS use notion-oauth** (not the token-based `notion` integration).

## ⚠️ CRITICAL: Use Wrapper Scripts for Create/Update

**mcporter CLI CANNOT reliably pass nested JSON objects** for `pages` (array of objects) or `data` (union type with `command` field). This causes endless "Invalid arguments" errors.

**ALWAYS use the wrapper scripts:**

```bash
# CREATE a page (with optional content file)
<LOCAL_PATH>/dev/skills/notion-oauth/create-page.sh "Title" "parent-uuid" [/path/to/content.md]

# UPDATE a page (insert, replace, replace-range, props)
<LOCAL_PATH>/dev/skills/notion-oauth/update-page.sh insert PAGE_ID "anchor text..." /path/to/content.md
<LOCAL_PATH>/dev/skills/notion-oauth/update-page.sh replace PAGE_ID /path/to/content.md
<LOCAL_PATH>/dev/skills/notion-oauth/update-page.sh replace-range PAGE_ID "old text..." /path/to/new-content.md
<LOCAL_PATH>/dev/skills/notion-oauth/update-page.sh props PAGE_ID '{"title":"New Title"}'
```

**These scripts use Python internally to construct proper JSON and call mcporter.** They handle all escaping. Don't waste time trying to pass nested JSON through mcporter CLI directly.

**What DOES work directly with mcporter CLI:**
- `notion-fetch` (simple string params): `mcporter call notion-oauth.notion-fetch id:"PAGE_UUID"`
- `notion-search` (simple string params): `mcporter call notion-oauth.notion-search query:"search term"`
- `notion-get-comments`, `notion-get-users`, `notion-get-teams` (simple params)

## Available Tools

| Tool | Purpose |
|------|---------|
| `notion-search` | Search pages, databases, connected sources |
| `notion-fetch` | Get full page/database content by ID or URL |
| `notion-create-pages` | Create one or more pages |
| `notion-update-page` | Update page properties or content |
| `notion-move-pages` | Move pages to a new parent |
| `notion-duplicate-page` | Duplicate a page |
| `notion-create-database` | Create a database with schema |
| `notion-update-data-source` | Update database properties/schema |
| `notion-create-comment` | Add a comment to a page |
| `notion-get-comments` | Get all comments on a page |
| `notion-get-teams` | List teamspaces |
| `notion-get-users` | List workspace users |
| `notion-query-database-view` | Query a database view |

---

## 1. Search (`notion-search`)

```bash
# Semantic search across workspace + connected sources (Slack, Drive, GitHub, Jira, Linear, etc.)
mcporter call notion-oauth.notion-search query="quarterly report"

# Filter by date range
mcporter call notion-oauth.notion-search query="project updates" \
  filters:'{"created_date_range":{"start_date":"2024-01-01","end_date":"2025-01-01"}}'

# Search within a specific page
mcporter call notion-oauth.notion-search query="action items" page_url="<NOTION_PAGE_ID>"

# Force workspace-only (faster) or AI search
mcporter call notion-oauth.notion-search query="meeting notes" content_search_mode="workspace_search"

# Search users
mcporter call notion-oauth.notion-search query="lance@<ORG_DOMAIN>" query_type="user"

# Search within a database (use data_source_url from fetch output)
mcporter call notion-oauth.notion-search query="bug fix" data_source_url="collection://f336d0bc-..."
```

**Returns:** Page titles, IDs, URLs, snippets. Use `notion-fetch` to get full content.

---

## 2. Fetch (`notion-fetch`)

```bash
# By page ID (with or without dashes)
mcporter call notion-oauth.notion-fetch id="<NOTION_PAGE_ID>"

# By URL
mcporter call notion-oauth.notion-fetch id="https://www.notion.so/<NOTION_PAGE_ID>"
```

**Returns:** Full page content in Notion-flavoured Markdown, including:
- Page properties
- All content blocks
- Child pages/databases as `<page url="...">` or `<database url="...">` tags
- Data source info as `<data-source url="collection://...">` tags

**Always fetch before updating** to understand existing content structure.

---

## 3. Create Pages (`notion-create-pages`)

### Schema

```json
{
  "pages": [
    {
      "properties": {
        "title": "Page Title"
      },
      "content": "# Heading\n\nMarkdown content here"
    }
  ],
  "parent": {
    "page_id": "parent-page-uuid"
  }
}
```

### Key Rules

- `pages` is an **array of objects**, each with optional `properties` and `content`
- For pages outside a database: only `title` property is allowed
- For pages inside a database: use property names from the database schema
- `content` is a string in Notion-flavoured Markdown
- `parent` can be `{"page_id": "..."}`, `{"database_id": "..."}`, or `{"data_source_id": "..."}`
- Up to 100 pages per call

### Common LLM Mistakes (⚠️ AVOID THESE)

The notion-create-pages schema has tripped up many LLMs. Here are the 6 most common errors:

#### 1. Missing `pages` parameter entirely
❌ **WRONG:**
```bash
mcporter call notion-oauth.notion-create-pages title="My Page" parent_page_id="abc123"
```

✅ **CORRECT:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"My Page"}}]' \
  'parent={"page_id":"abc123"}'
```

#### 2. Using flat key names instead of nested `properties.title`
❌ **WRONG:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"title":"My Page","parent_page_id":"abc123"}]'
```

✅ **CORRECT:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"My Page"}}]' \
  'parent={"page_id":"abc123"}'
```

**Why:** The title must be nested inside the `properties` object. Parent is a separate top-level parameter.

#### 3. Using camelCase (parentPageId, pageTitle, pageContent)
❌ **WRONG:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"pageTitle":"My Page"}]' \
  'parentPageId="abc123"'
```

✅ **CORRECT:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"My Page"}}]' \
  'parent={"page_id":"abc123"}'
```

**Why:** The API uses snake_case (`page_id`) and specific key names (`properties.title`, not `pageTitle`).

#### 4. Passing strings instead of objects in pages array
❌ **WRONG:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=["My Page"]' \
  'parent={"page_id":"abc123"}'
```

✅ **CORRECT:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"My Page"}}]' \
  'parent={"page_id":"abc123"}'
```

**Why:** Each element in `pages` must be an object with a `properties` field.

#### 5. Wrong type for content field
❌ **WRONG:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"My Page"},"content":{"markdown":"# Hello"}}]' \
  'parent={"page_id":"abc123"}'
```

✅ **CORRECT:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"My Page"},"content":"# Hello\n\nContent here"}]' \
  'parent={"page_id":"abc123"}'
```

**Why:** `content` is a plain string (Notion-flavoured Markdown), not an object.

#### 6. Incomplete mcporter commands
❌ **WRONG:**
```bash
mcporter call notion-oauth.notion-create-pages --title "My Page"
```

✅ **CORRECT:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"My Page"}}]' \
  'parent={"page_id":"abc123"}'
```

**Why:** mcporter uses `key=value` syntax for arguments, not `--flag` syntax. Both `pages` and `parent` are required.

---

### Quick Reference: Correct Schema Pattern

**Minimal page (title only):**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"TITLE_HERE"}}]' \
  'parent={"page_id":"PARENT_UUID"}'
```

**With content:**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"TITLE_HERE"},"content":"# Heading\n\nMarkdown content"}]' \
  'parent={"page_id":"PARENT_UUID"}'
```

**Use the wrapper script to avoid mistakes:**
```bash
<LOCAL_PATH>/dev/skills/notion-oauth/create-page.sh "Page Title" "parent-uuid" [content-file]
```

### mcporter Syntax

The challenge is passing nested JSON through mcporter CLI. Use these patterns:

**Pattern A: Simple page (short content)**
```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"My Page"},"content":"# Hello\n\nContent here"}]' \
  'parent={"page_id":"<UUID>"}'
```

**Pattern B: Long content via Python helper**
```bash
python3 << 'PYEOF'
import json, subprocess

content = """# My Long Page

## Section 1
Lots of content here...

## Section 2
More content...
"""

pages = [{"properties": {"title": "My Page Title"}, "content": content}]
parent = {"page_id": "<UUID>"}

# Build mcporter command
pages_json = json.dumps(pages)
parent_json = json.dumps(parent)

cmd = f"mcporter call notion-oauth.notion-create-pages 'pages={pages_json}' 'parent={parent_json}'"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)
PYEOF
```

**Pattern C: Create page, then update content separately**
```bash
# Step 1: Create empty page with title
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"Investigation Tracker"}}]' \
  'parent={"page_id":"<UUID>"}'

# Step 2: Update with full content (see section 4)
mcporter call notion-oauth.notion-update-page \
  'data={"page_id":"NEW_PAGE_ID","command":"replace_content","new_str":"# Full content..."}'
```

**Pattern D: stdin JSON (most reliable for large content)**
```bash
python3 -c "
import json, subprocess
content = open('/tmp/my-content.md').read()
pages_json = json.dumps([{'properties':{'title':'My Page'},'content':content}])
parent_json = json.dumps({'page_id':'PARENT_ID'})
subprocess.run(['mcporter','call','notion-oauth.notion-create-pages',
    f'pages={pages_json}', f'parent={parent_json}'], check=True)
"
```

### In a Database

```bash
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"title":"Bug Fix","status":"In Progress","priority":3}}]' \
  'parent={"database_id":"DATABASE_UUID"}'
```

---

## 4. Update Page (`notion-update-page`)

All updates go through the `data` parameter with a `command` field.

### 4a. Update Properties

```bash
mcporter call notion-oauth.notion-update-page \
  'data={"page_id":"PAGE_UUID","command":"update_properties","properties":{"title":"New Title"}}'
```

Database pages support all property types:
```json
{
  "page_id": "...",
  "command": "update_properties",
  "properties": {
    "title": "Updated Title",
    "status": "Done",
    "priority": 5,
    "checkbox": "__YES__",
    "date:deadline:start": "2024-12-25",
    "date:deadline:is_datetime": 0
  }
}
```

### 4b. Replace All Content

```bash
mcporter call notion-oauth.notion-update-page \
  'data={"page_id":"PAGE_UUID","command":"replace_content","new_str":"# New Content\n\nReplaces everything."}'
```

For long content, use the Python helper:
```bash
python3 -c "
import json, subprocess
content = open('/tmp/page-content.md').read()
data = json.dumps({'page_id':'PAGE_UUID','command':'replace_content','new_str':content})
subprocess.run(['mcporter','call','notion-oauth.notion-update-page',f'data={data}'], check=True)
"
```

### 4c. Replace Specific Content Range

```bash
mcporter call notion-oauth.notion-update-page \
  'data={"page_id":"PAGE_UUID","command":"replace_content_range","selection_with_ellipsis":"# Old Section...end of section","new_str":"# New Section\nUpdated content"}'
```

**`selection_with_ellipsis`:** First ~10 chars + `...` + last ~10 chars of the content to replace. Must be unique.

### 4d. Insert Content After

```bash
mcporter call notion-oauth.notion-update-page \
  'data={"page_id":"PAGE_UUID","command":"insert_content_after","selection_with_ellipsis":"## Previous section...","new_str":"\n## New Section\nInserted content"}'
```

### Content Preservation

- `replace_content` and `replace_content_range` check for child pages/databases
- If any would be deleted, the operation fails with a list of affected items
- Include child references in `new_str` as `<page url="...">` tags to preserve them
- Set `"allow_deleting_content": true` only after user confirmation

---

## 5. Move Pages (`notion-move-pages`)

```bash
mcporter call notion-oauth.notion-move-pages \
  'page_or_database_ids=["PAGE_UUID_1","PAGE_UUID_2"]' \
  'new_parent={"page_id":"TARGET_PAGE_UUID"}'
```

---

## 6. Create Database (`notion-create-database`)

```bash
mcporter call notion-oauth.notion-create-database \
  title:'[{"type":"text","text":{"content":"Task Tracker"}}]' \
  'parent={"page_id":"PARENT_UUID"}' \
  'properties={"Status":{"type":"status","status":{"options":[{"name":"Not Started"},{"name":"In Progress"},{"name":"Done"}]}},"Priority":{"type":"number","number":{"format":"number"}}}'
```

---

## 7. Comments (`notion-create-comment`, `notion-get-comments`)

```bash
# Get comments
mcporter call notion-oauth.notion-get-comments page_id="PAGE_UUID"

# Add comment
mcporter call notion-oauth.notion-create-comment \
  'parent={"page_id":"PAGE_UUID"}' \
  'rich_text=[{"type":"text","text":{"content":"This looks good!"}}]'
```

---

## 8. Users & Teams

```bash
mcporter call notion-oauth.notion-get-users
mcporter call notion-oauth.notion-get-users query="lance"
mcporter call notion-oauth.notion-get-teams
```

---

## 9. Query Database View (`notion-query-database-view`)

```bash
# Use the view URL from Notion (with ?v= parameter)
mcporter call notion-oauth.notion-query-database-view \
  view_url="https://www.notion.so/workspace/db-id?v=view-id"
```

---

## Common Workflows

### Create a page with full content

```bash
# 1. Write content to temp file
cat > /tmp/notion-content.md << 'EOF'
## Section 1
Content here...

## Section 2
More content...
EOF

# 2. Create page with content via Python
python3 -c "
import json, subprocess
content = open('/tmp/notion-content.md').read()
pages = json.dumps([{'properties':{'title':'My Page'},'content':content}])
parent = json.dumps({'page_id':'PARENT_UUID'})
result = subprocess.run(
    ['mcporter','call','notion-oauth.notion-create-pages',f'pages={pages}',f'parent={parent}'],
    capture_output=True, text=True
)
print(result.stdout[-500:] if result.stdout else '')
print(result.stderr[-500:] if result.stderr else '')
"
```

### Find and update an existing page

```bash
# 1. Search for it
mcporter call notion-oauth.notion-search query="investigation tracker"

# 2. Fetch current content
mcporter call notion-oauth.notion-fetch id="PAGE_UUID"

# 3. Update specific section
mcporter call notion-oauth.notion-update-page \
  'data={"page_id":"PAGE_UUID","command":"replace_content_range","selection_with_ellipsis":"## Old Section...end of old","new_str":"## Updated Section\nNew content"}'
```

### Add a row to a database

```bash
# 1. Fetch database to see schema
mcporter call notion-oauth.notion-fetch id="DATABASE_UUID"

# 2. Create page in database with properties matching schema
mcporter call notion-oauth.notion-create-pages \
  'pages=[{"properties":{"Name":"New Task","Status":"In Progress","Priority":1}}]' \
  'parent={"database_id":"DATABASE_UUID"}'
```

---

## Known Parent Pages

| Name | ID | Use For |
|------|-----|---------|
| <ORG_NAME> Notes | <ORG_ID> | General work notes |
| <ORG_NAME> Tasks | <ORG_ID> | Task tracking |
| Security Command Centre | <UUID> | Security work |

---

## Common LLM Mistakes (How to Fix Schema Errors)

When using <PROJECT_NAME> to call `notion-create-pages`, the LLM frequently generates **wrong argument schemas**. This causes validation errors that look like "hanging" but are actually fast failures followed by retries.

### The 6 Failure Patterns (Opus Diagnosis, Feb 11 2026)

**1. Missing `pages` parameter entirely**
```json
// ❌ WRONG - pages parameter is missing
{
  "title": "My Page",
  "parent_page_id": "de528ff9-...",
  "content": "..."
}

// ✅ RIGHT - pages is an array of objects
{
  "pages": [{"properties": {"title": "My Page"}, "content": "..."}],
  "parent": {"page_id": "de528ff9-..."}
}
```

**2. Using flat key names instead of nested `properties`**
```json
// ❌ WRONG - flat structure
{"pages": [{"title": "My Page", "parent_page_id": "...", "format": "..."}]}

// ✅ RIGHT - nested properties object
{"pages": [{"properties": {"title": "My Page"}}], "parent": {"page_id": "..."}}
```

**3. Using camelCase invented field names**
```json
// ❌ WRONG - camelCase doesn't exist
{"pages": [{"parentPageId": "...", "pageTitle": "...", "pageContent": "..."}]}

// ✅ RIGHT - use properties + content
{"pages": [{"properties": {"title": "..."}, "content": "..."}], "parent": {"page_id": "..."}}
```

**4. Passing strings instead of objects in pages array**
```json
// ❌ WRONG - strings in pages array
{"pages": ["Title 1", "Title 2"]}

// ✅ RIGHT - objects with properties
{"pages": [{"properties": {"title": "Title 1"}}, {"properties": {"title": "Title 2"}}]}
```

**5. Wrong type for content field**
```json
// ❌ WRONG - content as object/array
{"pages": [{"properties": {"title": "..."}, "content": {"text": "..."}}]}

// ✅ RIGHT - content as string
{"pages": [{"properties": {"title": "..."}, "content": "# Heading\\n\\nContent"}]}
```

**6. Incomplete or malformed mcporter command**
```bash
# ❌ WRONG - bare command with no args
mcporter call notion-oauth.notion-create-pages

# ✅ RIGHT - full command with proper JSON
mcporter call notion-oauth.notion-create-pages 'pages=[{"properties":{"title":"My Page"}}]' 'parent={"page_id":"de528ff9-..."}'
```

### Solution: Use the Wrapper Scripts

Instead of fighting with LLM schema generation, use the provided wrapper scripts:

```bash
# CREATE: Simple page with title only
<LOCAL_PATH>/dev/skills/notion-oauth/create-page.sh "My Page Title" "<NOTION_ID>"

# CREATE: Page with content from file
<LOCAL_PATH>/dev/skills/notion-oauth/create-page.sh "My Page" "de528ff9-..." /tmp/content.md

# UPDATE: Insert content after an anchor point
<LOCAL_PATH>/dev/skills/notion-oauth/update-page.sh insert "PAGE_UUID" "## Last Section..." /tmp/new-section.md

# UPDATE: Replace all content
<LOCAL_PATH>/dev/skills/notion-oauth/update-page.sh replace "PAGE_UUID" /tmp/full-content.md

# UPDATE: Replace specific range
<LOCAL_PATH>/dev/skills/notion-oauth/update-page.sh replace-range "PAGE_UUID" "## Old Section...end of old" /tmp/new-section.md

# UPDATE: Change properties
<LOCAL_PATH>/dev/skills/notion-oauth/update-page.sh props "PAGE_UUID" '{"title":"New Title"}'
```

The wrappers handle all JSON construction internally via Python subprocess. No schema errors, no retries, no mcporter CLI JSON parsing issues.

---

## Troubleshooting

**"Invalid arguments" / schema errors:**
- See **Common LLM Mistakes** section above
- Use the wrapper script (`create-page.sh`) to avoid schema construction issues
- If using mcporter directly: `pages` must be an array of objects, not strings
- Each page object must have `properties` (object with title) and optionally `content` (string)

**Long content fails:**
- Shell escaping breaks with special characters in markdown
- Use the Python subprocess pattern (Pattern B/D) for reliable large content
- Or use the wrapper script which handles escaping automatically

**"Requires membership":**
- You're using the wrong Notion integration. Use `notion-oauth`, not `notion`.

**Content not rendering:**
- Notion uses its own Markdown flavour. Fetch `notion://docs/enhanced-markdown-spec` for the spec.
- Standard markdown tables, bold, lists all work.
- Use `---` for dividers, `- [ ]` for checkboxes.

---

*Last updated: Feb 11, 2026*
