---
name: cron-reminders
description: **Create reliable, verified reminders using the cron tool.**
category: workflows
runtimes: [claude]
pii_safe: true
---
# Cron Reminders Skill

**Create reliable, verified reminders using the cron tool.**

## The Problem

Saying "I'll remind you in X minutes" without verification = broken promises.

## The Solution

**Pattern: CREATE → VERIFY → CONFIRM**

## Delivery Target (CRITICAL — Feb 16, 2026 Fix)

**NEVER use `sessionTarget: "main"` + `systemEvent` for channel-targeted delivery.**
Main session is bound to whichever channel was last active. If that channel's plugin is down (WhatsApp DNS failure, etc.), the cron job fails with "whatsapp-not-running" or similar.

### Reliable Pattern: isolated + agentTurn + explicit delivery

```javascript
{
  action: "add",
  job: {
    name: "reminder-name",
    sessionTarget: "isolated",  // Runs in its own session
    schedule: { at: "2026-02-08T16:30:00Z" },
    payload: {
      kind: "agentTurn",
      message: "Deliver this reminder: [text]. If targeting WhatsApp, use sessions_send to the WhatsApp session key.",
      model: "haiku",
      timeoutSeconds: 60
    },
    delivery: {
      mode: "announce",
      channel: "discord",          // Primary delivery: Discord (most reliable)
      to: "channel:CHANNEL_ID"     // Specific Discord channel
    }
  }
}
```

### For WhatsApp-targeted reminders
Use isolated + agentTurn with instructions to deliver via sessions_send:
```javascript
payload: {
  kind: "agentTurn",
  message: "Send this reminder to WhatsApp group <WHATSAPP_GROUP_ID> via sessions_send: [reminder text]. If WhatsApp delivery fails, post to Discord #petex (<DISCORD_CHANNEL_ID>) as fallback.",
  model: "haiku"
}
```

### Legacy Pattern (DEPRECATED — causes failures when WhatsApp is down)

```javascript
// DON'T USE THIS for channel-targeted delivery
{
  action: "add",
  job: {
    name: "reminder-name",
    sessionTarget: "main",  // FRAGILE: bound to last-active channel
    schedule: { at: "2026-02-08T16:30:00Z" },
    payload: {
      kind: "systemEvent",
      text: "Reminder text here"
    }
  }
}
```

**Override only for channel-specific notifications:**
- Monitoring alerts → specify Discord channel in `payload.text`
- Team notifications → use `message` tool in payload
- But personal reminders → ALWAYS `sessionTarget: "main"` (Signal)

## Cron Tool Parameters

The cron tool uses these parameters:

```javascript
{
  action: "add",
  job: {
    name: "reminder-name",  // required: unique identifier
    sessionTarget: "main",  // ALWAYS for reminders - routes to Signal
    schedule: {
      at: "2026-02-08T16:30:00Z"  // ISO timestamp for one-time
      // OR for recurring:
      // kind: "cron",
      // expr: "*/5 * * * *"
    },
    payload: {
      kind: "systemEvent",
      text: "What the cron should do (instruction to the agent)"
    }
  }
}
```

The `payload.text` field is what gets sent to the agent when the cron fires. Write it as a complete instruction.

## Step-by-Step Implementation

### 1. Calculate when reminder should fire

```javascript
// For relative time (e.g., "in 5 minutes")
const now = new Date();
const fireTime = new Date(now.getTime() + (5 * 60 * 1000));
const isoTime = fireTime.toISOString();

// For absolute time (e.g., "at 3pm")
const fireTime = new Date("2026-02-08T15:00:00-05:00"); // EST
const isoTime = fireTime.toISOString();
```

### 2. Create the cron job

```javascript
cron({
  action: "add",
  job: {
    name: "download-check-jurassic",
    sessionTarget: "main",  // Routes to Signal note-to-self
    schedule: {
      at: isoTime  // ISO timestamp
    },
    payload: {
      kind: "systemEvent",
      text: "Check download status for Jurassic Park RiffTrax. Run: qbt-cli list | grep -i jurassic and report progress/speed."
    }
  }
})
```

**Critical:** The `payload.text` field must:
- Be a complete instruction (what to check, how to check it, where to report)
- Include channel context (which channel to respond in)
- Specify what success looks like

