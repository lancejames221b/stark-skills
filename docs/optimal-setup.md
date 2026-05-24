# Optimal Setup — One Practitioner's AI-Augmented Workflow

> **What this is.** One person's working architecture for an AI-augmented dev/ops/life
> workflow. `stark-skills` is the skill layer. The setup that gets the most value out of
> it also has a memory layer, a voice layer, a notes layer, and a way to use more than
> one machine without thinking about it. This document describes the whole stack so a
> reader can copy the parts they want and skip the parts they don't.
>
> **What this is NOT.** A turnkey product. A recommendation that you adopt all of it.
> A claim that this is *the* right way to do it. It's one configuration that works,
> shared so you can borrow ideas. Every component listed here is replaceable. Most are
> optional.

---

## Why read this

The skills in `stark-skills/` are designed to compose with other tools. A skill named
`/save` writes to a memory store. A skill named `/handoff` posts to a notes provider.
A skill named `/sonos-announce` talks to a voice runtime. Read in isolation, the
skills look like they reference things that don't exist. They reference a working
configuration — described here.

If you just want to install one or two skills, you don't need this doc. If you want
the full experience the skills were designed for, this is the recipe.

Reading time: ~15 minutes. Minimum viable setup time: ~30 minutes. Full setup with
all optional components: a weekend, plus ongoing tuning.

---

## The stack at a glance

```
                           ┌───────────────────────────┐
                           │   You (terminal / voice)  │
                           └─────────────┬─────────────┘
                                         │
                       ┌─────────────────┴─────────────────┐
                       │      Claude Code  (or Codex,      │
                       │      OpenCode, etc.)              │
                       │      + skills from stark-skills   │
                       └─┬───────────┬───────────┬─────────┘
                         │           │           │
            ┌────────────┘           │           └────────────┐
            │                        │                        │
            ▼                        ▼                        ▼
   ┌────────────────┐      ┌──────────────────┐    ┌────────────────────┐
   │  Memory layer  │      │  Notes / intake  │    │  Voice layer       │
   │                │      │  layer           │    │                    │
   │  agent-        │      │  Notion (MCP)    │    │  openjarvis        │
   │  hivemind      │◄────►│                  │    │  (Discord +        │
   │  +             │      │                  │    │   speech)          │
   │  Obsidian      │      │                  │    │                    │
   └────────────────┘      └──────────────────┘    └────────────────────┘
            ▲                        ▲                        ▲
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     │
                ┌────────────────────┴────────────────────┐
                │   mcporter — cross-host MCP frontend    │
                │   (one CLI; talks to any MCP server     │
                │    on any reachable machine)            │
                └────────────────────┬────────────────────┘
                                     │
                ┌────────────────────┴────────────────────┐
                │   Multi-machine fabric                  │
                │                                         │
                │   workstation  ──┐                      │
                │                  │  Tailscale + SSH     │
                │   inference  ────┤  aliases             │
                │                  │                      │
                │   mac        ────┘                      │
                └─────────────────────────────────────────┘
                                     │
                ┌────────────────────┴────────────────────┐
                │   Local inference                       │
                │   LM Studio / Ollama with Qwen,         │
                │   distilled Opus-class models, etc.     │
                └─────────────────────────────────────────┘
```

The pieces in plain English:

- **Skills layer** — `stark-skills` (this repo). Markdown files that teach an agent
  how to do specific things and when to do them.
- **Memory layer** — a place for the agent to write down what it just learned and
  read it back later, across sessions and machines.
- **Notes layer** — where humans and agents put structured artifacts that need to be
  shared, edited, and revisited: meeting notes, plans, decisions.
- **Voice layer** — a way to talk to the agent and have it talk back, untethered from
  the terminal.
- **Multi-machine fabric** — SSH plus Tailscale so any host can call any other host
  with a short alias.
- **Local inference** — runs models on hardware you own when latency, cost, or
  privacy matters more than capability.

You can run with just the skills layer and a memory store. Everything else is opt-in.

---

## Layer 1 — Skills (this repo)

Install `stark-skills` into whatever coding agent you use. The repo ships install
scripts for Claude Code, the `pi` agent, and OpenCode. All scripts default to
`--dry-run`.

