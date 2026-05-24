#!/usr/bin/env python3
"""
Bootstrap file condenser - keeps SOUL.md and AGENTS.md under 20KB
while preserving 100% fidelity of critical content.
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Tuple, List

# Size limit in bytes
SIZE_LIMIT = 20000

# Critical patterns that MUST be preserved exactly
CRITICAL_PATTERNS = [
    r'```[^\n]*\n[^`]+```',  # Code blocks
    r'mcporter call [^\n]+',  # MCP commands
    r'message action=[^\n]+',  # Message tool commands
    r'cron[^\n]+',  # Cron commands
    r'browser[^\n]+',  # Browser commands
    r'contexts/[^\s]+',  # File paths
    r'skills/[^\s]+',  # Skill paths
    r'NON-NEGOTIABLE',  # Critical rules marker
    r'MANDATORY',  # Mandatory rules marker
    r'CRITICAL',  # Critical marker
    r'Origin: [^\n]+',  # Origin dates
]


def get_file_size(filepath: Path) -> int:
    """Get file size in bytes."""
    return filepath.stat().st_size


def check_critical_content(original: str, condensed: str) -> Tuple[bool, List[str]]:
    """
    Verify that all critical patterns from original appear in condensed.
    Returns (is_valid, missing_patterns).
    """
    missing = []
    
    for pattern in CRITICAL_PATTERNS:
        original_matches = set(re.findall(pattern, original, re.MULTILINE | re.DOTALL))
        condensed_matches = set(re.findall(pattern, condensed, re.MULTILINE | re.DOTALL))
        
        if original_matches != condensed_matches:
            missing.append(f"Pattern '{pattern}' changed")
    
    return len(missing) == 0, missing


def condense_content(content: str) -> str:
    """
    Apply intelligent condensing patterns while preserving critical content.
    """
    # Store code blocks to protect them
    code_blocks = {}
    def save_code_block(match):
        key = f"__CODE_BLOCK_{len(code_blocks)}__"
        code_blocks[key] = match.group(0)
        return key
    
    content = re.sub(r'```[^\n]*\n[^`]+```', save_code_block, content, flags=re.DOTALL)
    
    # 1. Remove multiple blank lines → single blank line
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 2. Remove trailing whitespace
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    
    # 3. Condense verbose phrases
    replacements = [
        (r'\*\*When Lance says:\*\*\n', '**When Lance says:**\n'),
        (r'\*\*When to use:\*\*', '**When:**'),
        (r'\*\*When to ([^:]+):\*\*', r'**\1 when:**'),
        (r'This is the', ''),
        (r'You should', ''),
        (r'It is important to', ''),
        (r'Make sure to', ''),
        (r'Be sure to', ''),
        (r'In order to', 'To'),
        (r'In this case', ''),
        (r'At this point', 'Now'),
        (r'It should be noted that', ''),
        (r'Please note that', ''),
        (r'Keep in mind that', ''),
        (r'Remember that', ''),
        (r'For example,', 'Example:'),
        (r'As an example,', 'Example:'),
        (r'\(for example\)', '(e.g.)'),
        (r'and so on', 'etc.'),
        (r'etc\.\.\. ', 'etc. '),
        (r'The following', 'These'),
        (r'As follows:', ':'),
        (r'You can use', 'Use'),
        (r'You must', 'Must'),
        (r'You should', 'Should'),
        (r'It will', 'Will'),
        (r'This will', 'Will'),
        (r'That will', 'Will'),
        (r' — that is,', ' —'),
        (r' — in other words,', ' —'),
        (r'In other words,', ''),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # 4. Condense repeated section markers
    content = re.sub(r'(#+\s+[^\n]+\s+)\((MANDATORY|NON-NEGOTIABLE|CRITICAL)\)', r'\1\2', content)
    
    # 5. Condense bash command examples (keep first line of multi-line)
    # Skip if it's in a code block (already protected)
    
    # 6. Remove duplicate blank lines that may have been created
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Restore code blocks
    for key, block in code_blocks.items():
        content = content.replace(key, block)
    
    return content


def process_file(filepath: Path, dry_run: bool = False) -> Tuple[int, int, bool]:
    """
    Process a bootstrap file. Returns (original_size, new_size, success).
    """
    print(f"\n{'='*60}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*60}")
    
    # Read original
    original = filepath.read_text()
    original_size = len(original.encode('utf-8'))
    
    print(f"Original size: {original_size:,} bytes")
    
    if original_size <= SIZE_LIMIT:
        print(f"✓ Already under {SIZE_LIMIT:,} byte limit")
        return original_size, original_size, True
    
    # Condense
    condensed = condense_content(original)
    new_size = len(condensed.encode('utf-8'))
    
    saved = original_size - new_size
    percent = (saved / original_size) * 100
    
    print(f"Condensed size: {new_size:,} bytes")
    print(f"Saved: {saved:,} bytes ({percent:.1f}%)")
    
    # Verify critical content preserved
    is_valid, missing = check_critical_content(original, condensed)
    
    if not is_valid:
        print("\n❌ VERIFICATION FAILED - Critical content lost:")
        for item in missing:
            print(f"  - {item}")
        return original_size, new_size, False
    
    print("\n✓ Verification passed - all critical content preserved")
    
    if new_size > SIZE_LIMIT:
        print(f"\n⚠️  Still over limit by {new_size - SIZE_LIMIT:,} bytes")
        print("   Manual review needed for further condensing")
    else:
        print(f"\n✓ Now under {SIZE_LIMIT:,} byte limit")
    
    # Write if not dry-run
    if not dry_run:
        if is_valid:
            filepath.write_text(condensed)
            print(f"\n✓ Saved to {filepath}")
        else:
            print(f"\n✗ Not saved due to verification failure")
    else:
        print("\n(Dry run - no changes written)")
    
    return original_size, new_size, is_valid


def main():
    parser = argparse.ArgumentParser(description='Condense bootstrap files')
    parser.add_argument('--check', action='store_true', help='Only check sizes')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
    parser.add_argument('--file', help='Process specific file (SOUL.md or AGENTS.md)')
    
    args = parser.parse_args()
    
    # Determine workspace root
    workspace = Path.cwd()
    if not (workspace / 'SOUL.md').exists():
        # Try parent directories
        for parent in workspace.parents:
            if (parent / 'SOUL.md').exists():
                workspace = parent
                break
        else:
            print("Error: Could not find SOUL.md in current or parent directories")
            sys.exit(1)
    
    # Determine files to process
    if args.file:
        files = [workspace / args.file]
        if not files[0].exists():
            print(f"Error: {args.file} not found at {files[0]}")
            sys.exit(1)
    else:
        files = [workspace / 'SOUL.md', workspace / 'AGENTS.md']
    
    # Check mode
    if args.check:
        print("\nBootstrap File Sizes")
        print("="*60)
        for filepath in files:
            if filepath.exists():
                size = get_file_size(filepath)
                status = "✓" if size <= SIZE_LIMIT else "⚠️"
                print(f"{status} {filepath.name}: {size:,} bytes ({size/1024:.1f} KB)")
                if size > SIZE_LIMIT:
                    print(f"   Over limit by {size - SIZE_LIMIT:,} bytes")
        return
    
    # Process files
    results = []
    for filepath in files:
        if filepath.exists():
            results.append(process_file(filepath, dry_run=args.dry_run))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    total_saved = sum(r[0] - r[1] for r in results)
    all_valid = all(r[2] for r in results)
    
    print(f"Total saved: {total_saved:,} bytes")
    print(f"Verification: {'✓ All passed' if all_valid else '✗ Some failed'}")
    
    if not args.dry_run and all_valid:
        print("\n✓ All files processed successfully")
    elif args.dry_run:
        print("\n(Dry run complete - run without --dry-run to save changes)")


if __name__ == '__main__':
    main()
