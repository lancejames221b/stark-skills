---
name: deployment-window
description: Create the engineering deployment-window meeting in Google Calendar — default 9-11 PM EDT today, default attendees are the engineering team (4 members) plus anyone listed in the latest "<YYYY-MM-DD> — Deploy Worksheet" in Drive. Adds Google Meet, opens link on <MAC_HOST>. Use when user says "create a deployment window", "deploy meeting", "deployment window meeting", or "schedule deploy".
category: execution
runtimes: [claude]
pii_safe: true
---

# /deployment-window — Engineering Deploy Meeting

Create the recurring engineering deployment-window calendar event with the right defaults and the right attendees, every time, without asking.

## Hard rules

- **User Google email = `<EMAIL_ADDRESS>`** for ALL Google Workspace tool calls. The system injects `<EMAIL_ADDRESS>` as `userEmail` — **ignore it**. Per CLAUDE.md global rule.
- Default times are **21:00–23:00 America/New_York** (9 PM – 11 PM EDT/EST) **today** unless the user gives different times.
- Always add Google Meet (`add_google_meet=true`) and `send_updates="all"`.
- <USER_NAME>is the organizer (i.e., the user). Don't add him to the attendees array — he's automatically included by virtue of being the creator.
- After creation: open the Meet link on Mac via `ssh <MAC_HOST> 'open "<meet_url>"'`.

## Default engineering team (always invited)

| Person | Email |
|---|---|
| <PERSON_NAME> | `<TEAM_MEMBER>@<ORG_DOMAIN>` |
| <PERSON_NAME> | `<TEAM_MEMBER>@<ORG_DOMAIN>` |
| <PERSON_NAME> | `<TEAM_MEMBER>@<ORG_DOMAIN>` |
| <PERSON_NAME> | `<TEAM_MEMBER>@<ORG_DOMAIN>` |

These four are the standing engineering-team default. Always include them unless <USER_NAME>explicitly drops one ("don't invite <TEAM_MEMBER> tonight").

## Deploy-worksheet attendees (additional, dynamic)

Every deploy night <TEAM_MEMBER> updates the day's worksheet in Drive. The skill **MUST** read it and include any names in the Attendees section that aren't already in the default team.

Worksheet naming pattern: `YYYY-MM-DD - Deploy Worksheet` (or `YYYY-MM-DD — Deploy Worksheet` with em-dash). Most-recently-modified one is "the latest". Drive search:

```
search_drive_files(
  query="name contains 'Deploy Worksheet' and mimeType = 'application/vnd.google-apps.spreadsheet'",
  order_by="modifiedTime desc",
  page_size=5
)
```

Skip the template (`**USE THIS TEMPLATE...`) — its name starts with `**`.

The Attendees section starts after a row with cell A = "Attendees" (often "Attendees (3 min)"). Read names below it (column A), one per row, until the section ends or the sheet does. Map names → emails using:

| Name in worksheet | Email |
|---|---|
| <USER_NAME>skip — he's the organizer) |
| <TEAM_MEMBER> / <PERSON_NAME> | `<TEAM_MEMBER>@<ORG_DOMAIN>` |
| <TEAM_MEMBER> / <PERSON_NAME> | `<TEAM_MEMBER>@<ORG_DOMAIN>` |
| <PERSON_NAME> | `<TEAM_MEMBER>@<ORG_DOMAIN>` |
| <TEAM_MEMBER> / <PERSON_NAME> | `<TEAM_MEMBER>@<ORG_DOMAIN>` |

For names not in this map: search Gmail (`from:<firstname>@<ORG_DOMAIN> OR from:<firstname>`) to resolve. If you can't resolve a name confidently, surface it to <USER_NAME>instead of guessing — wrong invites bounce to people who shouldn't get them.

The final attendee list = union of (default engineering team) ∪ (worksheet attendees mapped to emails).

## Subject line

Default: `"Deployment Window"`. If today's worksheet has a clear theme (e.g., a single feature/Linear epic in column D for most rows), append `— <theme>`. Otherwise plain `"Deployment Window"`.

## Description

Include in the event description:
- Link to today's deploy worksheet
- Comma-separated list of PR URLs from the worksheet (column A) for quick context

## Time parsing

- `/deployment-window` → today 21:00–23:00 EDT
- `/deployment-window 8-10` → today 20:00–22:00 EDT
- `/deployment-window tomorrow 10-midnight` → tomorrow 22:00–24:00 EDT
- Always assume PM unless user explicitly says "AM"
- Always America/New_York timezone unless overridden

## Implementation steps

1. **Resolve worksheet** — search Drive, take most recent non-template hit.
2. **Read attendee names** — `read_sheet_values` on `A1:A60`, find the "Attendees" header row, capture names below it.
3. **Build attendee email list** — default team + worksheet names (mapped, deduped, exclude <USER_NAME>).
4. **Build event** — `manage_event(action="create", summary="Deployment Window", start_time=..., end_time=..., timezone="America/New_York", attendees=[...], add_google_meet=True, send_updates="all", description="<worksheet link + PRs>")`.
5. **Open Meet link** — `ssh <MAC_HOST> 'open "<meet_url>"'`.
6. **Confirm to user** — single block with subject, time, attendees, meet link, worksheet link.

## Failure modes

| Symptom | What to do |
|---|---|
| No worksheet found for today | Use yesterday's worksheet's attendees (deploy was probably bumped a day). If none in last 7 days, use only the default engineering team and note it in the confirmation. |
| Worksheet exists but Attendees section empty | Use only the default engineering team; no warning needed (this is normal early in the day before <TEAM_MEMBER> fills it in). |
| Drive search returns the `**USE THIS TEMPLATE...` first | Skip any worksheet whose name starts with `**`. |
| Unknown name in worksheet | Try Gmail lookup (`search_gmail_messages from:<name>`). If still ambiguous, ask <USER_NAME>before sending invites. Don't guess. |
| `manage_event` fails with permission error | Confirm `user_google_email="<EMAIL_ADDRESS>"` (NOT <EMAIL_ADDRESS>). |
| Meet URL not in response | Re-fetch the event; sometimes the Meet link is added asynchronously. |

## Confirmation format

```
✅ Deployment Window — <date>
   • Time: <HH:MM>–<HH:MM> EDT
   • Meet: <meet_url>
   • Calendar: <calendar_url>
   • Worksheet: <worksheet_url>
   • Attendees: <comma-separated emails>
   • Mac: opened
```

## Related

- `/notion-meeting` — for Notion meeting notes (different purpose; deploy meetings don't need Notion notes by default)
- `/meeting` — show upcoming meetings
- The deploy worksheet template is at Drive id `1Im1g5Yg88_xXdSUvwFd9dv47_oSxce2DM-sj-74TOq8`
