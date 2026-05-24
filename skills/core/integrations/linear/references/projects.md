# Linear Projects Reference

Complete guide for projects, status updates, milestones, and project management.

## Table of Contents
- [Projects](#projects)
- [Status Updates](#status-updates)
- [Milestones](#milestones)
- [Project Labels](#project-labels)

## Projects

### Listing Projects

```bash
mcporter call linear.list_projects \
  team:"Engineering" \
  state:"started" \
  limit:20
```

**Filter Parameters:**
- `query` - Search project name
- `state` - State type, name, or ID
- `team` - Team name or ID
- `member` - User ID, name, email, or "me"
- `initiative` - Initiative name or ID
- `createdAt` / `updatedAt` - ISO date or duration
- `includeMilestones` - Include milestones
- `includeMembers` - Include project members
- `includeArchived` - Include archived

### Getting Project Details

```bash
mcporter call linear.get_project \
  query:"<PROJECT_NAME>" \
  includeMilestones:true \
  includeMembers:true \
  includeResources:true
```

Returns full project details including:
- Project metadata
- Optional: milestones, members, resources (documents/links/attachments)

### Creating Projects

```bash
mcporter call linear.create_project \
  name:"<PROJECT_NAME> Search Integration" \
  icon:":rocket:" \
  color:"#4CAF50" \
  summary:"Build search infrastructure" \
  team:"Engineering" \
  state:"started" \
  priority:2 \
  lead:"me"
```

**Required:**
- `name` - Project name
- `team` - Team name or ID

**Optional:**
- `icon` - Emoji (e.g., `:rocket:`)
- `color` - Hex color
- `summary` - Short summary (max 255 chars)
- `description` - Full Markdown description
- `state` - Project state
- `startDate` / `targetDate` - ISO format dates
- `priority` - 0=None, 1=Urgent, 2=High, 3=Medium, 4=Low
- `lead` - User ID, name, email, or "me"
- `labels` - Array of label names/IDs
- `initiative` - Initiative name or ID

### Updating Projects

```bash
mcporter call linear.update_project \
  id:"project-uuid" \
  state:"completed" \
  targetDate:"2026-03-01"
```

**All parameters same as create, except:**
- `id` - Required project ID
- `lead` - Set to `null` to remove
- `initiatives` - Array of initiative IDs/names

### Project States

Common states:
- `planned` - Not started
- `started` - Active
- `paused` - On hold
- `completed` - Done
- `canceled` - Won't do

### Project Icons

Use emoji format:
- `:rocket:` - 🚀
- `:chart_with_upwards_trend:` - 📈
- `:hammer:` - 🔨
- `:zap:` - ⚡
- `:star:` - ⭐

Or plain emoji: 🚀 📈 🔨 ⚡ ⭐

## Status Updates

Status updates are progress reports attached to projects or initiatives.

### Listing Status Updates

```bash
mcporter call linear.get_status_updates \
  type:"project" \
  project:"<PROJECT_NAME>" \
  limit:10
```

**Parameters:**
- `type` - Required: "project" or "initiative"
- `id` - Optional: specific update ID
- `project` - Project name or ID
- `initiative` - Initiative name or ID
- `user` - User ID, name, email, or "me"
- `createdAt` / `updatedAt` - Date filters
- `limit` / `cursor` / `orderBy` - Pagination

### Creating Status Updates

```bash
mcporter call linear.save_status_update \
  type:"project" \
  project:"<PROJECT_NAME>" \
  health:"onTrack" \
  body:"## Progress Update

**Completed:**
- Database migration 20% done
- Elasticsearch Phase 1 complete

**Next:**
- Search API endpoints
- Performance testing

**Blockers:** None"
```

**Parameters:**
- `type` - Required: "project" or "initiative"
- `project` - Project name or ID (for type=project)
- `initiative` - Initiative name or ID (for type=initiative)
- `body` - Markdown content
- `health` - "onTrack" | "atRisk" | "offTrack"
- `isDiffHidden` - Hide diff with previous update

**Omit `id` to create new, provide `id` to update existing.**

### Updating Status Updates

```bash
mcporter call linear.save_status_update \
  type:"project" \
  id:"status-update-uuid" \
  health:"atRisk" \
  body:"Updated status..."
```

### Deleting Status Updates

```bash
mcporter call linear.delete_status_update \
  type:"project" \
  id:"status-update-uuid"
```

### Health Status Meanings

| Health | Color | When to Use |
|--------|-------|-------------|
| onTrack | Green | On schedule, no issues |
| atRisk | Yellow | Behind or facing risks |
| offTrack | Red | Significantly delayed or blocked |

### Status Update Best Practices

**Structure:**
```markdown
## [Title - optional]

**Progress:**
- What got done
- Key achievements

**Next Steps:**
- What's coming
- Timeline

**Blockers/Risks:**
- Issues or concerns
- Mitigation plans

**Metrics:**
- Key numbers
- Performance indicators
```

**Frequency:**
- Weekly for active projects
- Bi-weekly for maintenance mode
- After major milestones

## Milestones

Milestones are target dates within projects.

### Listing Milestones

```bash
mcporter call linear.list_milestones project:"<PROJECT_NAME>"
```

### Getting Milestone Details

```bash
mcporter call linear.get_milestone \
  project:"<PROJECT_NAME>" \
  query:"Phase 1 Complete"
```

### Creating Milestones

```bash
mcporter call linear.create_milestone \
  project:"<PROJECT_NAME>" \
  name:"Elasticsearch Integration" \
  description:"Complete ES deployment and indexing" \
  targetDate:"2026-02-15"
```

**Parameters:**
- `project` - Required: project name or ID
- `name` - Required: milestone name
- `description` - Optional: Markdown description
- `targetDate` - Optional: ISO format date

### Updating Milestones

```bash
mcporter call linear.update_milestone \
  project:"<PROJECT_NAME>" \
  id:"milestone-name-or-id" \
  targetDate:"2026-02-20"
```

**Remove target date:**
```bash
mcporter call linear.update_milestone \
  project:"<PROJECT_NAME>" \
  id:"milestone-id" \
  targetDate:null
```

### Milestone vs Issue Due Dates

- **Milestones** - Project-level targets, group multiple issues
- **Issue due dates** - Individual task deadlines

Use milestones for phases/releases, issue due dates for specific tasks.

## Project Labels

Separate from issue labels. Used to categorize projects.

### Listing Project Labels

```bash
mcporter call linear.list_project_labels limit:50
```

**Parameters:**
- `name` - Filter by name
- `limit` / `cursor` / `orderBy` - Pagination

### Using Project Labels

**On project creation:**
```bash
mcporter call linear.create_project \
  name:"..." \
  team:"Engineering" \
  labels:'["infrastructure","migration"]'
```

**On project update:**
```bash
mcporter call linear.update_project \
  id:"project-uuid" \
  labels:'["infrastructure","search"]'
```

**Note:** Project labels are workspace-level, not team-specific.
