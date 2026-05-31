---
name: vibe-code
description: The mode where CLAUDE drives and QWEN (a cheap local model) executes. Claude plans the smallest next step as INTENT + CONTRACT + GATE (not code), hands it to qwen via the qwen-do executor or a warm tmux session, independently verifies qwen's artifacts (never the self-report), and runs a continuous-improvement loop that feeds surgical corrections back so qwen's unaided hit-rate rises over time. Claude is the human at the wheel: it can stop a spinning run (Esc / Ctrl-C / kill the session). The inverse of vibe-plan/vibe-verify (where qwen drives and calls Claude). Use when there is real executable work a local model can type out under Claude's direction. Trigger phrases - "/vibe-code", "vibe code this", "drive qwen", "let me orchestrate qwen", "Claude drives qwen executes".
---

# /vibe-code - Claude drives, qwen executes, both get better over time

In vibe-code, CLAUDE is the orchestrator (the "human") and QWEN is the vibe coder, a cheap local
model Claude directs one bounded step at a time. Claude plans the smallest next step, hands it to
qwen via the `qwen-do` executor, then independently verifies qwen's transcript against a gate, and
runs a continuous-improvement loop: log what qwen got right and wrong, feed corrections back so
qwen's unaided hit-rate rises over time. Raising qwen makes Claude a sharper orchestrator too. That
improvement loop is the POINT of vibe-code, not a side effect.

This is the INVERSE of `vibe-plan` / `vibe-verify` (the sibling team's rename of claude-plan /
claude-verify), where qwen drives and shells out to Claude for the plan and the verdict. Here Claude
holds the wheel. Reference those two as the mirror helpers; do not build them in this skill.

## When to use

- There is real executable work a local model can type out: data prep, cleaning, scaffolding, dep
  installs, training/eval runs, smoke tests, mechanical refactors, anything deterministic with a
  clear pass check.
- You want parallelism: qwen types (free, local) while Claude spends its expensive tokens on
  judgment and verification.

## When NOT to use

- Pure conversation, planning, or analysis with no code to run.
- Trivial one-line edits Claude should just make itself (delegating costs more than doing it).
- Open-ended architecture or debugging where a small model loses the thread. Plan it yourself first,
  then hand qwen the bounded pieces.

## The loop

