---
name: thread-task
description: Spawn a focused sub-agent task in a Discord thread with full channel context. Use when <USER_NAME>says "/thread NAME" optionally followed by args like model, ticket (ENG-xxx), prompt/task description. Creates a Discord thread in the current channel (or a target channel with /thread channel <#id>), loads current channel context (haivemind + context file), spawns a sub-agent in that thread with the task, memory, and relevant project state. Supports model override (e.g. opus, cursor-sonnet), Linear ticket reference, and free-form task prompt.
category: workflows
runtimes: [claude]
pii_safe: true
---

# thread-task

Spawn a focused sub-agent into a Discord thread, carrying full channel context.

## Invocation

Accepts both structured flags and natural language — parse intent from the full message.

### `/thread handback [thread-id or name]`
Pull the latest results from a thread back to the main channel on demand.

```
/thread handback                         ← summarize the most recent active thread
/thread handback ENG-685                 ← handback from thread matching that name
/thread handback <#<DISCORD_CHANNEL_ID>>  ← handback from specific thread ID
```

**Handback execution:**
1. Read the last 20 messages from the target thread:
   ```
   message action=read channel=discord channelId=[thread-id] limit=20
   ```
2. Summarize: what was done, what was found, what's next
3. Post summary to main channel:
   ```
   message action=send channel=discord target=[main-channel-id] message="📋 **Handback: [thread-name]**\n\n[summary bullets]\n\nFull thread: <#[thread-id]>"
   ```

---

```
/thread <name or description> [--model <alias>] [--ticket <ENG-xxx>] [--prompt <task>]
/thread channel <#channel-id or alias> [-> <task description>]
```

**Structured examples:**
- `/thread tokens-db-export`
- `/thread eng-686-deploy --ticket ENG-686 --model cursor-sonnet`
- `/thread rephish-test --model opus --prompt "test rePhish from GCP"`

**Cross-channel examples:**
- `/thread channel <#<DISCORD_CHANNEL_ID>> -> do the data lookup for <PRODUCT_NAME>`
- `/thread channel infra -> check k8s pod status`
- `/thread channel <PRODUCT_NAME> -> investigate auth failures`
- `/thread channel #security-intel -> threat check 1.2.3.4`

**Natural language examples (also valid):**
- `/thread tokens db migration` → thread name: "tokens-db-migration"
- `/thread rephish test on gcp model opus` → name: "rephish-test-gcp", model: opus
- `/thread eng-685 export tokens.db to cloud sql` → ticket: ENG-685, task from remaining text
- `/thread deploy deps ticket ENG-686 use cursor sonnet` → ticket: ENG-686, model: cursor-sonnet-thinking

**Parsing rules (NLP):**
- `/thread channel` keyword → cross-channel mode (see below)
- Extract ticket: any `ENG-NNN` or `eng-NNN` pattern in the message
- Extract model: words like "opus", "cursor", "sonnet", "flash", "gemini" near "model"/"use"/"with"
- Thread name: derive from the core noun phrase (slugify it)
- Task: anything descriptive that isn't a ticket/model signal becomes the prompt
- When ambiguous, use the full message text as both thread name and task

---

## Cross-Channel Mode (`/thread channel`)

Use this to create a thread in a **different** Discord channel and spawn the agent there.

### Channel Resolution (in order)
1. **Discord mention** `<#ID>` — use the numeric ID directly
2. **Alias** from `contexts/channel-registry.json` (e.g. `infra` → `<DISCORD_CHANNEL_ID>`)
3. **Channel name** — match `name` field in registry
4. **Numeric ID** — use directly if all digits

```bash
# Resolve alias to channel ID:
cat <LOCAL_PATH>/dev/contexts/channel-registry.json | python3 -c "
import json, sys
reg = json.load(sys.stdin)
channels = reg.get('channels', {})
for cid, ch in channels.items():
    if '[alias]' in ch.get('aliases', []) or ch.get('name') == '[alias]':
        print(cid)
        break
"
```

### Cross-Channel Execution Steps
1. **Resolve target channel ID** from mention, alias, or name (see above)
2. **Load BOTH contexts:**
   - Source channel (where <USER_NAME>is): haivemind + context file
   - Target channel: haivemind + context file
3. **Create thread in the TARGET channel:**
   ```
   message action=thread-create channel=discord channelId=[TARGET-channel-id] threadName=[thread-name]
   ```
4. **Spawn sub-agent** with target channel context, post-back to target thread
5. **Confirm in SOURCE channel** (where <USER_NAME>issued the command):
   ```
   Routing to #[target-channel-name] → thread "[thread-name]" | Agent: [model]
   ```
   Also send a brief note to the target channel so it's visible there too.

### Task from Context
When `/thread channel` is used, the task may come from:
- Text after `->` or `→` in the command: `/thread channel infra -> check pod status`
- A URL or reference provided (e.g. a Slack message link — fetch it and use that as the task)
- If no task given, use "investigate and report on current state" as the default

---

## Standard Mode (same channel)

## Execution Steps

### 1. Load Channel Context

```bash
# Get channel ID from session key
# e.g. agent:main:discord:channel:<DISCORD_CHANNEL_ID> → <DISCORD_CHANNEL_ID>

mcporter call haivemind.search_memories query="[channel-id] context" limit=10
# Read context file if it exists:
cat <LOCAL_PATH>/dev/contexts/[channel-id].md
```

### 2. Fetch Linear Ticket (if --ticket provided)

```bash
mcporter call linear.get_issue issue_id=[TICKET]
```

Extract: title, description, status, assignee.

### 3. Create Discord Thread

```
message action=thread-create channel=discord channelId=[channel-id] threadName=[thread-name]
```

Save the returned thread ID.

### 4. Build Sub-Agent Task

Compose a task prompt that includes:
- **Channel context:** project name, current state, recent decisions (from haivemind + context file)
- **Ticket context:** if --ticket provided, include ticket title + description
- **Task:** the --prompt or parsed task description
- **Post-back instruction:** "Post all results to Discord thread [thread-id] using: message action=send channel=discord target=[thread-id]"
- **Memory instruction:** "Search haivemind for [channel-id] context before starting. Store findings after with channel-id prefix."

See `references/task-template.md` for the full prompt template.

### 5. Spawn Sub-Agent

Use the requested model (default: `cursor-sonnet-thinking`). Always use `max-opus-high` for <PROJECT_NAME> channel tasks unless overridden.

```
sessions_spawn task="[composed task]" model=[model] mode=run runTimeoutSeconds=600
```

**MANDATORY: Add handback instructions to every sub-agent task prompt:**

```
## Handback (REQUIRED — do this last)
When your work is complete, post a final summary to the MAIN channel <#[source-channel-id]>:
  message action=send channel=discord target=[source-channel-id] message="✅ **[thread-name] — Done**

[3-5 bullet point summary of what was completed, what was found, what's next]

Full details: <#[thread-id]>"

This handback message is non-negotiable. It closes the loop so <USER_NAME>sees results in the main channel without having to check the thread.
```

### 6. Post opening message INTO the thread (MANDATORY — do this before spawning agent)

Immediately after creating the thread, post the first message INTO the thread:
```
message action=send channel=discord target=[thread-id] message="🧵 **[thread-name]**
Ticket: [ENG-xxx or none] | Model: [model]

**Context:**
[2-4 bullet points from haivemind/context file about current project state]

**Task:**
[what the agent is about to do]

Starting now — updates here as they happen."
```

This must happen BEFORE spawning the sub-agent. The thread must have content the moment it's created.

**In the current channel** reply with ONLY the link:
```
Thread created → <#[thread-id]>
```

All further progress, results, and sub-agent announcements go to the **thread**. Never post status/results to the main channel after the initial link.

---

## Model Aliases

| Alias | Resolves to |
|-------|------------|
| `opus` | max-opus-high |
| `opus-low` | max-opus-low |
| `sonnet` | cursor-sonnet-thinking |
| `cursor-sonnet` | cursor-sonnet-thinking |
| `cursor` | cursor-agent/auto |
| `flash` | gemini-flash |
| default (<PROJECT_NAME> channel) | max-opus-high |
| default (other) | cursor-sonnet-thinking |

## Channel Context Carried to Sub-Agent

Always include in the sub-agent task:
- Channel ID
- Project name (from context file or haivemind)
- Current state summary (last 3-5 bullet points from context or haivemind)
- Active Linear tickets (if known)
- Any explicit stop conditions or constraints from the context file

## Sub-Agent Post-Back + Handback Chain

**Thread** = workspace (all progress, intermediate results, logs)
**Main channel** = handback only (final summary when done)

### Handback format (sub-agent posts to main channel when complete):
```
✅ **[thread-name] — Done**

• [What was built/fixed/found — bullet 1]
• [Key finding or number — bullet 2]
• [Any remaining items or blockers — bullet 3]
• [Next step if applicable]

Full details: <#[thread-id]>
```

### Chaining
If the task prompt includes a "next task" or the handback reveals clear next steps, I (Jarvis) will:
1. Receive the handback in the main channel
2. Acknowledge it
3. Propose or auto-kick the next logical task (another `/thread` or direct action)

This creates a continuous loop: spawn → work → handback → chain → spawn.

Template for sub-agent instructions (see `references/task-template.md`).
