---
name: plan
description: Produce a Qwen-ready implementation spec from a feature/UI request. Bakes in <USER_NAME>s modern-frontend design primer + a strict output format so the resulting plan can be handed to Qwen 3.6 (or any local executor) and produce on-brand code without an extra design pass. Use when the user says "plan this", "make a spec", "what's the plan for X", "design plan for X", or before kicking off any UI/feature work that needs to look polished.
category: planning
runtimes: [claude]
pii_safe: true
---

# /plan — Design-aware implementation spec

Produce a plan that's specific enough to execute mechanically. Two outputs:
1. A **plan markdown** saved to `./plans/<slug>.md` (or `--output`)
2. A **paste-ready ChatGPT meta-prompt** at the bottom <USER_NAME>can use externally to push GPT-5.5 to do real research

When the spec is handed to Qwen 3.6 (via opencode/PI/`/pdo`), Qwen must be able to execute without extra design judgment — the design choices are all spelled out.

## When to use

| Trigger | Choice |
|---|---|
| New feature / UI work | yes — always plan first |
| Bug fix touching ≤3 files | no — go direct |
| Refactor with cross-cutting design impact | yes |
| Quick prototype | no — but borrow the design primer |

## Output format (mandatory — Qwen reads this verbatim)

```markdown
# Plan: <slug>
**Task**: 1-2 sentence summary
**Scope**: in-scope vs out-of-scope, explicit
**Stack**: confirm Next.js 15 / React 19 / TypeScript strict / Tailwind v4 / shadcn/ui / Lucide
**References**: links to inspiration sites, existing components, design tokens

## Files

For each file to create or modify:

### `path/to/file.tsx` — [CREATE | MODIFY]
**Purpose**: 1 sentence
**Imports**:
- `<exact import line>`
**Exports**:
- `<exact signature>`
**Implementation directives**:
- bullet 1 — what it does, with explicit Tailwind classes / shadcn components / Lucide icons
- bullet 2 — explicit prop shapes, exact ARIA attributes, exact handler names
**Acceptance**:
- visible behavior assertion 1
- visible behavior assertion 2
**Loading state**: skeleton / suspense / N/A
**Empty state**: copy + CTA
**Error state**: how it surfaces

## Data flow

If applicable: where state lives, what fetches what, server vs client component split.

## Test plan

- Manual smoke: 3 explicit user actions to verify
- Mobile (375px): which 2 screens to spot-check
- Keyboard: 1 tab-through flow

## Open questions

Numbered list of things the executor (Qwen) should NOT decide on its own. If empty, write "None".
```

## <USER_NAME>s design primer (always include in the plan's `Stack` + `Implementation directives` sections)

### Stack defaults (do not vary unless the user overrides)
- Next.js 15 App Router + React 19, TypeScript strict, no `any`
- Tailwind v4 utility-only — no CSS modules, no styled-components
- shadcn/ui (owned in `components/ui/`) + Radix for behavior
- Lucide React only — no emoji, no Heroicons
- framer-motion for stateful animation; Tailwind transitions for hover/focus
- react-hook-form + zod for forms
- Geist Sans + Geist Mono via `next/font`

### Aesthetic — "modern" = Linear / Vercel / Stripe / Apple / Arc / Raycast
- **Dark default** + explicit light toggle (not auto-system)
- **Muted neutrals + ONE saturated accent** (default: `emerald-500` or `violet-500`)
- Backgrounds: `bg-zinc-950` / `bg-zinc-900`. Text: `text-zinc-100` primary / `text-zinc-400` secondary / `text-zinc-500` tertiary
- **Subtle borders, no big shadows** — `border border-zinc-800/60`, hover `ring-1 ring-zinc-700/30`
- **Density = Linear, not Salesforce** — `p-3` cards, `p-4` sections, `text-sm` body, `text-xs` metadata
- **Type rhythm**: titles `text-2xl tracking-tight font-semibold`, sections `text-base font-medium`, body `text-sm`, captions `text-xs text-zinc-500`. Never `font-bold` for body
- **Spacing**: 4px grid only — `gap-2/3/4/6`, never odd values
- **Radii**: `rounded-md` default, `rounded-xl` hero cards, `rounded-full` pills/avatars only
- **Motion**: 150–200ms ease-out, route-only page transitions

