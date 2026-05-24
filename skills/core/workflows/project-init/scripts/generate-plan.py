#!/usr/bin/env python3
"""
generate-plan.py — Project planning script for project-init skill.

Takes a project directive and outputs a structured JSON plan with:
- Project metadata (name, description, definition of done)
- Phased ticket breakdown with model assignments
- Notion page content (markdown)

Usage:
  python3 generate-plan.py --directive "Migrate TinyDB to Firestore" [--channel-id 123] [--context "..."]
  python3 generate-plan.py --dry-run  # Test with sample directive

The script uses Claude API (via subprocess calling mcporter or direct API)
to analyze the directive and produce the plan. Falls back to a template-based
approach if the API is unavailable.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

# ── Model selection rubric ──────────────────────────────────────────────

MODEL_RUBRIC = {
    "simple": {
        "model": "sonnet-low",
        "account": "unit-low",
        "signals": [
            "single file change",
            "docs/README only",
            "config/env changes",
            "formatting/linting",
            "copy edits",
            "<20 lines changed",
        ],
    },
    "standard": {
        "model": "sonnet-medium",
        "account": "unit-medium",
        "signals": [
            "1-3 files changed",
            "new endpoint/function (existing patterns)",
            "adding tests",
            "API integration (known pattern)",
            "schema additions",
        ],
    },
    "complex": {
        "model": "sonnet-high",
        "account": "unit-high",
        "signals": [
            "4+ files changed",
            "modifying architecture",
            "database migration",
            "multi-step refactor",
            "frontend + backend",
            "rollback concerns",
        ],
    },
    "deep": {
        "model": "opus-high",
        "account": "max-high",
        "signals": [
            "architectural decisions",
            "security-critical",
            "cross-service coordination",
            "performance-critical",
            "novel problem",
            "trade-off analysis",
        ],
    },
    "max": {
        "model": "opus-high",
        "account": "max-high",
        "signals": [
            "subsystem replacement",
            "cross-system migration",
            "10+ files with dependencies",
            "critical path (errors costly)",
            "novel protocol/system design",
        ],
    },
}

# ── Planning prompt ─────────────────────────────────────────────────────

PLANNING_PROMPT = """You are a senior engineering lead planning a project.

Given the following project directive, break it down into a structured plan.

## Directive
{directive}

## Existing Context
{context}

## Instructions

