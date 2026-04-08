"""
Google Ads Plugin — Connection Test
Verifies AdLoop can reach the Google Ads API and returns basic account info.
"""

import subprocess
import sys
import json


def check_adloop_installed():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "adloop", "--version"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def run_health_check():
    """Call the adloop health_check tool via CLI."""
    print("Running AdLoop health check...")
    result = subprocess.run(
        [sys.executable, "-m", "adloop", "check"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("Health check output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
    return result.returncode == 0


def check_config_exists():
    import os
    config_path = os.path.expanduser("~/.adloop/config.yaml")
    if os.path.exists(config_path):
        print(f"Config found: {config_path} — OK")
        return True
    else:
        print(f"ERROR: Config not found at {config_path}")
        print("Run scripts/setup-auth.py first.")
        return False


def check_token_exists():
    import os
    token_path = os.path.expanduser("~/.adloop/token.json")
    if os.path.exists(token_path):
        print(f"OAuth token found: {token_path} — OK")
        return True
    else:
        print(f"WARNING: OAuth token not found at {token_path}")
        print("You may need to re-authenticate. Run: adloop init")
        return False


if __name__ == "__main__":
    print("Google Ads Plugin — Connection Test")
    print("=" * 50)

    if not check_adloop_installed():
        print("ERROR: AdLoop not installed. Run scripts/setup-auth.py first.")
        sys.exit(1)
    else:
        print("AdLoop installed — OK")

    config_ok = check_config_exists()
    token_ok = check_token_exists()

    if not config_ok:
        sys.exit(1)

    print()
    success = run_health_check()

    if success:
        print("\nAll checks passed. Ready to use Google Ads tools.")
    else:
        print("\nSome checks failed. Review errors above.")
        print("Common fixes:")
        print("  - Re-run setup:  python scripts/setup-auth.py")
        print("  - Re-auth only:  adloop init")
        print("  - Check token:   cat ~/.adloop/config.yaml")