### Layout
- Command palette (cmdk) when ≥10 actions
- Persistent left rail ~240px collapsible
- Top bar minimal (breadcrumb + 1-2 actions)
- Centered `max-w-screen-xl` content (NOT edge-to-edge except tables/code)
- Tables: borders off, alternate-row off, sticky header on, hover highlight on, fixed widths

### Microcopy
- Action labels imperative + short ("Add member", "Save changes")
- Empty states: 1 line why + 1 CTA, no illustrations
- Errors: plain English, what failed + how to fix
- Pluralize 0/1/n correctly always

### Accessibility floor (non-negotiable)
- Keyboard reachable + `focus-visible:ring-2 focus-visible:ring-emerald-500/50`
- Form inputs paired with `<label>` (visible or sr-only)
- WCAG AA contrast on actual background
- `aria-label` on icon-only buttons
- `motion-safe:` / `motion-reduce:` for animations

### Anti-patterns (REJECT — these are the AI-frontend smells)
- Big drop shadows, gradients on every card, neon outlines
- Multi-color stat dashboards (red/yellow/green/blue squares)
- Center-aligned hero with placeholder image
- Inline styles, `!important`, deeply nested classname ternaries
- Emoji in product UI (✨🚀💡)
- Glassmorphism `backdrop-blur` cards everywhere
- More than 1 font family
- 4+ button styles — there are 3: primary (filled), secondary (outline/ghost), destructive

### File conventions
- One component per file, named export, file = component name
- Tailwind classes inline (no separate `.css`)
- Hooks in `hooks/` named `useThing.ts`
- Server Components default; `"use client"` only when needed
- Loading via Suspense + skeleton (NOT spinners)
- Errors via `error.tsx` + sonner toast for transient

### Code defaults
- Explicit return types on exports
- `unknown` + type guards instead of `any`
- Imports ordered: react/next → external → `@/components` → `@/lib` → relative → CSS
- Tailwind class order via prettier-plugin-tailwindcss (layout → spacing → sizing → typography → colors → effects → states)

### Acceptance for design quality (every plan must hit all 6)
- [ ] Looks at home next to a Linear/Vercel screenshot
- [ ] Works in dark + light without breakage
- [ ] Keyboard-navigable end to end
- [ ] Mobile 375px doesn't break (no horizontal scroll)
- [ ] ≤6 distinct hex colors visible per page
- [ ] Loading + empty + error states designed (not afterthoughts)

---

## ChatGPT 5.5 meta-prompt (paste-ready — the one <USER_NAME>uses externally)

When <USER_NAME>pastes a request into ChatGPT 5.5 to plan something, prepend with this block. It forces research + analysis depth that GPT tends to skip on its own:

````
ROLE: You are a senior staff engineer planning an implementation. You will produce a Qwen-ready spec, not prose.

REQUIRED RESEARCH (do this BEFORE writing the plan, do NOT skip):
1. Web-search for the latest stable versions of every library you intend to use. Cite version numbers.
2. Web-search 3 reference implementations of similar UIs from these companies: Linear, Vercel, Stripe. Quote 1 design choice from each that you'll borrow.
3. If the task involves a library you haven't used in 6 months, fetch its current docs page and quote the API signature you'll call.
4. List the 2 most likely failure modes and how the spec mitigates each.

FORMAT:
- Output the plan in EXACTLY this Markdown structure:
  # Plan: <slug>
  Task / Scope / Stack / References / Files / Data flow / Test plan / Open questions
- Each file gets a section with: Purpose, Imports (exact lines), Exports (exact signatures), Implementation directives (bullet-level explicit, with Tailwind classes / shadcn components / Lucide icons named), Acceptance criteria, Loading/Empty/Error states.
- No vague verbs. "Use a card" → "Use shadcn `<Card>` with `border-zinc-800/60` and `p-4`".
- TypeScript strict. No `any`. Explicit return types.
- Stack: Next.js 15 / React 19 / Tailwind v4 / shadcn/ui / Lucide. Do not propose anything else without justification.