```bash
git clone https://github.com/lancejames221b/stark-skills.git
cd stark-skills

# See what would be installed
./scripts/install-claude.sh --dry-run

# Install a single skill
./scripts/install-claude.sh skills/core/handoff/

# Install everything for Claude Code
./scripts/install-claude.sh --force
```

Default install paths:

| Agent    | Env var                  | Default                              |
| -------- | ------------------------ | ------------------------------------ |
| Claude   | `CLAUDE_SKILLS_DIR`      | `~/.claude/skills`                   |
| pi       | `PI_SKILLS_DIR`          | `~/.pi/agent/skills`                 |
| OpenCode | `OPENCODE_COMMANDS_DIR`  | `~/.config/opencode/commands`        |

After install, the agent picks up skills automatically the next time it starts. Most
skills declare trigger phrases in their frontmatter so the agent invokes them
without being asked.

**First skill to try.** Once installed, ask your agent: *"save this conversation as
a note"*. If you have a memory layer (next section), the `/save` skill will fire and
persist a summary. If you don't have one yet, the skill will tell you what's missing.

---

## Layer 2 — Memory (agent-hivemind + Obsidian)

The most useful add-on. Without a memory layer, every agent session starts cold.
With one, the agent remembers decisions, naming conventions, your toolchain, and
what it tried last time.

Two pieces, used together:

### agent-hivemind — semantic memory store

