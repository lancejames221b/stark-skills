---
name: survey
description: Passive read-only investigation and analysis. Use when <USER_NAME>says "survey", "look into", "what's going on with", "investigate", or any phrasing that implies gathering information WITHOUT taking action. This is explicitly non-interventional - gather data, analyze, and report only. NO changes, fixes, restarts, or modifications.
category: verification
runtimes: [claude]
pii_safe: true
---

# Survey - Passive Investigation Mode

**Core principle: LOOK, DON'T TOUCH**

This skill is for passive investigation when <USER_NAME>wants information about a situation WITHOUT you jumping ahead to fix it. Use when he says things like:

- "Survey this"
- "Look into this"
- "What's going on with X?"
- "Investigate this"
- "Check on X" (without "fix" or "restart")
- Any phrasing that implies investigation without action

## What Survey Does

**READ-ONLY operations:**
- Check service status (`systemctl status`, `docker ps`, `kubectl get`)
- Read logs (`journalctl`, container logs, application logs)
- Check configurations (read config files, don't modify)
- Inspect network state (`netstat`, `ss`, firewall rules)
- Check resource usage (`df`, `free`, `top`, process lists)
- Query APIs for status information
- Review recent changes (`git log`, file timestamps)

**ANALYZE and REPORT:**
- Identify patterns in logs
- Compare current state to expected state
- Highlight anomalies or concerning metrics
- Provide evidence-based findings
- Suggest possible causes (but don't fix them)

## What Survey NEVER Does

**FORBIDDEN actions:**
- ❌ Restart services
- ❌ Modify configurations
- ❌ Apply patches or updates
- ❌ Change firewall rules
- ❌ Kill processes
- ❌ Delete or move files
- ❌ Run database migrations
- ❌ Deploy changes
- ❌ Modify DNS/networking
- ❌ ANY write operations outside of reporting

**If you need to act:** Ask explicitly. "Would you like me to restart the service?" or "Should I apply this fix?"

## Investigation Workflow

### 1. Understand the Scope
First, clarify what you're surveying:
- A specific service or application?
- A whole system or server?
- A deployment or infrastructure component?
- Network connectivity or performance?

### 2. Gather Evidence (Read-Only)
Run appropriate diagnostic commands:

```bash
# Service health
systemctl status <service>
docker ps -a | grep <name>
kubectl get pods -n <namespace>

# Logs (recent, limited)
journalctl -u <service> --since "10 minutes ago" -n 100
docker logs --tail 100 <container>
kubectl logs -n <namespace> <pod> --tail=100

# Configuration review
cat /etc/<service>/config.conf
docker inspect <container>
kubectl describe pod <pod>

# Resource state
df -h
free -h
netstat -tulpn | grep <port>
ss -tulpn | grep <port>

# Recent activity
git log --oneline -10
ls -ltr /path/to/directory | tail -20
```

### 3. Analyze Findings
Look for:
- Error messages or warnings in logs
- Services in failed/restarting state
- Resource exhaustion (disk, memory, CPU)
- Configuration mismatches
- Recent changes that correlate with issues
- Network connectivity problems

### 4. Report Structure
Present findings in a clear, actionable format:

```markdown
## Survey Results: <Component Name>

**Status:** [Healthy/Degraded/Down/Unknown]

**Key Findings:**
- Finding 1 with evidence
- Finding 2 with evidence

**Logs:** (relevant excerpts only, not full dumps)
[brief log snippets showing the issue]

**Observations:**
- What's working
- What's not working
- What's unusual

**Possible Causes:**
- Hypothesis 1 based on evidence
- Hypothesis 2 based on evidence

**Next Steps (if <USER_NAME>wants to act):**
- Suggested action 1
- Suggested action 2
```

### 5. Stay Passive
End with: "This is a passive survey. Let me know if you'd like me to take action on any of these findings."

## Context Integration

### When to Auto-Load Project Context
If the survey target matches a known project:
1. Check `contexts/channel-registry.json` for project context
2. Load relevant `contexts/[project].md` for system details
3. Search haivemind: `mcporter call haivemind.search_memories query="[project] infrastructure"`

This gives you baseline knowledge (where logs are, what services exist, normal behavior).

### Integration with Other Skills
- **diagnose** - May escalate to diagnose after survey if deep analysis needed
- **plan** - Survey findings feed into planning fixes
- **healthcheck** - Survey can use healthcheck patterns for system audits

## Examples

### Example 1: Service Investigation
**<USER_NAME>Survey the self-service-alerting backend"

**Response:**
1. Check backend service status (systemd/docker)
2. Review last 100 lines of logs
3. Check API health endpoint
4. Review database connectivity
5. Check recent deploys (git log)
6. Report findings without restarting anything

### Example 2: Infrastructure Check
**<USER_NAME>What's going on with the GKE cluster?"

**Response:**
1. Check node health (`kubectl get nodes`)
2. Check pod status across namespaces
3. Review recent events (`kubectl get events`)
4. Check resource usage (node CPU/memory)
5. Review ingress/service status
6. Report without making changes

### Example 3: Performance Investigation
**<USER_NAME>Look into why the API is slow"

**Response:**
1. Check API response times (logs/metrics)
2. Check database query performance (slow query logs)
3. Check resource usage (CPU/memory/disk)
4. Check network latency (if external dependencies)
5. Review recent code changes
6. Report findings with evidence

## Voice Mode Adaptation

**In voice mode (when <USER_NAME>says "survey" while mobile/AirPods):**
- Deliver TL;DR summary in voice (2-3 sentences: status + key finding + suggested action)
- Post full survey report to relevant Discord channel
- Confirm: "Full survey report posted to #[channel]"

**Never read detailed logs or multi-point findings over voice.**

## Differentiation from Diagnose

| Survey | Diagnose |
|--------|----------|
| Passive observation | Active investigation |
| Quick status check | Deep root cause analysis |
| Read-only commands | May run test cases |
| Surface-level analysis | Detailed debugging |
| "What's happening?" | "Why is this happening?" |
| Minutes to complete | May take longer |

**When to escalate:** If survey reveals complex issues requiring deep analysis, suggest: "This looks complex. Would you like me to run a full diagnose?"

## Remember

Survey is about gathering intelligence, not taking action. You're a reconnaissance mission, not a strike team. Report what you find, suggest what could be done, but **wait for explicit permission before changing anything**.
