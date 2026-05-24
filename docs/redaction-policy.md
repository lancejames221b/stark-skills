# Redaction Policy

## Goal

Every file in `stark-skills` must be safe to commit and push without leaking personal information.

## What Must Be Redacted (or Parameterized)

- Personal names, usernames
- Email addresses
- Phone numbers
- Home/office addresses
- Private machine names and hostnames
- Private IPs (`192.168.x.y`, `10.x.y.z` in private contexts, `172.16–31.x`)
- Discord/Slack/Signal channel IDs and server/guild IDs
- Notion page/database IDs
- Google Drive folder/files IDs
- API keys, OAuth tokens, cookies (any form of credential)
- Local absolute paths (`/home/<user>/`, `C:\Users\<user>\`)
- Customer names, internal project codenames
- Real device/room names in voice skills

## Allowed Placeholders (Canonical Set)

```text
<USER_NAME>        — Person's name
<GITHUB_ORG>       — GitHub organization
<REPO_NAME>        — Repository name
<HOST_ALIAS>       — Host or computer alias (not FQDN)
<PRIVATE_IP>       — Private network address
<DISCORD_CHANNEL_ID>
<SLACK_CHANNEL_ID>
<NOTION_DATABASE_ID>
<GOOGLE_DRIVE_FOLDER_ID>
<PHONE_NUMBER>
<EMAIL_ADDRESS>
<LOCAL_PATH>       — Absolute filesystem path (e.g., /home/<user>/...)
<DEVICE_NAME>      — Home/media device name
<ROOM_NAME>        — Physical room name in voice workflows
```

## Tools and Checks

| Script / Doc                           | Purpose                                                                                                       |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `docs/redaction-policy.md` (this file) | Policy reference for all writers.                                                                             |
| `scripts/redact-skill.sh`              | Apply redaction patterns to a given skill or file.                                                            |
| `scripts/validate-no-pii.sh`           | Scan skills or targets for obvious PII and private values. Must be run on any new/edited files before commit. |
| `tests/fixtures`                       | Example values for testing redaction tools (private by design, ignored from repos).                           |

## Migration Process (from source → this repo)

1. Copy candidate into staging (`staging/` dir, git-ignored).
2. Run `scripts/redact-skill.sh --apply staging/<skill-name>/`.
3. Manually review the output (especially integrations and voice skills).
4. Run `scripts/validate-no-pii.sh staging/<skill-name>/`.
5. Only then move into `skills/` or `adapters/`.

## Important Notes

- **Never commit a `.gitignore` file that re-includes a private value.**
- **Always leave real redaction maps untracked** (`.gitignore`d).
- When in doubt, leave it out.