1. Identify the project name and write a clear description.
2. Define a concrete "Definition of Done" (3-5 bullet points).
3. Break the work into phases (1-4 phases typically).
4. For each phase, define tickets with:
   - A short title
   - A 2-3 sentence description of what the ticket accomplishes
   - Numbered implementation steps (3-8 steps)
   - Verification criteria (how to prove it's done)
   - Complexity assessment: simple | standard | complex | deep | max
   - Priority: urgent | high | normal | low
   - Key files likely touched

5. Assign models based on complexity:
   - simple → sonnet-low (docs, config, simple scripts)
   - standard → sonnet-medium (most coding, API changes)
   - complex → sonnet-high (multi-file refactors, migrations)
   - deep → opus-high (architecture, security, planning)
   - max → opus-high with explicit thinking (cross-system, critical path)

6. Be cost-conscious: default to the lowest sufficient model. A typical 10-ticket project
   should be roughly 40% simple/standard, 40% standard/complex, 20% complex/deep.

## Output Format

Return ONLY valid JSON (no markdown fencing, no explanation) in this exact structure:

{{
  "project_name": "...",
  "description": "...",
  "definition_of_done": ["...", "..."],
  "phases": [
    {{
      "name": "Phase 1: ...",
      "tickets": [
        {{
          "id": "T-001",
          "title": "...",
          "description": "...",
          "steps": ["1. ...", "2. ..."],
          "verification": ["...", "..."],
          "model": "sonnet-medium",
          "priority": "high",
          "complexity": "standard",
          "key_files": ["src/...", "tests/..."]
        }}
      ]
    }}
  ]
}}
"""


def generate_plan_via_mcporter(directive: str, context: str = "") -> dict | None:
    """Use mcporter to call an LLM for plan generation."""
    prompt = PLANNING_PROMPT.format(
        directive=directive, context=context or "No prior context found."
    )

    # Try using claude CLI directly (stripped env to avoid API key conflicts)
    try:
        env = {
            "HOME": os.environ.get("HOME", "/home/generic"),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        }
        oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        if oauth_token:
            env["CLAUDE_CODE_OAUTH_TOKEN"] = oauth_token

        result = subprocess.run(
            [
                "claude",
                "--dangerously-skip-permissions",
                "-p",
                prompt,
                "--output-format",
                "text",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            # Strip markdown code fencing if present
            if output.startswith("```"):
                lines = output.split("\n")
                # Remove first and last lines if they're fencing
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                output = "\n".join(lines)
            return json.loads(output)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Claude CLI failed: {e}", file=sys.stderr)

    return None


def generate_plan_template(directive: str) -> dict:
    """Fallback: generate a template plan from the directive text."""
    # Extract a project name from the first phrase
    name = directive.split(".")[0].split(",")[0].strip()
    if len(name) > 60:
        name = name[:60] + "..."

    today = datetime.now().strftime("%Y-%m-%d")

    return {
        "project_name": name,
        "description": directive,
        "definition_of_done": [
            "All tasks completed and verified",
            "Tests passing",
            "Documentation updated",
            "Deployed to staging/production as applicable",
        ],
        "phases": [
            {
                "name": "Phase 1: Setup & Planning",
                "tickets": [
                    {
                        "id": "T-001",
                        "title": "Project setup and environment",
                        "description": f"Set up the project environment and dependencies for: {name}",
                        "steps": [
                            "1. Review existing codebase and dependencies",
                            "2. Set up development environment",
                            "3. Create initial configuration",
                        ],
                        "verification": [
                            "Environment runs without errors",
                            "All dependencies installed",
                        ],
                        "model": "sonnet-low",
                        "priority": "high",
                        "complexity": "simple",
                        "key_files": [],
                    }
                ],
            },
            {
                "name": "Phase 2: Implementation",
                "tickets": [
                    {
                        "id": "T-002",
                        "title": "Core implementation",
                        "description": f"Implement the core functionality for: {name}. "
                        "Break this ticket down further once requirements are clearer.",
                        "steps": [
                            "1. Implement core logic",
                            "2. Add error handling",
                            "3. Write tests",
                        ],
                        "verification": [
                            "Core functionality works as specified",
                            "Tests passing",
                        ],
                        "model": "sonnet-medium",
                        "priority": "high",
                        "complexity": "standard",
                        "key_files": [],
                    }
                ],
            },
            {
                "name": "Phase 3: Verification & Cleanup",
                "tickets": [
                    {
                        "id": "T-003",
                        "title": "Testing and documentation",
                        "description": "Final testing, documentation, and cleanup.",
                        "steps": [
                            "1. Run full test suite",
                            "2. Update documentation",
                            "3. Clean up temporary files and debug code",
                        ],
                        "verification": [
                            "All tests pass",
                            "Docs are current",
                            "No debug artifacts",
                        ],
                        "model": "sonnet-low",
                        "priority": "normal",
                        "complexity": "simple",
                        "key_files": [],
                    }
                ],
            },
        ],
        "_generated": today,
        "_method": "template_fallback",
    }


def add_notion_content(plan: dict) -> dict:
    """Add formatted Notion page markdown to the plan."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# {plan['project_name']}",
        "",
        f"> **Status:** Active · **Created:** {today}",
        "",
        "---",
        "",
        "## Overview",
        "",
        plan.get("description", ""),
        "",
        "## Definition of Done",
        "",
    ]

    for item in plan.get("definition_of_done", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Ticket Overview", ""])
    lines.append("| # | Title | Model | Priority | Status |")
    lines.append("|---|-------|-------|----------|--------|")

    for phase in plan.get("phases", []):
        for ticket in phase.get("tickets", []):
            tid = ticket.get("id", "?")
            title = ticket.get("title", "?")
            model = ticket.get("model", "?")
            priority = ticket.get("priority", "?")
            lines.append(f"| {tid} | {title} | {model} | {priority} | Todo |")

    lines.extend(["", "## Phases", ""])

    for phase in plan.get("phases", []):
        lines.append(f"### {phase['name']}")
        for ticket in phase.get("tickets", []):
            lines.append(
                f"- **{ticket['id']}:** {ticket['title']} — {ticket.get('description', '')[:80]}"
            )
        lines.append("")

    plan["notion_content"] = "\n".join(lines)
    return plan


def validate_plan(plan: dict) -> list[str]:
    """Validate plan structure and return any issues."""
    issues = []

    if not plan.get("project_name"):
        issues.append("Missing project_name")
    if not plan.get("phases"):
        issues.append("Missing phases")
    if not plan.get("definition_of_done"):
        issues.append("Missing definition_of_done")

    valid_models = {"sonnet-low", "sonnet-medium", "sonnet-high", "opus-high"}
    valid_priorities = {"urgent", "high", "normal", "low"}
    valid_complexities = {"simple", "standard", "complex", "deep", "max"}

    ticket_ids = set()
    for phase in plan.get("phases", []):
        if not phase.get("name"):
            issues.append("Phase missing name")
        for ticket in phase.get("tickets", []):
            tid = ticket.get("id")
            if not tid:
                issues.append("Ticket missing id")
            elif tid in ticket_ids:
                issues.append(f"Duplicate ticket id: {tid}")
            ticket_ids.add(tid)

            if not ticket.get("title"):
                issues.append(f"{tid}: missing title")
            if ticket.get("model") not in valid_models:
                issues.append(
                    f"{tid}: invalid model '{ticket.get('model')}' — must be one of {valid_models}"
                )
            if ticket.get("priority") not in valid_priorities:
                issues.append(
                    f"{tid}: invalid priority '{ticket.get('priority')}' — must be one of {valid_priorities}"
                )
            if ticket.get("complexity") not in valid_complexities:
                issues.append(
                    f"{tid}: invalid complexity '{ticket.get('complexity')}' — must be one of {valid_complexities}"
                )

    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured project plan from a directive."
    )
    parser.add_argument(
        "--directive", type=str, help="Project directive text", default=""
    )
    parser.add_argument(
        "--channel-id", type=str, help="Discord channel ID", default=""
    )
    parser.add_argument(
        "--context",
        type=str,
        help="Existing context from haivemind",
        default="",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run with a sample directive for testing",
    )
    parser.add_argument(
        "--template-only",
        action="store_true",
        help="Skip LLM, use template fallback only",
    )
    parser.add_argument(
        "--validate-only",
        type=str,
        help="Validate an existing plan JSON file",
        default="",
    )

    args = parser.parse_args()

    # Validate-only mode
    if args.validate_only:
        with open(args.validate_only) as f:
            plan = json.load(f)
        issues = validate_plan(plan)
        if issues:
            print(f"Validation failed ({len(issues)} issues):", file=sys.stderr)
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)
            sys.exit(1)
        else:
            print("Plan is valid.", file=sys.stderr)
            sys.exit(0)

    # Dry-run mode
    if args.dry_run:
        directive = (
            "Migrate all TinyDB-based persistence in the tokens service to Firestore. "
            "This includes user tokens, session data, and refresh token storage. "
            "Must maintain backward compatibility during migration. "
            "Related ticket: ENG-682."
        )
        context = "Previous work: ENG-680 set up Firestore client library."
    else:
        directive = args.directive
        context = args.context

    if not directive:
        print("Error: --directive is required (or use --dry-run)", file=sys.stderr)
        sys.exit(1)

    # Generate plan
    plan = None
    if not args.template_only:
        print("Generating plan via LLM...", file=sys.stderr)
        plan = generate_plan_via_mcporter(directive, context)

    if plan is None:
        print("Using template fallback...", file=sys.stderr)
        plan = generate_plan_template(directive)

    # Validate
    issues = validate_plan(plan)
    if issues:
        print(f"Warning: plan has {len(issues)} validation issues:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)

    # Add Notion content
    plan = add_notion_content(plan)

    # Add metadata
    plan["_channel_id"] = args.channel_id
    plan["_generated_at"] = datetime.now().isoformat()

    # Output
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