[`lancejames221b/agent-hivemind`](https://github.com/lancejames221b/agent-hivemind)
is a self-hosted MCP server that gives an agent a vector database plus keyword
search over its own memories. It's the canonical write target for short bursts:
*"remember that the staging password rotates Friday"*. It also stores cross-machine
state — what was happening on the workstation when you switched to the laptop.

Install (from the agent-hivemind repo's own README — link out for the latest
instructions). Once it's up, expose it as an MCP server in your agent config. From
that point forward, any skill that calls `mcp__haivemind__*` (or `mcporter call
haivemind.*`) will work.

### Obsidian — human-readable canonical store

[Obsidian](https://obsidian.md) is a local-first markdown editor. In this stack it
plays a complementary role: it's the place where humans go to actually *read* their
notes, hand-edit them, link them to each other, and build a long-lived knowledge
graph. agent-hivemind is great for retrieval; Obsidian is great for browsing.

Pattern: the `/save` skill writes a markdown file into a vault folder, then asks
agent-hivemind to index it. You can read and edit the file directly in Obsidian.
The agent reads it back via agent-hivemind's semantic search.

### The user-facing verbs

Once both are wired up, two skills become the daily drivers:

| Skill   | What it does                                                          |
| ------- | --------------------------------------------------------------------- |
| `/save` | Writes a markdown note to Obsidian and indexes it in agent-hivemind.  |
| `/load` | Searches agent-hivemind and pulls the relevant note(s) into context.  |

Use them like punctuation:

```
> /save the cron schedule for the index rebuild is 0 3 * * 0
saved: 2026-05-24-cron-schedule.md (haivemind id: 7a3f...)

> later, in a fresh session...
> /load what's the cron schedule for the index rebuild
[loads the note, agent picks up where it left off]
```

This single pattern — `save` everything important, `load` when starting a new
session — is what most of the rest of the stack is built around.

---

## Layer 3 — Notes & intake (Notion)

Memory is for the agent. Notion is for collaboration: meetings, plans, decisions,
anything you'd want a human teammate to be able to read and edit alongside the
agent.

Use the [official Notion MCP server](https://www.npmjs.com/package/@notionhq/notion-mcp-server)
(or whichever current MCP build Notion publishes). Once configured, agents can:

- Create new pages from a meeting transcript.
- Query structured databases (a database of plans, a database of decisions, etc.)
- Append meeting follow-ups as child pages.
- Read back what was decided three weeks ago.

The pattern that makes this work: keep a small number of *structured* Notion
databases — meetings, plans, handoffs, decisions — each with a consistent schema.
Agents query by schema (date range, tag, status) instead of by full-text search,
which gives much higher precision.

The `/handoff` skill in this repo is a good example. It writes a meeting-style page
to a Notion database with a known schema, then drops an index entry into
agent-hivemind so the next session can find it.

> **Local Notion MCP gotcha.** The local-mode Notion MCP only sees pages that have
> been explicitly shared with the integration via Notion's UI. Hosted Notion MCP
> (via OAuth) sees everything you have access to. Several skills in this repo
> assume the OAuth flavor.

---

## Layer 4 — Voice (openjarvis)

Optional but transformative. If you only ever interact with the agent through a
terminal, you don't need this layer.

[`lancejames221b/openjarvis`](https://github.com/lancejames221b/openjarvis) is a
Discord-first voice runtime. It pipes speech-to-text → agent (with skills) →
text-to-speech, with Discord as the transport so you can talk to the agent from a
phone, a watch, or any device that runs the Discord app.

Why Discord as the transport:

- Already runs everywhere.
- Handles auth, presence, push notifications, and message history for free.
- Easy to spin up a channel per project — voice becomes scoped.
- A built-in audit log of every voice exchange.

The voice-tier skills in `stark-skills/skills/voice/` are designed to ride on
openjarvis. They handle things like:

- Morning briefing (calendar + email + PRs, read out loud).
- "Where did I put X" style item-location memory.
- Voice control of media (Roku, Plex, Sonos).
- Push-to-speaker routing ("send this to the kitchen speaker").

Run openjarvis on whichever machine has the spare CPU and the best mic situation
(often a desktop or a small always-on box). Wire it up to the same agent-hivemind
instance the rest of your stack uses and voice exchanges automatically become part
of the same memory plane as your terminal sessions.

---

## Layer 5 — Multi-machine fabric

You can run all of the above on a single laptop. It's nicer with more than one
machine, and most of the interesting skills assume at least two reachable hosts.

The reference pattern is three hosts:

| Role             | What runs there                                              |
| ---------------- | ------------------------------------------------------------ |
| **workstation**  | Your primary terminal. Coding agent. Browser. Editor.         |
| **inference**    | Bigger box with a GPU. Local models, heavy MCP servers.       |
| **mac**          | Apple Silicon. MLX / LM Studio for Apple-only model variants. |

You may collapse two of them into one machine if you don't need all three. The
important thing is that they can reach each other.

### SSH aliases

Every skill that talks to another host does it via `ssh <HOST_ALIAS>`. Set up an
`~/.ssh/config` so the aliases work:

```
Host workstation
  HostName <internal-ip-or-tailscale-name>
  User <you>

Host inference
  HostName <internal-ip-or-tailscale-name>
  User <you>

Host mac
  HostName <internal-ip-or-tailscale-name>
  User <you>
```

Pick whatever names match how you think. The skills in this repo use placeholder
host aliases like `<WORKSTATION_HOST>`, `<INFERENCE_HOST>`, `<MAC_HOST>`. Swap in
your real names when you install.

### Tailscale (or your VPN of choice)

[Tailscale](https://tailscale.com) gives every host a stable name and a stable IP
that work whether you're at home, on a coffee shop wifi, or behind a corporate
NAT. The skills don't care which VPN you use — they just assume the SSH alias
works from wherever you happen to be.

### mcporter — one CLI for every MCP server, on every host

[`mcporter`](https://github.com/openclaw/mcporter) (or your preferred MCP-CLI
shim) is what makes the multi-host setup actually pleasant. Without it, you'd be
maintaining separate MCP client configs on every host. With it, one command on any
host can reach any MCP server on any other host:

```bash
# From workstation, call a tool on the inference host's notion MCP server
ssh inference 'mcporter call notion.notion-search query="release plan"'

# From the inference host, push a memory to haivemind
mcporter call haivemind.store_memory content="..." category="operations"
```

Several skills assume you can do this fan-out. The conventional pattern is: run
the heavy MCP servers (Notion, haivemind, Google Workspace) on the inference host;
call them from anywhere via `ssh inference 'mcporter call ...'`.

---

## Layer 6 — Local inference (LM Studio, Ollama)

Optional. Use it when you want a private model handling something that doesn't
need frontier capability.

Two runtimes worth installing:

- **[LM Studio](https://lmstudio.ai)** — GUI for downloading + running GGUF and
  MLX models. Good on Apple Silicon. Exposes an OpenAI-compatible HTTP server.
- **[Ollama](https://ollama.ai)** — CLI-first. Great on Linux + NVIDIA. Also
  exposes an OpenAI-compatible HTTP server.

Pattern: keep one Qwen-class model and one distilled large model loaded on the
inference host. Wire your local agents (Cline / Continue / etc.) to hit them via
the LAN address. Skills in this repo that mention "local inference" (e.g.
`/lms-warm`, `/ollama-pull`, `/cline-model`) all assume you've done this and just
need orchestration verbs.

You do not need a local model to use any of the skills in this repo. They're
opt-in.

---

## How the pieces talk

A normal day looks like this:

1. You start a terminal session on the workstation. You type `/load what was I
   doing yesterday on the index rebuild project`.
2. The agent calls `mcporter call haivemind.search_memories` over the local MCP
   bridge.
3. agent-hivemind returns 3 relevant notes; the agent pulls the canonical
   markdown files from the Obsidian vault and reads them.
4. You work for an hour. You hit a decision point you want to record.
5. You say `/save the index rebuild now uses Qwen3 instead of Llama for the
   reranker; cost dropped 40%`.
6. The agent writes `~/obsidian/notes/2026-05-24-index-rebuild-reranker.md` and
   indexes it in agent-hivemind.
7. Your phone buzzes — your meeting starts in 5 minutes. You switch to voice:
   *"Jarvis, brief me on the index rebuild project."*
8. openjarvis (running on the inference host) gets the speech, transcribes it,
   asks the agent. The agent runs `/load index rebuild`, reads the note from
   step 6, and the TTS reads back the summary on the kitchen speaker.
9. The meeting wraps. You say *"save the decision: ship the new reranker on
   Tuesday."* It lands in agent-hivemind, available to both the voice runtime
   and the terminal session on the workstation, both of which are using the
   same memory plane.

The mortar that holds this together: `mcporter`, the SSH aliases, and a shared
memory layer. Once you have all three, every host feels like the same computer.

---

## Recommended companion repos

| Repo                                                                                                              | What it is                                                            |
| ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| [`lancejames221b/stark-skills`](https://github.com/lancejames221b/stark-skills) (this repo)                       | Skill library for coding/voice agents.                                |
| [`lancejames221b/agent-hivemind`](https://github.com/lancejames221b/agent-hivemind)                               | Self-hosted MCP memory server (semantic + keyword search).            |
| [`lancejames221b/openjarvis`](https://github.com/lancejames221b/openjarvis)                                       | Discord-first voice runtime that hosts skills.                        |

Each repo is independently usable. You can install stark-skills without ever
touching agent-hivemind; you'll just skip the memory-dependent skills. You can
run openjarvis without stark-skills; you'll just have a voice runtime without
the higher-level workflows.

---

## Recommended SaaS

| Service                                            | Why                                                                                                                      |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| [Notion](https://notion.so)                        | Meeting notes, plans, decisions. Has an official MCP server. Best collab surface for agent-assisted work.                |
| [Obsidian](https://obsidian.md)                    | Local-first markdown vault. Canonical write target for `/save`. Free for personal use.                                   |
| [1Password](https://1password.com)                 | Secret store. Accessed via the `op` CLI or the 1Password SSH agent. The `1ps` skill in this repo wraps it.               |
| [Tailscale](https://tailscale.com)                 | Stable hostnames across networks. Free tier covers most personal setups.                                                 |
| [Trello](https://trello.com) (optional)            | Long-running project boards. Has an official MCP server. The `trello` skill in this repo wraps it.                       |
| [GitHub](https://github.com) (you already use it)  | Source of truth for code. `gh` CLI is assumed by several skills.                                                         |

All of them have free tiers that are sufficient for one person. None of them
lock you in — every skill that touches a SaaS provider does it through MCP, so
swapping providers is mostly a matter of swapping the MCP server.

---

## You don't need all of it

The minimum viable setup is **two pieces**:

1. A coding agent (Claude Code, OpenCode, Codex, whatever).
2. A memory store.

That's it. With just those two, you can install the `/save` and `/load` skills
from this repo and the agent gets a persistent memory across sessions. Total
setup time: ~15 minutes.

From there, each additional layer is opt-in:

| Add this layer       | When it starts to be worth it                                            |
| -------------------- | ------------------------------------------------------------------------ |
| Notes layer (Notion) | When you have meetings whose notes you want the agent to read.           |
| Voice layer          | When you want to use the agent away from the keyboard.                   |
| Multi-machine fabric | When one machine isn't enough (GPU on a second box, mobile while away).  |
| Local inference      | When cost, latency, or privacy matter more than capability.              |

You can stop at any point. There is no "you must complete the whole stack to
benefit" cliff.

---

## A 30-minute path from zero

If you're starting from nothing and want something working today, do this in
order. Each step is ~5 minutes.

### 1. Install your coding agent

Claude Code, OpenCode, Codex — whichever you prefer. This doc's examples use
Claude Code's conventions but the skills work in any of them.

### 2. Clone stark-skills

```bash
git clone https://github.com/lancejames221b/stark-skills.git
cd stark-skills
```

### 3. Install one skill to verify the install path

```bash
./scripts/install-claude.sh --dry-run
./scripts/install-claude.sh skills/core/handoff/
```

Confirm the file showed up at `~/.claude/skills/handoff/SKILL.md`.

### 4. Set up agent-hivemind

Follow the install instructions in
[`lancejames221b/agent-hivemind`](https://github.com/lancejames221b/agent-hivemind).
You'll end up with an MCP server running locally.

### 5. Add agent-hivemind to your agent's MCP config

This step varies by agent. For Claude Code, edit `~/.claude/settings.json` and
add the haivemind MCP server. Restart the agent.

### 6. Install the memory skills

```bash
./scripts/install-claude.sh skills/core/memory/
./scripts/install-claude.sh skills/core/handoff/
```

### 7. Try `/save` and `/load`

Start a fresh agent session. Type:

```
/save the agent install path on this machine is ~/.claude/skills
```

Then start *another* fresh session and type:

```
/load where is the agent install path
```

If the agent returns your note, the loop is working.

You now have a persistent-memory coding agent. Everything beyond this is
acceleration.

---

## What this is NOT

- **A turnkey product.** It's a set of opinions about how the pieces fit
  together, plus the glue. You will still spend setup time.
- **The only way to do this.** Plenty of other configurations work. This one
  is documented because it's the one this repo's skills were built against.
- **A monolith.** Every piece is replaceable. Don't like Obsidian? Use Logseq.
  Don't like Tailscale? Use ZeroTier or plain WireGuard. Don't like Notion?
  Skip the notes layer entirely.
- **Free.** Notion has a free tier; 1Password and Tailscale have paid tiers
  that personal users can usually live without. The biggest hidden cost is
  *time*: getting the multi-host fabric working will eat a Saturday.

---

## Tradeoffs worth knowing up front

- **Memory drift.** A semantic memory store will surface notes that *look*
  relevant but are out of date. The `/save` convention of always including a
  date in the note title helps; you'll still occasionally have to manually
  prune.
- **MCP-server sprawl.** Each new SaaS adds an MCP server. Each MCP server is
  another process to monitor and another auth flow to keep alive. `mcporter`
  helps consolidate the *client* side but doesn't reduce the server count.
- **Skill collisions.** Skills declare trigger phrases. If two skills both
  claim *"brief me"*, the agent has to disambiguate. Periodically audit your
  `~/.claude/skills/` for trigger overlap.
- **Voice latency.** STT + LLM + TTS is rarely under 2 seconds end-to-end.
  Voice is best for *initiating* work, not for tight back-and-forth.
- **Multi-host security.** Anything reachable over Tailscale is reachable from
  any of your devices, which means a compromised laptop can read your memory
  store. Treat the inference host like a production service.

---

## Where to go next

- Read [`docs/install.md`](install.md) for skill-by-skill install details.
- Read [`docs/multi-agent-workflows.md`](multi-agent-workflows.md) for examples
  of skills composing into end-to-end procedures.
- Read [`docs/redaction-policy.md`](redaction-policy.md) before contributing
  any skill that originated from your private setup.
- Browse [`skills/core/`](../skills/core/) to see what's available.
- Browse [`skills/voice/`](../skills/voice/) if you set up the voice layer.

If something is unclear, the friendliest fix is a PR that clarifies it. This
doc is a living artifact — it gets sharper every time a stranger tries to
follow it and tells us where they got stuck.