1. **Plan ONE smallest bounded step.** Pick the smallest step that proves something (prefer "write
   the fix plus a sub-30s test, run it, show output" over "do the whole feature"). Define up front:
   the step, the GATE that decides PASS, and the smoke-test the step must include. State the exact
   command line, the device, the batch size, the workers. Qwen does NOT reach for hardware on its
   own, so spell out "use the RTX 4090, device cuda, batch 256, num-workers 8" every time, and
   parallelize CPU work up to the available threads (12 on generic).
2. **Execute via qwen-do.** Give qwen the EXACT command line, not a description of intent (loose
   intent makes it improvise). ALWAYS pass the prompt with `qwen-do -f /tmp/step.txt`, NEVER
   interpolate a quote-heavy prompt into an ssh command line: inline quotes and `python -c "..."`
   break the outer shell and qwen never starts (the classic "loaded but nothing showing"). To ship a
   prompt or a quote-heavy file to a remote box, base64 it across:
   `base64 -w0 step.txt | ssh host 'base64 -d > /tmp/step.txt'`, then run qwen-do against the file.
3. **Verify independently from artifacts.** Never trust qwen's own PASS/BLOCK self-label or its exit
   code (it has mislabeled a clean run BLOCKED off a script status line). Re-derive the verdict from
   the artifacts the step produced. ALWAYS `git diff` to check qwen's "Files changed" claims, it
   over-claims edits it never wrote to disk. Read the "Surprises / deviations" line first, that is
   where a false pass hides.
4. **Smoke-test-first, always.** Prove the code on a tiny sample (a few hundred rows, or a
   hand-built micro example) with an explicit schema/row-shape assertion in under ~30s BEFORE any
   full-data or training run. A step that would run for minutes without a smoke test is a BLOCK. This
   is the single biggest rework-killer: parse and schema bugs caught on the tiny sample, not after a
   multi-minute run.
5. **Treat perfect metrics as RED FLAGS, not wins.** AUC=1.0, EER=0.0, F1=1.0, or a suddenly round
   huge count means investigate (self-matching eval, dropped class, leak), never celebrate.
6. **A missing input is a BLOCK, not a substitute-and-continue.** Never lower a gate, never quietly
   swap in a stand-in for a missing file. Stop and report exactly what is missing.

## qwen-do invocation reference

`qwen-do` (the executor this skill wraps) lives in stark-skills `skills/workflows/qwen-do` and is
installed on the executor box at `~/.local/bin/qwen-do`. It layers a fixed executor system prompt
(do-one-step-then-STOP, smoke-test-first, block-don't-substitute, distrust-perfect-metrics) and
writes a transcript to `./.qwen-runs/<stamp>.log` in the working repo.

| Flag / env | Meaning |
| --- | --- |
| `-f /tmp/step.txt` | Feed the prompt from a file. USE THIS for anything non-trivial or quote-heavy. |
| `--warm` | Carry conversation context across the steps of ONE task. Default is fresh (no carryover) to prevent executor drift. |
| `--resume <id>` | Resume a specific session id. |
| `QWEN_MODEL` | Model id the local server exposes (e.g. `qwen3.6-35b-a3b-mlx`). |
| `QWEN_BASE_URL` | OpenAI-compatible endpoint of the local model server (e.g. Mac LM Studio at `192.168.1.122:1234/v1`). |
| `QWEN_APPROVAL` | `auto` (default) \| `auto-edit` \| `yolo` \| `default` \| `plan`. |

Headless over ssh REQUIRES `QWEN_APPROVAL=yolo`. The default `auto` (and `auto-edit`) run an LLM
approval classifier that BLOCKS `run_shell_command` in non-interactive mode, so the executor cannot
run smoke tests, python, or nvidia-smi. Only `yolo` lets shell run unattended. The safety nets that
replace the classifier are the qwen-do executor system prompt (no destructive ops, no printing
secrets) plus Claude verifying every transcript before authorizing the next step. Set
`QWEN_CODE_SUPPRESS_YOLO_WARNING=1` to keep transcripts clean.

Canonical remote invocation:

```bash
base64 -w0 step.txt | ssh host 'base64 -d > /tmp/step.txt'
ssh host 'cd <repo> && QWEN_APPROVAL=yolo QWEN_MODEL=<model> QWEN_BASE_URL=<url> qwen-do -f /tmp/step.txt'
```

Expect a quiet gap with no session output at the start of any step that installs deps or downloads a
model: qwen-do does pip/model fetch first and silently. That is not a hang.

## When the model server goes down: restarting LM Studio

qwen connects to a remote model server (LM Studio on `max`, the Mac, at `192.168.1.122:1234`). If
that server sleeps, crashes, or goes unreachable, every qwen inference attempt fails with an API
body/connection timeout — the REPL appears to hang or the pane shows a timeout error. Signs:
- The tmux pane is frozen mid-step with "API body timeout" or similar
- `curl -s http://192.168.1.122:1234/v1/models` returns an error or times out

**Recovery steps (in order):**
1. Check if it is just sleeping: `ssh max 'pgrep -x "LM Studio"'` — if process exists it may just
   need a moment. Try a model ping first.
2. If not running or not responding, launch it:
   ```bash
   ssh max 'open -a "LM Studio"'
   ```
   Wait ~10s for it to fully start and reload the model (it auto-loads the last-used model).
3. Verify it is serving:
   ```bash
   ssh max 'curl -s http://127.0.0.1:1234/v1/models | head -c 200'
   ```
   Should return a JSON list with your model. If empty, open LM Studio's UI and manually start the
   server (the GUI toggle must be on).
4. After LM Studio is back: **send `/new` to the qwen tmux session** to clear any partial/broken
   context from the failed inference, then re-send the step prompt.

Note: `ssh max` reaches the Mac (hostname `max`, `192.168.1.122`). Never use `ssh 192.168.1.122`
directly — use the hostname alias. The `open -a "LM Studio"` command works headlessly over ssh.

## Preferred for a watched warm session: drive qwen in a tmux session over ssh

When you want a PERSISTENT warm qwen REPL that Lance can also watch live, run qwen in a `tmux`
session ON the executor box and drive it purely over ssh. This beats both other paths for an
interactive, observable run: it is warm (context carries across steps), persistent (survives ssh
disconnects and the watching machine sleeping), clean to read (plain `capture-pane`, none of the
AppleScript/TUI-redraw garbage or 30s write-timeouts of a screen-scraping terminal MCP), and
shareable (Lance attaches to the SAME session to watch). The tmux session and qwen both run on the
executor box, so any files qwen touches are there, exactly like the other paths.

Lifecycle and drive loop (NAME=p2, REPO and model/env are Lance's):
```bash
# start a detached session running the interactive qwen REPL (--yolo so shell tools run unattended)
ssh host 'tmux kill-session -t NAME 2>/dev/null; tmux new-session -d -s NAME -c REPO \
  "source .venv/bin/activate; export QWEN_MODEL=<model> QWEN_BASE_URL=<url> QWEN_CODE_SUPPRESS_YOLO_WARNING=1; qwen --yolo"'
ssh host 'tmux has-session -t NAME && echo ALIVE'         # confirm
# FIRE a step: ship the prompt to a file (quote-heavy), send it, then send Enter SEPARATELY
base64 -w0 step.txt | ssh host 'base64 -d > /tmp/step.txt'
ssh host 'tmux send-keys -t NAME "$(cat /tmp/step.txt)"; sleep 1; tmux send-keys -t NAME Enter'
# READ qwen's screen (clean) and scrollback for results
ssh host 'tmux capture-pane -t NAME -p'                   # current screen
ssh host 'tmux capture-pane -t NAME -p -S -150 | grep -iE "auc|done|error|<your marker>"'  # scrollback
ssh host 'tmux kill-session -t NAME'                      # when the task is done
```

Gotchas (all learned the hard way):
- **Send the text and Enter as TWO send-keys calls** (with a short sleep between). Combining them can
  race so the REPL submits a partial line.
- **Quote-heavy prompts: write to a file and `send-keys "$(cat file)"`**, never interpolate a prompt
  with inline quotes / `python -c "..."` straight into the ssh+tmux command line (same shell-quoting
  trap as the qwen-do `-f` rule).
- **VERIFY ON DISK, not from the pane.** The pane text is qwen's self-report; still `ls`/`git diff`/
  re-run the smoke on the executor box. qwen has claimed a file "not saved" when it WAS on disk, and
  vice versa.
- **Use `/new` to clear a stale qwen context.** After a failed or timed-out step (API timeout, LM
  Studio disconnect, mid-prompt `q` cancel), the REPL's internal conversation history can be
  corrupted or partially-written. Sending a new prompt into that state causes confusion or silent
  mis-execution. When in doubt: send `/new` to the session first to wipe the context, then re-send
  the prompt. Signs you need `/new`: the model seems to be continuing a prior train of thought,
  responds with partial output, or the pane shows a stray character (e.g. `q`) from a prior cancel.
  Cost: nothing — it is just a context reset.
  ```bash
  ssh host 'tmux send-keys -t NAME "/new" Enter'
  sleep 2   # let qwen acknowledge the reset
  # now re-send the real prompt
  ssh host 'tmux send-keys -t NAME "$(cat /tmp/step.txt)"; sleep 1; tmux send-keys -t NAME Enter'
  ```
- A terminal-control MCP that screen-scrapes a GUI terminal (e.g. iterm-mcp over AppleScript) is the
  WORSE tool for this: the app must be open, the TUI renders as garbage when read, long-inference
  writes time out at ~30s, and it dies if the machine sleeps. tmux-over-ssh has none of those. You do
  not need the GUI terminal at all to drive qwen; it only gives a human a window, and they can get
  that window by attaching to the same tmux session (`tmux attach -t NAME`).

## Optional: drive qwen through the hosted qwen-serve MCP (warm sessions)

`qwen-do` is the default and is battle-tested. The `qwen-serve` MCP is an OPTIONAL alternate executor
path that gives qwen a PERSISTENT warm session (context carried across steps) instead of a fresh
process per step, and removes the ssh + base64 file-ship dance. Use it when a task benefits from qwen
remembering the prior steps (multi-step refactors, iterative debugging) rather than fresh-per-step.

The MCP is hosted on the executor box and reachable remotely (for Lance's setup it runs as a systemd
service on `generic`, exposed tailnet-only over HTTPS via tailscale serve at
`https://generic.fin-snares.ts.net:8444/mcp`, registered in Claude Code user scope as `qwen-serve`).
The daemon and the qwen executor both run ON the executor box, so the `workspace` you pass is the
repo path THERE (e.g. `/home/generic/dev/ewitness-mcp`), and any files qwen touches are on that box,
exactly like the qwen-do path.

Tool flow (the MCP tools are `qwen_session_start`, `qwen_session_send`, `qwen_session_events`,
`qwen_session_end`):
1. `qwen_session_start({workspace, model})` once per task. Pass `model: "qwen3.6-35b-a3b-mlx"` (the
   pinned model). It ensures a daemon for that (workspace, model) pair and opens a session. The
   qwen-do executor system prompt is applied BY DEFAULT as `system_prompt_append` on the first send,
   so the do-one-step / smoke-test-first / block-don't-substitute discipline is preserved. Returns
   `session_id` + `base_url`; keep both.
2. `qwen_session_send({session_id, base_url, prompt})` per step. `prompt` is the SAME bounded step
   you would have put in `/tmp/step.txt` (exact command line, device/batch/workers, gate, smoke
   test, the STEP-PASS/BLOCKED report contract). Multimodal: pass `files: [abs_path, ...]` to attach
   images/PDFs (validated up front, never silently dropped). The call blocks until the turn ends and
   returns `{output, status, stop_reason, last_step_block, error}`.
3. `qwen_session_end({session_id, base_url})` when the task is done.

VERIFY THE SAME WAY regardless of path. The MCP's `last_step_block` and `output` are qwen's
SELF-REPORT, exactly as untrustworthy as the qwen-do transcript: still `git diff` its edit claims
(here over ssh to the executor box, or via a follow-up send that runs `git --no-pager diff` and
pastes it), still re-run the smoke test yourself, still read "Surprises / deviations" first. A killed
or timed-out send (`status` == "timeout"/"error") is NOT the same as failed work: check the disk on
the executor box before re-dispatching (qwen may have written correct files before the cutoff).

Pick the path per task, do not mix mid-task: if you start a warm MCP session, stay on it for that
task's steps so the context actually accumulates; if you use qwen-do, stay with qwen-do.

## The improvement loop (the point of vibe-code)

After every verified step, append to a running performance log three things:
1. What qwen got RIGHT unaided (so you can stop over-specifying it later).
2. What FAILED (the bug, the misread, the over-claim).
3. What prompt phrasing or guardrail FIXED it.

Periodically distil the recurring lessons into two durable places:
- **(a) Sharper default step-prompts** Claude writes: pre-correct the known failure modes so you
  stop re-typing them. Examples that already pay off: always give the exact command line; always
  state device plus batch plus workers; always demand smoke-test-first with a schema assertion;
  always demand a structured report with a paste of the exact stdout or file contents; frame
  analysis steps as "rule out hypotheses a/b/c/d" (that framing gets clean falsifiable answers).
- **(b) Durable edits to qwen's own environment**, not just Claude's prompts: the qwen-do executor
  system prompt (in stark-skills `skills/workflows/qwen-do`), and qwen's project context on the box
  (`~/.qwen` settings/rules, repo conventions). Examples to push qwen-side: "verify your own file
  changes with git diff before claiming them", and a project note about the available GPU and CPU
  threads so hardware use becomes the default rather than something prompted each time.

Measure improvement as: fewer corrections per step, fewer rework loops, and qwen catching its own
bugs (it has already self-caught a units bug and switched to a working installer unprompted). The
goal is to raise qwen's unaided hit-rate over time. For Lance's project the running log lives in
memory as `project_qwen_performance_log`; update it as new behavior surfaces.

## Trello board as the orchestrator's dashboard

Claude is acting as the human. Humans track work on a board. That means Claude MUST maintain a
Trello board for every vibe-code engagement — not as an afterthought, but as a live artifact that
Lance can open at any time and see exactly what's running, what passed, and what's next.

**At engagement start:** If no board exists, create one via the Trello MCP (`mcp__trello__create_board`,
`mcp__trello__create_list`). Standard lists: "Plan & Specs", "In Progress", "Blocked / Needs Lance",
"Done". Create cards for every known card/step before starting.

**During execution (after each verified PASS):**
- Move the card to "Done" (`mcp__trello__update_card` with `idList: <done-list-id>`)
- Update the card description with the actual result, key metric, and commit hash
- Move the NEXT card to "In Progress"

**On BLOCK:** Move the card to "Blocked / Needs Lance" with a comment explaining exactly what is
missing. Do not proceed past a block.

**The board URL belongs in `continue.md`** so any future session can find it without asking.

This is not optional. If Claude is the orchestrator, the board is the orchestrator's external memory
that Lance can watch in real time — the same way a human tech lead keeps a sprint board live while
the team works. A board that lags by multiple cards is a board that has failed its purpose.

## Keep qwen fed (it is queueable)

There is one model server, so jobs run one at a time, but extra requests QUEUE rather than error
(worst case they wait). Operational rule: whenever Claude is about to do its own work or wait on
something, first hand qwen the next mechanical or verifiable step. Treat qwen as a background worker
with a queue, not a one-at-a-time tool to babysit. Good queue candidates: dep installs, data
prep/cleaning, file scaffolding, smoke tests, anything deterministic with a clear pass check.

## Trust mode: give qwen INTENT + CONTRACT + GATE, not code (the autonomy goal)

The strongest version of vibe-code does NOT hand qwen the function body. Pre-writing near-complete
code in the step prompt is cheating: it inflates qwen's apparent hit-rate and defeats the point,
which is real local-model autonomy. Instead, each step prompt states:

- **Intent** — what the thing must DO, in plain terms, and why it exists.
- **Contract** — the interface other code depends on (exact export signatures, request/response
  shapes, the validator/schema it must satisfy). This is the part you ARE precise about.
- **Gate** — how you will verify (tests, `node --check`, a live end-to-end you run yourself).
- **Constraints** — the non-negotiables (language/runtime, reuse-this-helper, no new deps, the XSS
  rule, house style), and an explicit invitation to research or import a skill if it helps.

Then STOP. Let qwen design the implementation. **Let it fail.** When your verification finds a
defect, the diagnosis is the orchestrator's job (root-cause it precisely, e.g. sample a flaky API
5x to quantify a failure rate), but the code change is qwen's: hand back a SURGICAL correction step
(exact find→replace pairs or a tight defect description + gate), never patch the code yourself and
never pre-write code to dodge the failure. Measured payoff seen in practice: contract-only prompts
produced equally-correct results with far less of Claude coding through qwen's fingers, AND qwen
self-improved unprompted (noticed its own smoke test was landing INCOMPLETE and rewrote the test to
send realistic inputs rather than fake a pass). That self-correction is the signal you are doing it
right. The exception that proves the rule: for a risky EXTERNAL bit (a raw third-party API call),
smoke-test it YOURSELF first, then hand qwen the proven request shape verbatim — de-risking an
integration is not the same as spoon-feeding business logic.

## You are the human: stop a spinning run, do not babysit it

Claude holds the wheel, which includes the brakes. When a qwen run is grinding uselessly (a verify
loop you already have the answer from, a wrong path, a hang), STOP it — do not wait out a multi-minute
timeout. You can send control codes to the tmux session:

- `tmux send-keys -t NAME Escape` — cancel the current inference (qwen returns to its prompt).
- `tmux send-keys -t NAME C-c` — interrupt; `tmux send-keys -t NAME C-u` — clear a half-typed/stray
  input line (a leaked keystroke on the prompt will corrupt the next turn — clear it).
- `tmux send-keys -t NAME "/new" Enter` — wipe stale/corrupted context after a cancel or timeout.
- `tmux kill-session -t NAME` — nuke it entirely and restart fresh.

Corollary: do NOT run your own copy of a script concurrently with qwen's run. One model server means
requests serialize; two runs of the same thing just tangle and slow each other. Let the executor own
its deliverable; you verify the artifact after.

## Verification is qwen's job too — get the tool to do it

Resist hand-rolling verification in your own shell (curl/python E2E loops, ad-hoc smoke drivers).
That is executable work a local model should type — hand qwen a "write a smoke script, run it against
the live target, report PASS/INCOMPLETE/FAIL honestly" step. Two concrete reasons beyond principle:
(1) a hand-built JSON payload that interpolates model-returned text breaks on newlines/quotes
("Invalid control character") — qwen's `JSON.stringify` body avoids it; (2) an honest script that
asserts shapes and only prints PASS on a real success is more trustworthy than your eyeballing curl
output. You still VERIFY the artifact (read the script, re-run it once alone), but you do not author
it. And remember the thing under test may already be proven by an earlier step — do not rabbit-hole
chasing a literal terminal state ("shipped", "PASS") when the underlying behavior is already
confirmed; a documented INCOMPLETE/expected-reinforce can be the correct, honest outcome.

## Reading the tmux pane: idle-detection and verification gotchas

These cost real time until learned:

- **The spinner wraps two lines.** A narrow `capture-pane -S -6` window can miss the "esc to cancel"
  spinner text and falsely read "idle". Detect idle by the ABSENCE of "esc to cancel"/"cancel" in a
  WIDE window (`capture-pane -S -15` or more), not by pane-equality.
- **Pane-equality stability is a false-positive trap.** qwen pauses to "think" mid-file-write, so two
  identical captures do not mean done. Gate on spinner-absence; if you must use equality, require 3+
  consecutive identical reads AND no spinner.
- **Keep the step.txt ASCII-only.** Box-drawing (`─`) and arrow (`→`) characters in the prompt body
  make `tmux send-keys "$(cat step.txt)"` spit "not in a mode" and silently DROP the text — the send
  fails and qwen never starts. Write prompts in plain ASCII.
- **Count forbidden punctuation with python, not shell grep.** `grep -c '—'` mis-handles multibyte
  chars (quoting swallows the pattern → false 0). Use
  `python3 -c "t=open(F).read(); print(t.count(chr(0x2014)), t.count(chr(0x2013)), t.count(chr(0x2192)))"`
  to truly verify em-dash / en-dash / arrow == 0 in artifacts.
- **Read the line before trusting a grep hit.** A safety grep (`innerHTML`, etc.) can match a comment,
  not a real defect; for XSS-safety specifically, READ the render functions (every model-data field
  goes through createElement+textContent), do not just count.
- **Background servers from the Bash tool get reaped** (exit 144) when the call returns. Run any
  persistent server in its OWN tmux session so it survives. Verify against it over the tailnet, not
  via a screen-scraping browser MCP that cannot see this box's loopback.

## vibe-code vs vibe-plan / vibe-verify

| | orchestrates / executes | plans plus verifies |
| --- | --- | --- |
| **vibe-code** | qwen (local, cheap) | Claude (drives) |
| **vibe-plan / vibe-verify** | qwen (local) or you | Claude (read-only, called on demand) |

Same plan/do/verify loop, opposite caller. Use vibe-code when Claude is driving and wants a local
model to type. Use vibe-plan / vibe-verify when a local model is driving and wants frontier judgment
on tap.
