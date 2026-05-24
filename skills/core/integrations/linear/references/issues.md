# Linear Issues Reference

Complete guide for creating, updating, and managing Linear issues.

## Table of Contents
- [Creating Issues](#creating-issues)
- [Updating Issues](#updating-issues)
- [Listing and Searching](#listing-and-searching)
- [Issue Details](#issue-details)
- [Issue Statuses](#issue-statuses)
- [Issue Labels](#issue-labels)
- [Issue Relations](#issue-relations)
- [Priority Levels](#priority-levels)

## Creating Issues

```bash
mcporter call linear.create_issue \
  title:"Issue title" \
  description:"Markdown content" \
  team:"Engineering" \
  priority:2 \
  project:"ProjectName"
```

### Required Parameters
- `title` - Issue title
- `team` - Team name or ID

### Optional Parameters
- `description` - Markdown content
- `priority` - 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low
- `project` - Project name or ID
- `state` - State type, name, or ID
- `assignee` - User ID, name, email, or "me"
- `labels` - Array of label names or IDs
- `dueDate` - ISO format date
- `parentId` - Parent issue ID (for sub-tasks)
- `estimate` - Issue estimate value
- `cycle` - Cycle name, number, or ID
- `milestone` - Milestone name or ID

### Relations
- `blocks` - Array of issue IDs/identifiers this blocks
- `blockedBy` - Array of issue IDs/identifiers blocking this
- `relatedTo` - Array of related issue IDs/identifiers
- `duplicateOf` - Duplicate of issue ID/identifier

### Example: Full Issue Creation
```bash
mcporter call linear.create_issue \
  title:"Implement search API" \
  description:"Build REST endpoints for search functionality" \
  team:"Engineering" \
  priority:2 \
  project:"<PROJECT_NAME>" \
  state:"In Progress" \
  assignee:"me" \
  labels:'["backend","api"]' \
  dueDate:"2026-02-20" \
  estimate:5
```

## Updating Issues

```bash
mcporter call linear.update_issue \
  id:"issue-uuid-or-identifier" \
  state:"Completed"
```

### All Update Parameters
Same as create, plus:
- `id` - Required issue ID or identifier (e.g., ENG-123)
- Set to `null` to remove: assignee, parentId, duplicateOf

### Common Update Patterns

**Change state:**
```bash
mcporter call linear.update_issue id:"ENG-123" state:"In Progress"
```

**Assign:**
```bash
mcporter call linear.update_issue id:"ENG-123" assignee:"me"
```

**Update description:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  description:"Updated content with more details"
```

**Add to project:**
```bash
mcporter call linear.update_issue id:"ENG-123" project:"<PROJECT_NAME>"
```

**Change priority:**
```bash
mcporter call linear.update_issue id:"ENG-123" priority:1
```

## Listing and Searching

```bash
mcporter call linear.list_issues \
  team:"Engineering" \
  state:"In Progress" \
  assignee:"me" \
  limit:20
```

### Filter Parameters
- `team` - Team name or ID
- `state` - State type, name, or ID
- `assignee` - User ID, name, email, or "me"
- `project` - Project name or ID
- `priority` - 0-4
- `cycle` - Cycle name, number, or ID
- `label` - Label name or ID
- `query` - Search title/description
- `parentId` - Parent issue ID

### Date Filters
- `createdAt` - Created after (ISO date or duration like `-P7D`)
- `updatedAt` - Updated after (ISO date or duration)

### Pagination
- `limit` - Max results (default 50, max 250)
- `cursor` - Next page cursor from previous response
- `orderBy` - "createdAt" or "updatedAt"
- `includeArchived` - Include archived items

### Common Queries

**My open issues:**
```bash
mcporter call linear.list_issues assignee:"me" state:"started"
```

**Team backlog:**
```bash
mcporter call linear.list_issues team:"Engineering" state:"Backlog" limit:50
```

**Recent updates:**
```bash
mcporter call linear.list_issues updatedAt:"-P1D" orderBy:"updatedAt" limit:20
```

**Project issues:**
```bash
mcporter call linear.list_issues project:"<PROJECT_NAME>" state:"In Progress"
```

**Search by text:**
```bash
mcporter call linear.list_issues query:"elasticsearch" team:"Engineering"
```

## Issue Details

```bash
mcporter call linear.get_issue id:"issue-uuid" includeRelations:true
```

Returns:
- Full issue details
- Attachments
- Git branch name
- Optional: blocking/related/duplicate relations

## Issue Statuses

### List Statuses
```bash
mcporter call linear.list_issue_statuses team:"Engineering"
```

### Get Specific Status
```bash
mcporter call linear.get_issue_status \
  name:"In Progress" \
  team:"Engineering"
```

### State Types
Linear organizes statuses into types:
- `backlog` - Not started
- `unstarted` - Planned but not active
- `started` - In progress
- `completed` - Done
- `canceled` - Won't do

Use type names when filtering:
```bash
mcporter call linear.list_issues state:"started" team:"Engineering"
```

## Issue Labels

### List Labels
```bash
mcporter call linear.list_issue_labels team:"Engineering" limit:50
```

### Create Label
```bash
mcporter call linear.create_issue_label \
  name:"security" \
  description:"Security-related issues" \
  color:"#FF0000" \
  teamId:"team-uuid"
```

Omit `teamId` for workspace-level label.

### Label Colors
Use hex colors: `#FF0000`, `#00FF00`, etc.

### Label Groups
Create hierarchical labels:
```bash
mcporter call linear.create_issue_label \
  name:"backend" \
  isGroup:true \
  teamId:"team-uuid"

mcporter call linear.create_issue_label \
  name:"api" \
  parentId:"backend-label-uuid" \
  teamId:"team-uuid"
```

## Issue Relations

### Types of Relations
- **Blocks** - This issue blocks other issues
- **Blocked By** - This issue is blocked by other issues
- **Related To** - Related but no blocking relationship
- **Duplicate Of** - Duplicate of another issue

### Setting Relations on Create
```bash
mcporter call linear.create_issue \
  title:"..." \
  team:"Engineering" \
  blocks:'["ENG-123","ENG-124"]' \
  relatedTo:'["ENG-125"]'
```

### Setting Relations on Update
```bash
mcporter call linear.update_issue \
  id:"ENG-126" \
  blocks:'["ENG-123"]' \
  blockedBy:'["ENG-127"]'
```

**Note:** Relations replace existing, they don't append. Omit to keep unchanged.

### Removing Relations
```bash
mcporter call linear.update_issue \
  id:"ENG-126" \
  duplicateOf:null
```

## Priority Levels

| Value | Name | When to Use |
|-------|------|-------------|
| 0 | None | Default, no priority set |
| 1 | Urgent | Production issues, blockers |
| 2 | High | Important features, significant bugs |
| 3 | Normal | Standard work |
| 4 | Low | Nice-to-haves, minor improvements |

**Setting priority:**
```bash
mcporter call linear.create_issue \
  title:"..." \
  team:"Engineering" \
  priority:1
```

**Updating priority:**
```bash
mcporter call linear.update_issue id:"ENG-123" priority:2
```
