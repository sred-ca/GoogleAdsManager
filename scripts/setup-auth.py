"""
Google Ads Plugin — Auth Setup
Installs AdLoop and runs the interactive setup wizard.
"""

import subprocess
import sys
import shutil


def check_python_version():
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ required. You have {sys.version}")
        print("Download Python 3.11+ from https://python.org")
        sys.exit(1)
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} — OK")


def install_adloop():
    print("\nInstalling AdLoop...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "adloop", "--upgrade"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("ERROR: Failed to install AdLoop:")
        print(result.stderr)
        sys.exit(1)
    print("AdLoop installed — OK")


def check_adloop_installed():
    return shutil.which("adloop") is not None


def run_adloop_init():
    print("\nStarting AdLoop setup wizard...")
    print("-" * 50)
    print("You will need:")
    print("  1. Your Google Ads Developer Token")
    print("     (Google Ads > Tools > API Center)")
    print("  2. Your Google Ads Customer ID (10 digits, no dashes)")
    print("  3. A Google account login with access to the Ads account")
    print("-" * 50)
    input("\nPress Enter to continue...")

    result = subprocess.run(["adloop", "init"])
    if result.returncode != 0:
        print("\nSetup wizard encountered an error.")
        print("Try running manually: adloop init")
        sys.exit(1)


def print_next_steps():
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("  1. Run scripts/test-connection.py to verify connectivity")
    print("  2. Add the MCP server to Claude Code:")
    print("     claude mcp add --transport stdio adloop -- python -m adloop")
    print("\nConfig stored at: ~/.adloop/config.yaml")
    print("Audit log at:     ~/.adloop/audit.log")


if __name__ == "__main__":
    print("Google Ads Plugin — Auth Setup")
    print("=" * 50)
    check_python_version()
    install_adloop()
    run_adloop_init()
    print_next_steps()
