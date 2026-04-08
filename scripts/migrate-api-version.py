"""
Google Ads Plugin — API Version Migration Helper
Run this when upgrading to a new Google Ads API version.
Updates the version reference in config and checks for breaking changes.
"""

import re
import sys
import os
import subprocess

# Update these when a new API version is released
CURRENT_VERSION = "v23"
NEXT_VERSION = "v24"  # Update when migrating

FILES_TO_UPDATE = [
    "references/api-reference.md",
    "mcp-config/google-ads-server.json",
    "CLAUDE.md",
]


def check_adloop_version():
    """Check if AdLoop supports the target API version."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "adloop"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("AdLoop not installed. Run scripts/setup-auth.py first.")


def find_version_references(target_version):
    """Find all files referencing a specific API version."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches = []

    for root, dirs, files in os.walk(project_root):
        # Skip hidden dirs and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for fname in files:
            if fname.endswith(('.md', '.json', '.py', '.yaml', '.yml')):
                fpath = os.path.join(root, fname)
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if target_version in content:
                    count = content.count(target_version)
                    matches.append((fpath, count))

    return matches


def update_version_in_file(filepath, old_version, new_version):
    """Replace version string in a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    updated = content.replace(old_version, new_version)
    count = content.count(old_version)

    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        print(f"  Updated {count} reference(s) in {os.path.basename(filepath)}")
    return count


def print_migration_checklist(old_version, new_version):
    print(f"""
Migration Checklist: {old_version} → {new_version}
{'=' * 50}

Before migrating:
  [ ] Check Google Ads API release notes for {new_version}
      https://developers.google.com/google-ads/api/docs/release-notes
  [ ] Check AdLoop changelog for {new_version} support
      https://github.com/kLOsk/adloop/releases
  [ ] Run: pip install adloop --upgrade
  [ ] Test against test account first (never live first)

Breaking change areas to check:
  [ ] GAQL field names (some are renamed each version)
  [ ] Removed services or methods
  [ ] New required fields on existing mutations
  [ ] Enum value changes

After updating:
  [ ] Run scripts/test-connection.py
  [ ] Run a read-only monitoring pass (get_campaign_performance)
  [ ] Verify all GAQL queries in references/gaql-cheatsheet.md still work
  [ ] Update CURRENT_VERSION in this script
""")


def main():
    print("Google Ads Plugin — API Version Migration Helper")
    print("=" * 50)

    if len(sys.argv) < 2:
        print(f"Current tracked version: {CURRENT_VERSION}")
        print(f"\nUsage: python migrate-api-version.py [scan|migrate]")
        print(f"  scan    — find all {CURRENT_VERSION} references in project files")
        print(f"  migrate — update {CURRENT_VERSION} → {NEXT_VERSION} across project files")
        print_migration_checklist(CURRENT_VERSION, NEXT_VERSION)
        return

    command = sys.argv[1]

    if command == "scan":
        print(f"\nScanning for {CURRENT_VERSION} references...")
        matches = find_version_references(CURRENT_VERSION)
        if matches:
            print(f"\nFound {CURRENT_VERSION} in {len(matches)} file(s):")
            for fpath, count in matches:
                print(f"  {fpath} ({count} occurrence{'s' if count > 1 else ''})")
        else:
            print(f"No references to {CURRENT_VERSION} found.")

        print(f"\nAlso checking AdLoop installation:")
        check_adloop_version()

    elif command == "migrate":
        old = sys.argv[2] if len(sys.argv) > 2 else CURRENT_VERSION
        new = sys.argv[3] if len(sys.argv) > 3 else NEXT_VERSION

        print(f"\nMigrating references: {old} → {new}")
        confirm = input(f"This will update files in place. Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return

        matches = find_version_references(old)
        total = 0
        for fpath, _ in matches:
            total += update_version_in_file(fpath, old, new)

        print(f"\nDone. Updated {total} reference(s) across {len(matches)} file(s).")
        print(f"Don't forget to update CURRENT_VERSION in this script to {new}.")
        print_migration_checklist(old, new)

    else:
        print(f"Unknown command: {command}. Use 'scan' or 'migrate'.")


if __name__ == "__main__":
    main()
