# Linear Content Management Reference

Guide for documents, comments, attachments, and content features.

## Table of Contents
- [Documents](#documents)
- [Comments](#comments)
- [Attachments](#attachments)
- [Images](#images)
- [Search Documentation](#search-documentation)

## Documents

Linear documents are Markdown-based pages for specs, RFCs, and long-form content.

### Listing Documents

```bash
mcporter call linear.list_documents \
  projectId:"project-uuid" \
  orderBy:"updatedAt" \
  limit:50
```

**Filter Parameters:**
- `query` - Search query
- `projectId` - Filter by project
- `initiativeId` - Filter by initiative
- `creatorId` - Filter by creator
- `createdAt` / `updatedAt` - Date filters
- `includeArchived` - Include archived
- `limit` / `cursor` / `orderBy` - Pagination

### Getting Document

```bash
mcporter call linear.get_document id:"doc-uuid-or-slug"
```

Can query by:
- Document UUID
- Document slug (URL-friendly name)

### Creating Documents

```bash
mcporter call linear.create_document \
  title:"API Design RFC" \
  content:"# API Design

## Overview
Proposal for new REST API endpoints.

## Endpoints

### POST /api/search
Search messages with filters.

**Request:**
\`\`\`json
{
  \"query\": \"bitcoin\",
  \"limit\": 20
}
\`\`\`

**Response:**
\`\`\`json
{
  \"results\": [...]
}
\`\`\`

## Security
- API key authentication
- Rate limiting

## Timeline
- Week 1: Design review
- Week 2: Implementation
- Week 3: Testing" \
  project:"<PROJECT_NAME>" \
  icon:"📄" \
  color:"#4CAF50"
```

**Parameters:**
- `title` - Required: document title
- `content` - Markdown content
- `project` - Project name or ID
- `issue` - Issue ID or identifier (link to issue)
- `icon` - Icon emoji
- `color` - Hex color

### Updating Documents

```bash
mcporter call linear.update_document \
  id:"doc-uuid" \
  content:"# Updated Content

New content here..."
```

**All parameters same as create, except:**
- `id` - Required: document ID or slug

### Document Icons

Use emoji:
- 📄 - Generic document
- 📊 - Reports, analytics
- 🎨 - Design specs
- ⚙️ - Technical specs
- 📋 - Checklists, procedures
- 🔒 - Security docs

### Documents vs Issues

| Feature | Documents | Issues |
|---------|-----------|--------|
| Length | Long-form | Short-form |
| Purpose | Specs, RFCs, guides | Tasks, bugs |
| Versioning | Full history | Comments + updates |
| Status | N/A | Workflow states |
| Assignment | N/A | Assignee |
| Best for | Planning, design | Execution, tracking |

**When to use each:**
- **Document:** Architecture RFC, API design, project spec
- **Issue:** Implement feature, fix bug, write tests

## Comments

Comments provide discussion on issues.

### Listing Comments

```bash
mcporter call linear.list_comments issueId:"issue-uuid"
```

Returns all comments on an issue.

### Creating Comments

```bash
mcporter call linear.create_comment \
  issueId:"issue-uuid" \
  body:"Updated implementation based on feedback:
- Added error handling
- Improved performance
- Updated tests"
```

**Parameters:**
- `issueId` - Required: issue UUID
- `body` - Required: Markdown content
- `parentId` - Optional: parent comment ID (for replies)

### Reply to Comment

```bash
mcporter call linear.create_comment \
  issueId:"issue-uuid" \
  parentId:"comment-uuid" \
  body:"Good point, will update the PR"
```

### Comment Formatting

Use Markdown:

```markdown
# Heading

**Bold** and *italic*

- Bullet lists
- Work great

1. Numbered
2. Lists too

`inline code`

\`\`\`python
# Code blocks
def hello():
    print("world")
\`\`\`

[Links](https://example.com)

> Blockquotes

@mention users
```

### Comment Use Cases

**Progress updates:**
```bash
mcporter call linear.create_comment \
  issueId:"uuid" \
  body:"✅ ES cluster deployed
✅ Data indexed (24.5M messages)
⏳ Search API in progress"
```

**Discussion:**
```bash
mcporter call linear.create_comment \
  issueId:"uuid" \
  body:"Should we use Redis for caching?

Pros:
- Fast
- Mature

Cons:
- Additional infrastructure
- Complexity

Thoughts?"
```

**Technical details:**
```bash
mcporter call linear.create_comment \
  issueId:"uuid" \
  body:"Stack trace from error:

\`\`\`
Error: Connection timeout
  at connect (lib/db.js:45)
  at query (lib/db.js:78)
\`\`\`

Investigation notes:
- Occurs under high load
- Cloud SQL connection pool saturated
- Need to increase pool size"
```

## Attachments

Attachments are files linked to issues.

### Getting Attachment

```bash
mcporter call linear.get_attachment id:"attachment-uuid"
```

Returns attachment metadata and content.

### Creating Attachment

```bash
mcporter call linear.create_attachment \
  issue:"ENG-123" \
  base64Content:"[base64-encoded-file]" \
  filename:"screenshot.png" \
  contentType:"image/png" \
  title:"Error screenshot"
```

**Parameters:**
- `issue` - Required: issue ID or identifier
- `base64Content` - Required: base64-encoded file
- `filename` - Required: filename
- `contentType` - Required: MIME type
- `title` - Optional: attachment title
- `subtitle` - Optional: subtitle

### Deleting Attachment

```bash
mcporter call linear.delete_attachment id:"attachment-uuid"
```

### Common MIME Types

| File Type | MIME Type |
|-----------|-----------|
| PNG | image/png |
| JPEG | image/jpeg |
| PDF | application/pdf |
| Text | text/plain |
| JSON | application/json |
| ZIP | application/zip |

### Attachment Workflow

```bash
# 1. Read file and encode
FILE_CONTENT=$(base64 -i screenshot.png)

# 2. Upload to issue
mcporter call linear.create_attachment \
  issue:"ENG-123" \
  base64Content:"$FILE_CONTENT" \
  filename:"screenshot.png" \
  contentType:"image/png" \
  title:"Bug screenshot"

# 3. Comment about attachment
mcporter call linear.create_comment \
  issueId:"issue-uuid" \
  body:"Screenshot attached showing the error"
```

## Images

Extract images from Markdown content in issues/comments/documents.

### Extract Images

```bash
mcporter call linear.extract_images \
  markdown:"![Screenshot](linear-attachment://uuid)

More content with ![another](linear-attachment://uuid2)"
```

**Use case:** View images embedded in:
- Issue descriptions
- Comments
- Documents

**Returns:** Image data as viewable content

### Image References in Markdown

Linear uses special attachment URLs:
```markdown
![Description](linear-attachment://attachment-uuid)
```

To view these images, pass the markdown to `extract_images`.

## Search Documentation

Search Linear's official documentation for feature help.

### Search Docs

```bash
mcporter call linear.search_documentation \
  query:"keyboard shortcuts" \
  page:1
```

**Parameters:**
- `query` - Required: search query
- `page` - Optional: page number

**Use cases:**
- "How do I create a custom view?"
- "What keyboard shortcuts are available?"
- "How does cycle planning work?"
- "Can I link GitHub PRs?"

### Documentation Topics

Common searches:
- Keyboard shortcuts
- Integrations (GitHub, Slack, etc.)
- Custom views
- Automations
- Workflow states
- Notifications
- API usage

## Content Best Practices

### Issue Descriptions

**Good issue description:**
```markdown
## Problem
Search is slow (>2s response time)

## Expected
<100ms p95 latency

## Current Status
- ✅ Elasticsearch deployed
- ⏳ Indexing in progress
- ⏳ API endpoints pending

## Acceptance Criteria
- [ ] All data indexed
- [ ] API returns results <100ms
- [ ] Tests passing

## Technical Notes
Index: <PROJECT_NAME>
Cluster: d6df4f4edcb1466e8bd829b5656f19db
```

### Document Structure

**Good document:**
```markdown
# Title

## Overview
Brief summary (1-2 paragraphs)

## Problem Statement
What we're solving

## Proposed Solution
How we'll solve it

## Technical Design
Architecture, APIs, schemas

## Security Considerations
Threats and mitigations

## Timeline
Phases and dates

## Open Questions
What needs discussion

## References
Links to related docs/issues
```

### Comment Quality

**Good comment:**
- Concise
- Actionable
- Formatted well
- Links to context

**Bad comment:**
- Vague ("looks good")
- Walls of text
- No structure
- Missing context
