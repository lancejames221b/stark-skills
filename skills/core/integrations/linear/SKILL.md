---
name: linear
description: Comprehensive Linear project management via MCP. Use when working with Linear for issue tracking, project management, status updates, team coordination, or any Linear task. Covers all 40 Linear MCP tools - issues (create/update/list/get/statuses/labels), projects (create/update/list/get/milestones/status-updates), initiatives (create/update/list/get/status-updates), documents (create/update/list/get), comments (create/list), attachments (create/delete/get), teams (list/get), users (list/get), cycles (list), and organization management. Use for daily standups, sprint planning, code reviews, bug triage, release management, OKRs, roadmaps, and all Linear workflows.
category: integrations
runtimes: [claude]
pii_safe: true
---

# Linear Skill

Complete Linear project management via Linear MCP. All 40 tools available for issues, projects, initiatives, documents, comments, teams, and organization management.

## ⚡ Defaults (NON-NEGOTIABLE — apply to every issue create/update)

1. **Assignee:** Always `<EMAIL_ADDRESS>` (<USER_NAME><USER_NAME>, ID: `<LINEAR_ID>`) unless explicitly told otherwise
2. **Priority:** Always `0` (No priority) unless explicitly specified
3. **Project:** Always ask which project before creating — never create without one. If context makes it obvious (e.g. in #<PROJECT_NAME> → <PROJECT_NAME> <PROJECT_NAME>), confirm rather than assume.

**Project quick-reference:**
- `<UUID>` — <PROJECT_NAME> <PROJECT_NAME>
- `<UUID>` — Self Service Alerting
- (run `mcporter call linear.list_projects` to find others)

**When creating any issue, always include:**
```bash
mcporter call linear.create_issue \
  title:"Issue title" \
  team:"Engineering" \
  assigneeId:"<LINEAR_ID>" \
  priority:0 \
  projectId:"[confirmed project ID]"
```

---

## Quick Start

### Issues

**Create:**
```bash
mcporter call linear.create_issue \
  title:"Issue title" \
  team:"Engineering" \
  assigneeId:"<LINEAR_ID>" \
  priority:0
```

**Update:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  state:"Completed"
```

**List:**
```bash
mcporter call linear.list_issues \
  assignee:"me" \
  state:"started" \
  limit:20
```

### Projects

**Create (use `save_project` — `create_project` does NOT exist):**
```bash
mcporter call linear.save_project \
  name:"Project name" \
  team:"Engineering" \
  state:"started" \
  lead:"me" \
  priority:2
```

> ⚠️ `create_project` will return "Tool not found". Always use `save_project` for both create and update.
> For updates, pass `id:"<project-id>"` — omitting `id` creates a new project.

**⚠️ DESCRIPTION NEWLINES — CRITICAL:**
Linear descriptions render literal `\n` if you pass escaped strings. Always use real newlines in the description arg:
```bash
# ✅ CORRECT — real newlines between lines
mcporter call linear.save_project \
  name:"My Project" \
  team:"Engineering" \
  description:"First paragraph

Second paragraph

- Bullet 1
- Bullet 2"

# ❌ WRONG — shows literal \n in Linear UI
mcporter call linear.save_project description:"Line 1\n\nLine 2"
```
Full guide: `contexts/linear-formatting.md`

**Status update:**
```bash
mcporter call linear.save_status_update \
  type:"project" \
  project:"ProjectName" \
  health:"onTrack" \
  body:"Progress update..."
```

### Organization

**My work:**
```bash
mcporter call linear.list_issues assignee:"me"
```

**Team work:**
```bash
mcporter call linear.list_issues team:"Engineering" state:"started"
```

## Core Concepts

### Hierarchy

```
Organization
├── Initiatives (strategic goals, quarters/years)
│   ├── Projects (tactical execution, weeks/months)
│   │   ├── Milestones (target dates)
│   │   └── Issues (tasks, days/weeks)
│   │       └── Sub-Issues
```

### Priority Levels

- **0** - None ← **DEFAULT. Always use this unless <USER_NAME>explicitly says otherwise.**
- **1** - Urgent (production issues, blockers)
- **2** - High (important features, bugs)
- **3** - Normal (standard work)
- **4** - Low (nice-to-haves)

### State Types

- `backlog` - Not started
- `unstarted` - Planned
- `started` - In progress
- `completed` - Done
- `canceled` - Won't do

### The "me" Keyword

Use `"me"` to reference the current user:
- `assignee:"me"` - My issues
- `lead:"me"` - Make me lead
- `owner:"me"` - My initiatives
- `member:"me"` - Projects I'm on

## Reference Documentation

Comprehensive guides organized by feature area. Load as needed.

### [issues.md](references/issues.md)
Issue management - creating, updating, listing, searching, statuses, labels, relations, priorities.

**Read when:**
- Creating or updating issues
- Need filtering/search patterns
- Working with labels or relations
- Setting priorities

### [projects.md](references/projects.md)
Project management - creating/updating projects, status updates, milestones, project labels.

**Read when:**
- Creating or managing projects
- Writing status updates
- Working with milestones
- Need project organization patterns

### [workflows.md](references/workflows.md)
Common Linear workflows - daily standups, sprint planning, code reviews, bug triage, release management, incident response.

**Read when:**
- Need specific workflow patterns
- Planning sprints or releases
- Running standups or retrospectives
- Managing incidents

### [initiatives.md](references/initiatives.md)
Initiative management - creating/updating initiatives, status updates, hierarchy, OKRs, roadmaps.

**Read when:**
- Working with quarterly goals
- Managing strategic initiatives
- Setting up OKRs or roadmaps
- Creating initiative hierarchies

### [organization.md](references/organization.md)
Teams, users, cycles, and organizational structure patterns.

**Read when:**
- Working across teams
- Understanding team structure
- Using cycles (sprints)
- Querying users or teams

### [content.md](references/content.md)
Documents, comments, attachments, and content management.

**Read when:**
- Creating Linear documents
- Adding comments to issues
- Uploading attachments
- Need content formatting patterns

## Common Patterns

### Create Issue → Get ID → Update

```bash
# Create issue
RESULT=$(mcporter call linear.create_issue \
  title:"..." \
  team:"Engineering")

# Extract ID from result
ISSUE_ID=$(echo "$RESULT" | jq -r '.id')

# Update issue
mcporter call linear.update_issue \
  id:"$ISSUE_ID" \
  state:"In Progress"
```

### List → Process → Update

```bash
# Get all my open issues
mcporter call linear.list_issues \
  assignee:"me" \
  state:"started" \
  | jq -r '.issues[] | "\(.identifier): \(.title)"'

# Process each...
# Update as needed
```

### Project → Milestones → Issues

```bash
# 1. Create project
PROJECT_ID=$(mcporter call linear.create_project \
  name:"Q1 Search" \
  team:"Engineering" \
  | jq -r '.id')

# 2. Add milestones
mcporter call linear.create_milestone \
  project:"$PROJECT_ID" \
  name:"Phase 1" \
  targetDate:"2026-02-15"

# 3. Create issues in project
mcporter call linear.create_issue \
  title:"Deploy ES" \
  team:"Engineering" \
  project:"$PROJECT_ID" \
  milestone:"Phase 1"
```

### Search → Filter → Act

```bash
# Find stale issues
mcporter call linear.list_issues \
  team:"Engineering" \
  state:"started" \
  updatedAt:"-P30D" \
  | jq -r '.issues[] | .identifier'

# Close or reassign...
```

## Tool Categories

### Issues (10 tools)
- create_issue, update_issue, list_issues, get_issue
- list_issue_statuses, get_issue_status
- list_issue_labels, create_issue_label

### Projects (7 tools)
- create_project, update_project, list_projects, get_project
- list_project_labels
- create_milestone, update_milestone, list_milestones, get_milestone

### Initiatives (5 tools)
- create_initiative, update_initiative, list_initiatives, get_initiative

### Status Updates (3 tools)
- get_status_updates, save_status_update, delete_status_update

### Documents (4 tools)
- create_document, update_document, list_documents, get_document

### Comments (2 tools)
- create_comment, list_comments

### Attachments (3 tools)
- create_attachment, get_attachment, delete_attachment

### Organization (6 tools)
- list_teams, get_team
- list_users, get_user
- list_cycles
- search_documentation

### Images (1 tool)
- extract_images

## Tips

### Always Include Team

Most operations require a team:
```bash
# ✅ Good
mcporter call linear.create_issue title:"..." team:"Engineering"

# ❌ Missing team will fail
mcporter call linear.create_issue title:"..."
```

### Use Identifiers Not UUIDs

Where possible, use identifiers (ENG-123) instead of UUIDs:
```bash
# ✅ Readable
mcporter call linear.update_issue id:"ENG-123" state:"Done"

# Also works but less readable
mcporter call linear.update_issue id:"uuid-here" state:"Done"
```

### Pagination for Large Lists

Default limit is 50, max is 250:
```bash
mcporter call linear.list_issues team:"Engineering" limit:250

# Use cursor for next page
mcporter call linear.list_issues cursor:"cursor-from-prev" limit:250
```

### Date Filters

Use ISO dates or durations:
```bash
# Last 7 days
updatedAt:"-P7D"

# Last 30 days
updatedAt:"-P30D"

# Specific date
createdAt:"2026-02-01T00:00:00Z"
```

### State vs Status

- **State** - Generic type (started, completed, etc.)
- **Status** - Team-specific name ("In Progress", "Done", etc.)

Both work in filters:
```bash
# By type
mcporter call linear.list_issues state:"started"

# By name
mcporter call linear.list_issues state:"In Progress"
```

## Error Handling

### Common Issues

**Team required:**
```
Error: team is required
```
→ Add `team:"Engineering"` parameter

**Invalid priority:**
```
Error: priority must be 0-4
```
→ Use 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low

**Invalid state:**
```
Error: state not found
```
→ Use list_issue_statuses to see valid states

**Not found:**
```
Error: issue not found
```
→ Check identifier spelling (ENG-123 not eng-123)

### Debugging

**Get full issue details:**
```bash
mcporter call linear.get_issue id:"ENG-123" includeRelations:true
```

**List valid states:**
```bash
mcporter call linear.list_issue_statuses team:"Engineering"
```

**Search docs:**
```bash
mcporter call linear.search_documentation query:"your question"
```

## Integration Patterns

### Git Branch Names

Linear auto-generates git branch names:
```bash
ISSUE=$(mcporter call linear.create_issue \
  title:"Add caching" \
  team:"Engineering")

# Extract branch name
BRANCH=$(echo "$ISSUE" | jq -r '.gitBranchName')
# → "username/eng-123-add-caching"

git checkout -b "$BRANCH"
```

### External Links

Link to GitHub PRs, Notion docs, etc:
```bash
mcporter call linear.create_issue \
  title:"..." \
  team:"Engineering" \
  links:'[{"url":"https://github.com/org/repo/pull/123","title":"PR"}]'
```

### Blocking Dependencies

```bash
# This issue blocks others
mcporter call linear.create_issue \
  title:"API endpoints" \
  team:"Engineering" \
  blocks:'["ENG-124","ENG-125"]'

# This issue is blocked
mcporter call linear.create_issue \
  title:"Frontend integration" \
  team:"Engineering" \
  blockedBy:'["ENG-123"]'
```

## Full Tool Reference

All 40 Linear MCP tools are available. See reference documentation for detailed guides on:

- **Issues:** Creating, updating, searching, labeling, relating
- **Projects:** Managing, milestones, status updates
- **Initiatives:** Strategic goals, OKRs, roadmaps
- **Documents:** Specs, RFCs, long-form content
- **Comments:** Discussion, progress updates
- **Attachments:** Files, images, screenshots
- **Organization:** Teams, users, cycles
- **Workflows:** Standups, sprints, reviews, releases

Load reference files as needed for specific functionality.
