# Linear Organization Reference

Guide for teams, users, cycles, and organizational structure.

## Table of Contents
- [Teams](#teams)
- [Users](#users)
- [Cycles](#cycles)
- [Organization Structure](#organization-structure)

## Teams

### Listing Teams

```bash
mcporter call linear.list_teams limit:50
```

**Filter Parameters:**
- `query` - Search query
- `includeArchived` - Include archived teams
- `createdAt` / `updatedAt` - Date filters
- `limit` / `cursor` / `orderBy` - Pagination

### Getting Team Details

```bash
mcporter call linear.get_team query:"Engineering"
```

Can query by:
- Team UUID
- Team key (e.g., "ENG")
- Team name (e.g., "Engineering")

**Returns:**
- Team metadata
- Settings
- Members (if available)

### Team Keys

Each team has a unique key used in issue identifiers:
- Engineering → ENG → ENG-123
- Design → DES → DES-45
- Product → PROD → PROD-67

## Users

### Listing Users

```bash
mcporter call linear.list_users team:"Engineering" limit:50
```

**Filter Parameters:**
- `query` - Filter by name or email
- `team` - Team name or ID
- `limit` / `cursor` / `orderBy` - Pagination

### Getting User Details

```bash
mcporter call linear.get_user query:"me"
```

Can query by:
- User ID (UUID)
- Name
- Email
- "me" (current user)

### Using "me" in Queries

The "me" keyword references the current authenticated user:

```bash
# My issues
mcporter call linear.list_issues assignee:"me"

# My projects
mcporter call linear.list_projects member:"me"

# Assign to me
mcporter call linear.update_issue id:"ENG-123" assignee:"me"

# Make me project lead
mcporter call linear.update_project id:"project-uuid" lead:"me"

# My profile
mcporter call linear.get_user query:"me"
```

### Assigning Work

**By name:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  assignee:"John Doe"
```

**By email:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  assignee:"john@company.com"
```

**By user ID:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  assignee:"user-uuid"
```

**Unassign:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  assignee:null
```

## Cycles

Cycles are time-boxed periods (usually 1-2 weeks) for sprint planning.

### Listing Cycles

```bash
mcporter call linear.list_cycles team:"Engineering" type:"current"
```

**Types:**
- `current` - Active cycle
- `previous` - Last completed cycle
- `next` - Upcoming cycle
- Omit type for all cycles

### Using Cycles in Issues

**List current cycle issues:**
```bash
mcporter call linear.list_issues \
  team:"Engineering" \
  cycle:"current"
```

**Add issue to current cycle:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  cycle:"current"
```

**Add to specific cycle:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  cycle:"Cycle 5"
```

**Remove from cycle:**
```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  cycle:null
```

### Cycle Queries

**By cycle number:**
```bash
mcporter call linear.list_issues cycle:"5" team:"Engineering"
```

**By cycle name:**
```bash
mcporter call linear.list_issues cycle:"Sprint 23" team:"Engineering"
```

**By cycle type:**
```bash
# Current sprint
mcporter call linear.list_issues cycle:"current" team:"Engineering"

# Previous sprint
mcporter call linear.list_issues cycle:"previous" team:"Engineering"

# Next sprint
mcporter call linear.list_issues cycle:"next" team:"Engineering"
```

## Organization Structure

### Typical Hierarchy

```
Organization
├── Team: Engineering
│   ├── Users
│   ├── Cycles (sprints)
│   ├── Projects
│   └── Issues (ENG-*)
├── Team: Design
│   ├── Users
│   ├── Projects
│   └── Issues (DES-*)
└── Team: Product
    ├── Users
    ├── Projects
    └── Issues (PROD-*)

Initiatives (org-wide or team-specific)
├── Initiative: Q1 2026 Goals
│   ├── Project: Feature X (Engineering)
│   └── Project: Feature Y (Product)
```

### Cross-Team Work

**Issues belong to one team:**
```bash
# Can't change team after creation
mcporter call linear.create_issue title:"..." team:"Engineering"
```

**Projects can span teams:**
```bash
# Project in Engineering team
mcporter call linear.create_project name:"..." team:"Engineering"

# But can have issues from any team
mcporter call linear.create_issue \
  title:"..." \
  team:"Design" \
  project:"Engineering-Project"
```

**Initiatives span teams:**
```bash
# Org-wide initiative
mcporter call linear.create_initiative name:"Q1 2026 Goals"

# Link projects from different teams
mcporter call linear.update_project \
  id:"eng-project" \
  initiatives:'["Q1 2026 Goals"]'

mcporter call linear.update_project \
  id:"design-project" \
  initiatives:'["Q1 2026 Goals"]'
```

### Team Workflows

**Engineering team patterns:**
- Issues use team key (ENG-123)
- Sprints via cycles
- Projects for features
- Initiatives for quarters

**Design team patterns:**
- Issues for design tasks (DES-45)
- Projects for design systems
- Cycles optional (Kanban more common)

**Product team patterns:**
- Issues for specs/requirements (PROD-67)
- Projects for features
- Link to engineering issues

### Access Patterns

**Team member:**
```bash
# See my team's work
mcporter call linear.list_issues team:"Engineering"

# See my work across teams
mcporter call linear.list_issues assignee:"me"
```

**Project member:**
```bash
# See project work across teams
mcporter call linear.list_issues project:"Feature X"
```

**Initiative owner:**
```bash
# See all projects in initiative
mcporter call linear.get_initiative \
  query:"Q1 2026 Goals" \
  includeProjects:true
```

## Common Queries

### My Work Across Organization

```bash
# All my assigned issues
mcporter call linear.list_issues assignee:"me"

# My active projects
mcporter call linear.list_projects member:"me" state:"started"

# My initiatives
mcporter call linear.list_initiatives owner:"me" status:"Active"
```

### Team Overview

```bash
# Team details
mcporter call linear.get_team query:"Engineering"

# Team members
mcporter call linear.list_users team:"Engineering"

# Team's active work
mcporter call linear.list_issues \
  team:"Engineering" \
  state:"started"

# Team's current sprint
mcporter call linear.list_issues \
  team:"Engineering" \
  cycle:"current"

# Team's active projects
mcporter call linear.list_projects \
  team:"Engineering" \
  state:"started"
```

### Organization-Wide Views

```bash
# All active projects
mcporter call linear.list_projects state:"started" limit:100

# All active initiatives
mcporter call linear.list_initiatives status:"Active" limit:50

# All teams
mcporter call linear.list_teams limit:50

# Recent activity
mcporter call linear.list_issues \
  updatedAt:"-P1D" \
  orderBy:"updatedAt" \
  limit:50
```
