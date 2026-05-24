# Linear Workflows Reference

Common workflow patterns for Linear issue and project management.

## Table of Contents
- [Daily Standup](#daily-standup)
- [Sprint Planning](#sprint-planning)
- [Code Review Workflow](#code-review-workflow)
- [Bug Triage](#bug-triage)
- [Project Kickoff](#project-kickoff)
- [Release Management](#release-management)
- [Issue Escalation](#issue-escalation)

## Daily Standup

Get team's active work for standup meetings.

```bash
# My current work
mcporter call linear.list_issues \
  assignee:"me" \
  state:"started" \
  orderBy:"updatedAt" \
  limit:10

# Team's in-progress work
mcporter call linear.list_issues \
  team:"Engineering" \
  state:"started" \
  orderBy:"updatedAt" \
  limit:50

# Recent completions (yesterday)
mcporter call linear.list_issues \
  team:"Engineering" \
  state:"completed" \
  updatedAt:"-P1D" \
  limit:20
```

**Format output:**
For each person:
- What they completed (yesterday)
- What they're working on (today)
- Blockers

## Sprint Planning

### View Current Sprint

```bash
# List current cycle issues
mcporter call linear.list_issues \
  team:"Engineering" \
  cycle:"current" \
  orderBy:"priority"
```

### Add Issues to Sprint

```bash
# Move issue to current cycle
mcporter call linear.update_issue \
  id:"ENG-123" \
  cycle:"current"
```

### Sprint Capacity Check

```bash
# Get all sprint issues with estimates
mcporter call linear.list_issues \
  team:"Engineering" \
  cycle:"current"

# Sum estimates to check capacity
```

### Create Sprint Issues

```bash
# Create issue directly in sprint
mcporter call linear.create_issue \
  title:"Implement feature X" \
  team:"Engineering" \
  cycle:"current" \
  assignee:"me" \
  priority:2 \
  estimate:5
```

## Code Review Workflow

> Every PR should be linked to its Linear issue via `update_issue links=[{url, title}]` after the PR is created. This triggers Linear automation (PR status on ticket, auto-transitions on merge).

### Step 1: Create/Identify the Linear Issue

```bash
# If issue already exists, get its ID
mcporter call linear.list_issues \
  assignee:"me" \
  state:"started" \
  limit:10
```

### Step 2: Open the PR on GitHub

Create your PR normally via `gh pr create` or GitHub UI.

### Step 3: Link PR to Linear Issue

```bash
# Immediately after PR is created — add the GitHub PR URL as a link
mcporter call linear.update_issue \
  id:"ENG-123" \
  links:'[{"url":"https://github.com/<ORG_NAME>/REPO/pull/456","title":"PR #456: brief description"}]'
```

This is the equivalent of clicking "Add link" on the Linear issue UI. Without this, Linear automation does not fire.

### Step 4: Move Issue to In Review

```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  state:"In Review"
```

### Step 5: Update After Review

```bash
# Changes requested
mcporter call linear.update_issue \
  id:"ENG-123" \
  state:"In Progress"

# Approved, merged
mcporter call linear.update_issue \
  id:"ENG-123" \
  state:"Completed"
```

### Legacy: Create PR Tracking Issue (if no issue exists yet)

```bash
mcporter call linear.create_issue \
  title:"[PR] Feature implementation" \
  description:"PR: https://github.com/org/repo/pull/123

**Changes:**
- Feature X implementation
- Tests added

**Reviewers:** @reviewer1 @reviewer2" \
  team:"Engineering" \
  state:"In Review" \
  assignee:"me" \
  links:'[{"url":"https://github.com/org/repo/pull/123","title":"PR #123: feature implementation"}]'
```

### Git Branch Name (auto-generated)

When creating issue, Linear auto-generates git branch name:
```json
{
  "gitBranchName": "username/eng-123-feature-implementation"
}
```

### Add Review Comments

```bash
mcporter call linear.create_comment \
  issueId:"issue-uuid" \
  body:"Addressed review feedback:
- Fixed naming
- Added tests
- Updated docs"
```

## Bug Triage

### Create Bug Report

```bash
mcporter call linear.create_issue \
  title:"[BUG] Search returns duplicate results" \
  description:"## Steps to Reproduce
1. Navigate to search page
2. Enter query: 'test'
3. Observe duplicate results

## Expected Behavior
Unique results only

## Actual Behavior
Multiple duplicate entries

## Environment
- Browser: Chrome 120
- OS: macOS
- Version: v2.3.1" \
  team:"Engineering" \
  priority:2 \
  labels:'["bug","search"]' \
  state:"Triage"
```

### Triage Process

```bash
# 1. Review new bugs
mcporter call linear.list_issues \
  team:"Engineering" \
  state:"Triage" \
  labels:"bug" \
  orderBy:"createdAt"

# 2. Assess and prioritize
mcporter call linear.update_issue \
  id:"ENG-123" \
  priority:1 \
  state:"Backlog"

# 3. Assign if urgent
mcporter call linear.update_issue \
  id:"ENG-123" \
  assignee:"me" \
  state:"To Do"
```

### Bug Priority Guidelines

| Priority | Criteria |
|----------|----------|
| Urgent (1) | Production down, data loss, security |
| High (2) | Major feature broken, affects many users |
| Normal (3) | Minor bugs, edge cases |
| Low (4) | Cosmetic issues, non-critical |

## Project Kickoff

### Create Project

```bash
mcporter call linear.create_project \
  name:"Q1 Search Infrastructure" \
  team:"Engineering" \
  summary:"Build scalable search with ES and pgvector" \
  description:"## Goals
- Deploy Elasticsearch cluster
- Implement keyword search
- Add semantic search with pgvector

## Success Metrics
- Query latency <100ms
- 99.9% uptime
- Support 1M+ documents

## Timeline
Q1 2026 (Jan-Mar)" \
  icon:":mag:" \
  state:"planned" \
  startDate:"2026-01-15" \
  targetDate:"2026-03-31" \
  priority:2 \
  lead:"me"
```

### Add Milestones

```bash
mcporter call linear.create_milestone \
  project:"Q1 Search Infrastructure" \
  name:"Phase 1: Elasticsearch" \
  targetDate:"2026-02-15"

mcporter call linear.create_milestone \
  project:"Q1 Search Infrastructure" \
  name:"Phase 2: Semantic Search" \
  targetDate:"2026-03-15"
```

### Create Initial Issues

```bash
# Create epic/parent issue
mcporter call linear.create_issue \
  title:"[EPIC] Search Infrastructure" \
  team:"Engineering" \
  project:"Q1 Search Infrastructure" \
  priority:2

# Create sub-tasks
mcporter call linear.create_issue \
  title:"Deploy Elasticsearch cluster" \
  team:"Engineering" \
  project:"Q1 Search Infrastructure" \
  parentId:"epic-issue-id" \
  priority:2 \
  milestone:"Phase 1: Elasticsearch"
```

### First Status Update

```bash
mcporter call linear.save_status_update \
  type:"project" \
  project:"Q1 Search Infrastructure" \
  health:"onTrack" \
  body:"## Project Kickoff

**Scope Confirmed:**
- Elasticsearch deployment
- Keyword + semantic search
- <100ms query latency target

**Team:**
- Lead: [Name]
- Engineers: [Names]

**Next:**
- Finalize architecture
- Provision GCP resources
- Create detailed tickets

**Risks:** None at this stage"
```

## Release Management

### Create Release Issue

```bash
mcporter call linear.create_issue \
  title:"v2.4.0 Release" \
  description:"## Included
- Feature X
- Bug fixes (ENG-101, ENG-102)
- Performance improvements

## Checklist
- [ ] All tickets resolved
- [ ] Tests passing
- [ ] Docs updated
- [ ] Changelog written
- [ ] Deployed to staging
- [ ] QA sign-off
- [ ] Deployed to production" \
  team:"Engineering" \
  priority:1 \
  labels:'["release"]' \
  dueDate:"2026-02-20"
```

### Track Release Progress

```bash
# Get all issues for release
mcporter call linear.list_issues \
  team:"Engineering" \
  milestone:"v2.4.0" \
  state:"started"

# Check blockers
mcporter call linear.list_issues \
  team:"Engineering" \
  milestone:"v2.4.0" \
  state:"blocked"
```

### Post-Release Update

```bash
mcporter call linear.update_issue \
  id:"release-issue-id" \
  state:"Completed"

mcporter call linear.create_comment \
  issueId:"release-issue-id" \
  body:"✅ Released to production at 2026-02-20 14:30 UTC

**Metrics:**
- Deployment time: 15 minutes
- Zero downtime
- All tests passing

**Monitoring:** No errors detected in first hour"
```

## Issue Escalation

### Mark as Blocked

```bash
mcporter call linear.update_issue \
  id:"ENG-123" \
  state:"Blocked" \
  blockedBy:'["ENG-124"]'

mcporter call linear.create_comment \
  issueId:"ENG-123-uuid" \
  body:"Blocked by ENG-124 - need API endpoints before proceeding"
```

### Escalate Priority

```bash
# Bump to urgent
mcporter call linear.update_issue \
  id:"ENG-123" \
  priority:1

# Add urgent label
mcporter call linear.update_issue \
  id:"ENG-123" \
  labels:'["urgent","blocker"]'

# Notify via comment
mcporter call linear.create_comment \
  issueId:"ENG-123-uuid" \
  body:"⚠️ Escalated to urgent - production impact"
```

### Create Incident Issue

```bash
mcporter call linear.create_issue \
  title:"[INCIDENT] Production API errors" \
  description:"## Impact
- 50% of API requests failing
- Started: 2026-02-20 10:15 UTC
- Affected: All users

## Status
Investigating

## Timeline
10:15 - Issue detected
10:20 - Team notified
10:25 - Root cause investigation started" \
  team:"Engineering" \
  priority:1 \
  labels:'["incident","production"]' \
  state:"In Progress" \
  assignee:"me"
```
