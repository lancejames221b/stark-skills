# Sub-Agent Task Template

Use this template when composing the task prompt for the spawned sub-agent.

---

## Template

```
You are working on [PROJECT_NAME] in Discord channel [CHANNEL_ID].

## Channel Context
[PASTE HAIVEMIND + CONTEXT FILE SUMMARY HERE — 5-10 bullet points of current state]

## Active Tickets
[TICKET_ID]: [TICKET_TITLE] — [TICKET_STATUS]
[Description: first 300 chars of ticket description if available]

## Your Task
[TASK_DESCRIPTION]

## Memory Instructions
1. Before starting: search haivemind → mcporter call haivemind.search_memories query="[CHANNEL_ID] [PROJECT_NAME] [TASK_KEYWORD]" limit=10
2. After completing: store findings → mcporter call haivemind.store_memory content="[CHANNEL_ID] [TASK_NAME]: [summary of what you did/found]" category=[appropriate-category]

## Post-Back Instructions
Post ALL progress and intermediate results to Discord thread [THREAD_ID]:
  message action=send channel=discord target=[THREAD_ID] message="[your update]"

## Handback (MANDATORY — final step, non-negotiable)
When ALL work is complete, post a summary back to the MAIN channel [CHANNEL_ID]:
  message action=send channel=discord target=[CHANNEL_ID] message="✅ **[TASK_NAME] — Done**

• [key result 1]
• [key result 2]
• [key result 3]
• Next: [what comes next if applicable]

Full details: <#[THREAD_ID]>"

This closes the loop. <USER_NAME> sees the result in the main channel. The thread has the full transcript.

## Constraints
- [Any constraints from context file — e.g. "DO NOT start any services", "Do not modify live scripts"]
- Stop and report if you hit anything requiring manual intervention or approval
```

---

## Example (<PROJECT_NAME> Channel)

```
You are working on the <PROJECT_NAME> project (<PROJECT_NAME>) in Discord channel <DISCORD_CHANNEL_ID>.

## Channel Context
- DB migration DONE: 17,575 bots in Cloud SQL (<PROJECT_NAME>, <PRIVATE_IP>)
- ELSER search live: <PROJECT_NAME>, 1.24M docs, hybrid search at 9ms
- Phase 0 cutover prep DONE: 13 systemd units staged on <PROJECT_NAME>, all disabled
- scripts deployed to /opt/<PROJECT_NAME>/: token_grabbers, slack_cli, kit_sniper, rephish
- PG write target confirmed: process_tokens_v8.py → localhost Docker PG on <WORKSTATION_HOST>
- <WORKSTATION_HOST> SSH: root@<TAILSCALE_IP> (Tailscale)
- <PROJECT_NAME>: gcloud compute ssh <PROJECT_NAME> --zone=us-central1-a --project=<PROJECT_NAME>

## Active Tickets
ENG-686: Deploy token scraper services on GCP (13 tmux to systemd) — Triage
Description: Migrate all 13 active tmux sessions from <WORKSTATION_HOST> to systemd services on <PROJECT_NAME>.

## Your Task
Install Python dependencies on <PROJECT_NAME> for the token scraper services.
Test that psycopg2, telethon, aiohttp, aiofiles, cryptg all import successfully.
Check rePhish requirements.txt and install those too.

## Memory Instructions
1. Before starting: mcporter call haivemind.search_memories query="<DISCORD_CHANNEL_ID> <PROJECT_NAME> cutover deps" limit=10
2. After: mcporter call haivemind.store_memory content="<DISCORD_CHANNEL_ID> ENG-686 python deps: [results]" category=infrastructure

## Post-Back Instructions
Post results to Discord thread <DISCORD_CHANNEL_ID>:
  message action=send channel=discord target=<DISCORD_CHANNEL_ID> message="..."

## Constraints
- DO NOT start or enable any systemd services
- DO NOT modify process_tokens_v8.py on <WORKSTATION_HOST> (it's live)
- DO NOT activate the cutover — phase 0 only
```