### 3. Verify the cron was created

```javascript
// IMMEDIATELY after creation, verify:
cron({
  action: "list",
  includeDisabled: false
})
```

Look for your job in the list. Get the jobId.

### 4. Confirm to user with evidence

```
✅ Reminder created:
- Job ID: abc123
- Fires at: 2026-02-08 16:30:00 UTC (11:30 AM EST)
- Will check: [what you're monitoring]
```

## Complete Example

**User:** "Remind me in 5 minutes to check the downloads"

**Implementation:**
```javascript
// Step 1: Calculate fire time
const fireTime = new Date(Date.now() + 5 * 60 * 1000);
const isoTime = fireTime.toISOString(); // "2026-02-08T16:35:00.000Z"

// Step 2: Create cron
const result = await cron({
  action: "add",
  job: {
    name: "download-check-reminder",
    sessionTarget: "main",  // Routes to Signal note-to-self
    schedule: {
      at: isoTime
    },
    payload: {
      kind: "systemEvent",
      text: "Reminder: Check download status. Run qbt-cli list and report progress."
    }
  }
});

// Step 3: Verify
const jobs = await cron({
  action: "list",
  includeDisabled: false
});

// Step 4: Confirm
const job = jobs.jobs.find(j => j.id === result.id);
if (job) {
  reply(`✅ Reminder set for ${fireTime.toLocaleTimeString()} (${fireTime.toISOString()})
Job ID: ${job.id}
Will check downloads and report back here.`);
} else {
  reply("❌ Failed to create reminder - cron job not found in list. Let me check manually instead.");
}
```

## Recurring vs One-Time

**One-time (most reminders):**
```javascript
{
  name: "reminder-name",
  sessionTarget: "main",  // Signal note-to-self
  schedule: {
    at: "2026-02-08T16:30:00Z"  // ISO timestamp
  }
}
```

**Recurring (periodic checks):**
```javascript
{
  name: "periodic-check",
  sessionTarget: "main",  // Signal note-to-self
  schedule: {
    kind: "cron",
    expr: "*/5 * * * *"  // Every 5 minutes (cron syntax)
  }
}
```

## Delivery Routing

**Personal reminders → Signal note-to-self (default):**
```javascript
sessionTarget: "main"  // ALWAYS for reminders
payload: {
  kind: "systemEvent",
  text: "Reminder text"
}
```

**Monitoring/alerts → Can specify channel in payload text:**
```javascript
sessionTarget: "main"  // Still routes to Signal, but can mention context
payload: {
  kind: "systemEvent",
  text: "Check server health. If issues found, also post to Discord #infrastructure (123456)."
}
```

The `sessionTarget: "main"` pattern is deterministic - always routes to Signal note-to-self.

## Anti-Patterns

❌ **No verification:**
```javascript
cron({ action: "add", job: {...} });
reply("Reminder set!"); // Did it actually work?
```

❌ **Vague instructions:**
```javascript
payload: {
  kind: "systemEvent",
  text: "Check the thing"  // What thing? How? Where to report?
}
```

❌ **Wrong tool:**
```javascript
// DON'T use shell scripts or sleep commands
exec("sleep 300 && echo 'reminder'"); // This can't send Discord messages!
```

## Success Criteria

Before confirming to user, you must have:
1. ✅ Created the cron job
2. ✅ Verified it appears in cron list
3. ✅ Extracted the job ID
4. ✅ Calculated and displayed the fire time

If any step fails, admit it and offer an alternative (manual check now, or try again).

## Testing Your Reminder

After confirming to user, you can test by setting a very short reminder (30 seconds) and verifying it fires:

```javascript
cron({
  action: "add",
  job: {
    name: "test-reminder-30s",
    sessionTarget: "main",  // Routes to Signal note-to-self
    schedule: {
      at: new Date(Date.now() + 30000).toISOString()
    },
    payload: {
      kind: "systemEvent",
      text: "Test reminder: Reply 'Test successful'"
    }
  }
});
```

Wait 30 seconds. Did the message appear? If not, debug why.

## Remember

**A reminder promised is a reminder delivered.**

If you say "I'll remind you", make sure it actually happens.