DESIGN OPINION: target Linear / Vercel / Apple aesthetic. Dark by default. Muted neutrals + ONE accent. No emoji in product UI. Density like Linear, not Salesforce. ≤6 colors per page.

REJECT if your output:
- Contains "use a [generic component]" without exact library + className
- Skips loading/empty/error states
- Recommends a library you didn't research current version for
- Contains the word "robust" or "leverage"
````

## Behavior when invoked here

Two failure modes to avoid:
1. **Writing a plan from training data only** — produces stale advice for libraries that have moved on
2. **Writing a plan with no awareness of prior work** — re-suggests decisions <USER_NAME>has already made/rejected, repeats mistakes

So every `/plan` invocation MUST do BOTH a memory pass (Obsidian/hAIveMind via mcporter) AND a research pass (web) before writing a single line of the plan.

### Step 0 — Memory pass: pick up where you left off (do BEFORE research)

Before any web research, find out what's already been done. <USER_NAME>s memory is the source of truth — re-suggesting decisions he already made or repeating rejected approaches is the worst failure mode of a planner.

**A0. Read `./MEMORY.md` first if present.** Before any mcporter call, check for `./MEMORY.md` in cwd. This is the always-available local fallback — it works even when Obsidian and hAIveMind are offline. Grep it for the task's key terms and surface any matching entries above all other memory results. If <INFERENCE_HOST> is unreachable and `./MEMORY.md` exists, use it as the sole memory source and proceed (note in the plan: "Memory: local MEMORY.md only — <INFERENCE_HOST> offline").

**A. Always invoke `/load`** (or directly call `mcp__haivemind__search_memories` with `semantic=true`, `limit=8`) on the task's key terms. What you're hunting for:

