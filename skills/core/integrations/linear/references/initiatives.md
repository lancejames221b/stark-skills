# Linear Initiatives Reference

Complete guide for managing initiatives - high-level goals spanning multiple projects.

## Table of Contents
- [Understanding Initiatives](#understanding-initiatives)
- [Creating Initiatives](#creating-initiatives)
- [Managing Initiatives](#managing-initiatives)
- [Status Updates](#status-updates)
- [Initiative Hierarchy](#initiative-hierarchy)

## Understanding Initiatives

Initiatives are company-wide or team-wide goals that span multiple projects. Think of them as:
- **Initiatives** - Strategic goals (quarters/years)
- **Projects** - Tactical execution (weeks/months)
- **Issues** - Individual tasks (days/weeks)

**Example hierarchy:**
```
Initiative: "Improve Search Performance"
  ├── Project: "Elasticsearch Integration"
  │   ├── Issue: "Deploy ES cluster"
  │   └── Issue: "Index data"
  └── Project: "Query Optimization"
      ├── Issue: "Add caching"
      └── Issue: "Optimize SQL"
```

## Creating Initiatives

### Basic Initiative

```bash
mcporter call linear.create_initiative \
  name:"Q1 2026 Platform Improvements" \
  summary:"Improve performance, reliability, and scalability" \
  status:"Active"
```

### Full Initiative

```bash
mcporter call linear.create_initiative \
  name:"Search Infrastructure Overhaul" \
  summary:"Build modern search with ES and semantic capabilities" \
  description:"## Background
Current search is slow and basic. Need modern infrastructure.

## Goals
1. <100ms query latency
2. Support semantic search
3. Scale to 10M+ documents

## Success Metrics
- Query p95 latency: <100ms
- User satisfaction: >90%
- Search usage: +50%

## Timeline
Q1 2026 - Q2 2026" \
  icon:":rocket:" \
  color:"#4CAF50" \
  status:"Active" \
  targetDate:"2026-06-30" \
  owner:"me"
```

**Parameters:**
- `name` - Required: initiative name
- `summary` - Short summary (max 255 chars)
- `description` - Full Markdown description
- `icon` - Emoji (e.g., `:rocket:`)
- `color` - Hex color
- `status` - "Planned" | "Active" | "Completed"
- `targetDate` - ISO format date
- `owner` - User ID, name, email, or "me"

## Managing Initiatives

### Listing Initiatives

```bash
mcporter call linear.list_initiatives \
  status:"Active" \
  owner:"me" \
  limit:20
```

**Filter Parameters:**
- `query` - Search initiative name
- `status` - "Planned" | "Active" | "Completed"
- `owner` - User ID, name, email, or "me"
- `createdAt` / `updatedAt` - Date filters
- `includeProjects` - Include associated projects
- `includeSubInitiatives` - Include child initiatives
- `includeArchived` - Include archived

### Getting Initiative Details

```bash
mcporter call linear.get_initiative \
  query:"Q1 2026 Platform" \
  includeProjects:true \
  includeSubInitiatives:true
```

Returns:
- Full initiative details
- Optional: associated projects
- Optional: sub-initiatives

### Updating Initiatives

```bash
mcporter call linear.update_initiative \
  id:"initiative-uuid" \
  status:"Completed" \
  targetDate:"2026-06-30"
```

**All parameters same as create, except:**
- `id` - Required: initiative ID
- `owner` - Set to `null` to remove
- `parentInitiative` - Parent initiative name/ID, `null` to remove

### Initiative Status Lifecycle

```
Planned → Active → Completed
                 → Canceled (optional)
```

**When to update status:**
- **Planned** - Approved but not started
- **Active** - Work in progress
- **Completed** - All projects done, goals met
- **Canceled** - Deprioritized or no longer relevant

## Status Updates

Same as project status updates, but `type:"initiative"`.

### Create Initiative Status Update

```bash
mcporter call linear.save_status_update \
  type:"initiative" \
  initiative:"Q1 2026 Platform" \
  health:"onTrack" \
  body:"## Q1 Initiative Update

**Progress:**
- Elasticsearch project: 60% complete
- Query optimization: Starting next week

**Milestones:**
- ✅ ES cluster deployed
- ✅ Data indexed
- ⏳ Search API in progress
- ⏳ Semantic search planned

**Metrics:**
- Query latency: 150ms → 120ms (target: <100ms)
- Uptime: 99.95%

**Next Quarter:**
- Complete semantic search
- Performance tuning
- Scale testing

**Risks:**
- Resource constraints for scale testing
- Mitigation: Request additional GCP credits"
```

### List Initiative Updates

```bash
mcporter call linear.get_status_updates \
  type:"initiative" \
  initiative:"Q1 2026 Platform" \
  limit:10
```

## Initiative Hierarchy

### Creating Sub-Initiatives

```bash
mcporter call linear.create_initiative \
  name:"Elasticsearch Integration" \
  summary:"Deploy and integrate Elasticsearch" \
  parentInitiative:"Search Infrastructure" \
  status:"Active"
```

### Updating Hierarchy

```bash
# Add to parent
mcporter call linear.update_initiative \
  id:"child-initiative-uuid" \
  parentInitiative:"parent-initiative-name"

# Remove from parent
mcporter call linear.update_initiative \
  id:"child-initiative-uuid" \
  parentInitiative:null
```

### Viewing Hierarchy

```bash
# Get parent with children
mcporter call linear.get_initiative \
  query:"Search Infrastructure" \
  includeSubInitiatives:true

# Get child with parent context
mcporter call linear.get_initiative \
  query:"Elasticsearch Integration"
```

## Common Patterns

### Quarterly OKRs

```bash
# Create quarterly initiative
mcporter call linear.create_initiative \
  name:"Q1 2026 Engineering OKRs" \
  summary:"Quarterly objectives and key results" \
  description:"## Objectives

**1. Improve Platform Performance**
- KR1: Reduce p95 latency to <100ms
- KR2: Achieve 99.9% uptime
- KR3: Support 2x current load

**2. Enhance Search**
- KR1: Deploy Elasticsearch
- KR2: Add semantic search
- KR3: Improve relevance by 40%

**3. Strengthen Security**
- KR1: Complete SOC 2 audit
- KR2: Implement MFA
- KR3: Zero security incidents" \
  status:"Active" \
  targetDate:"2026-03-31" \
  icon:":dart:"
```

### Annual Roadmap

```bash
# Create annual initiative
mcporter call linear.create_initiative \
  name:"2026 Product Roadmap" \
  summary:"Full year product strategy" \
  status:"Active" \
  targetDate:"2026-12-31"

# Create quarterly sub-initiatives
for quarter in Q1 Q2 Q3 Q4; do
  mcporter call linear.create_initiative \
    name:"$quarter 2026 Roadmap" \
    parentInitiative:"2026 Product Roadmap" \
    status:"Planned"
done
```

### Linking Projects to Initiatives

**On project creation:**
```bash
mcporter call linear.create_project \
  name:"Elasticsearch Deployment" \
  team:"Engineering" \
  initiative:"Search Infrastructure"
```

**On project update:**
```bash
mcporter call linear.update_project \
  id:"project-uuid" \
  initiatives:'["Search Infrastructure","Q1 2026 OKRs"]'
```

**Note:** Projects can belong to multiple initiatives.

## Best Practices

### Initiative Naming

- Be specific: ❌ "Improve things" ✅ "Reduce API latency by 50%"
- Include timeframe: "Q1 2026 Search Improvements"
- Action-oriented: "Migrate to Kubernetes" not "Kubernetes"

### Initiative Scope

**Good initiative:**
- Clear goal
- Measurable outcomes
- 3-12 month duration
- 2-5 projects

**Too small:** Should be a project instead
**Too large:** Break into sub-initiatives

### Status Update Frequency

- **Active initiatives:** Weekly or bi-weekly
- **Planned initiatives:** Monthly or when status changes
- **Completed initiatives:** Final summary only

### Ownership

- Every initiative should have an owner
- Owner responsible for status updates
- Owner coordinates across projects
- Owner reports to stakeholders