- Prior plans on the same topic — read them. Don't replan from scratch if a plan already exists; extend or refine it.
- Decisions <USER_NAME>already made (architecture choices, library picks, design directions)
- Things he explicitly rejected (don't re-propose them)
- Status of related work — "is the API done? was the migration shipped? is there an open PR?"
- Most recent state of the project being planned for

**B. Look for prior plan files in the repo.** `ls plans/` or `find . -path '*/plans/*.md' -newer .git/HEAD~30 2>/dev/null`. If a previous plan exists for the same feature, READ IT and extend rather than replace.

**C. Use mcporter on <INFERENCE_HOST> for external memory** — Notion pages, hAIveMind beyond the local store, anything else. Pattern: `ssh <INFERENCE_HOST> 'mcporter call <server>.<tool> "param=value"'`. Don't ask <USER_NAME>to share Notion pages.

**D. Project context shortcuts.** If the task touches a known active project, search project-specific tags first:
- `discord-scraper` / `cohort-test` / `ENG-996`
- `<PROJECT_NAME>` / `<PROJECT_NAME>`
- `<PRODUCT_NAME>` / `<INTERNAL_SERVICE_HOST>`
- `<PROJECT_NAME>`
- `<VOICE_RUNTIME>` / `discord-<VOICE_RUNTIME>`
- `<PROJECT_NAME>` / `<PROJECT_NAME>`

**E. Cite memory in the plan.** The plan's "Research conducted" block must include a `## Memory` subsection listing every memory id read + key facts pulled. If memory turned up nothing, write "Memory: none — this is greenfield."

### Step 1 — Online research (do BEFORE writing anything)

Use WebSearch / WebFetch to:

1. **Library versions** — for every library or framework you'll propose (Next.js, React, Tailwind, shadcn/ui, etc.), search for the current stable version and any breaking changes in the last 90 days. Cite version numbers in the plan.
2. **Reference implementations** — find and read 2-3 real implementations of similar UIs/features. For UI work: search Linear / Vercel / Stripe / Apple design references. Quote at least one specific design choice from each that you'll borrow. For backend/infra: find the canonical pattern.
3. **API surface** — if the task uses a library you haven't actively used in the last few sessions, fetch its current docs page and quote the exact signature you'll call. Do not assume from training data.
4. **Failure modes** — search for "common pitfalls" / "gotchas" / "<library> bugs" on what you're proposing. Note 2 most likely.

If WebSearch is unavailable in the current environment (PI/opencode without web access), state that explicitly at the top of the plan as "Research conducted: NONE — proceeding from training data, treat plan as low-confidence". Do NOT proceed silently with stale knowledge.

### Step 2 — Clarify (only if genuinely ambiguous)

Ask 1-2 clarifying questions only when the task can't be planned without an answer. Otherwise proceed.

### Step 3 — Write the plan

Produce the plan in the format above. Save to `./plans/<slug>.md` (mkdir if needed). Include a top-of-file **"Research conducted"** block listing every search query + URL fetched + version cited, so the executor (Qwen) and reviewer (<USER_NAME>can audit the basis.

### Step 3.5 — Recommend the executor (which Qwen / local model to run this with)

Based on the task shape, recommend ONE local model from <USER_NAME>s catalog as the best fit, plus 1 backup. The plan output must include a `## Recommended executor` block. Use this matrix:

| Task shape | Primary | Backup | Why |
|---|---|---|---|
| **UI / design / frontend polish** | `qwen3.6-35b-a3b-turboquant-mlx` (alias `qwen`) | `qwen/qwen3-next-80b` (alias `qwen-next`) | 8bit quality matters for design judgment; flagship MoE has more world knowledge |
| **Pure code mechanics** (refactor, boilerplate, API binding) | `qwen/qwen3-coder-30b` (alias `coder`) | `qwen/qwen3-coder-next` (alias `coder-next`) | Coder-tuned, fastest at 4bit MoE |
| **Heavy reasoning / architecture / decisions** | `qwen/qwen3-next-80b` (alias `qwen-next`) | `qwen3.6-35b-a3b-turboquant-mlx` (alias `qwen`) | 80B-A3B has more headroom for non-trivial reasoning |
| **Long-context (full repo / large doc)** | `llama-4-scout-17b-16e-instruct` (alias `scout`) | `qwen3.6-35b-a3b-turboquant-mlx` | 10M ctx, scout is the only one with that range |
| **Quick prototype / throwaway** | `glm-4.7-flash-mlx@4bit` (alias `glm`) | `openai/gpt-oss-20b` (alias `gpt-oss`) | Smallest fast models, good enough for one-shot |
| **Mixed coder + design work (most common)** | `qwen/qwen3-coder-next` (alias `coder-next`) | `qwen3.6-35b-a3b-turboquant-mlx` | Best of both worlds, big enough for design judgment |

The block should look like:

```markdown
## Recommended executor

**Primary**: `<full-id>` (alias `<alias>`)
**Backup**: `<full-id>` (alias `<alias>`)
**Reasoning**: 1-line why
**Warm command**: `lms-warm <full-id> "$(cat plans/<this-plan>.md)"` — pre-load and prime cache with the plan as the system prompt.
```

If the task is genuinely ambiguous on shape, recommend `qwen-next` (the new flagship) as the safe default — it's the broadest-capability model in the local catalog as of 2026-05-10.

### Step 4 — Save the plan to memory

After writing the plan file:

- Invoke `/save` with category `project` to save a memory entry pointing at the plan file (so future `/plan` calls find it via Step 0). Body should include: task summary, slug, key decisions, and the path to the plan markdown.
- Optional flag `:notion` if the plan should also push to Notion (only if <USER_NAME>has said this is a customer-visible project).

### Step 5 — Hand off

Print:
- The output file path
- The hAIveMind memory id from Step 4
- One-line next step: `Hand to Qwen via /pdo, or refine in ChatGPT with the meta-prompt above`

Reminder: this skill is plan-only — never write implementation code here.

## Related

- `/pdo` — execute the plan with local Qwen
- `/oplan` — Opus-driven version (for the heaviest planning needs)
- `/pplan` — local-PI version (for fully private planning)
- The design primer is duplicated as the first section so this file is self-contained
