#!/usr/bin/env python3
"""
Version management script for idflow package.
"""

import re
import sys
from pathlib import Path
import argparse

def get_version():
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)

    content = pyproject_path.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        print("Error: version not found in pyproject.toml")
        sys.exit(1)

    return match.group(1)

def set_version(new_version):
    """Set new version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Replace version line
    new_content = re.sub(
        r'^version = "[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )

    if new_content == content:
        print(f"Error: Could not update version to {new_version}")
        sys.exit(1)

    pyproject_path.write_text(new_content)
    print(f"Version updated to {new_version}")

def bump_version(part="patch"):
    """Bump version by part (major, minor, patch)."""
    current_version = get_version()
    parts = current_version.split(".")

    if len(parts) != 3:
        print(f"Error: Invalid version format: {current_version}")
        sys.exit(1)

    try:
        major, minor, patch = map(int, parts)
    except ValueError:
        print(f"Error: Invalid version format: {current_version}")
        sys.exit(1)

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        print(f"Error: Invalid part '{part}'. Use major, minor, or patch")
        sys.exit(1)

    new_version = f"{major}.{minor}.{patch}"
    set_version(new_version)
    return new_version

def check_version_change():
    """Check if version changed between commits (for CI)."""
    import subprocess

    try:
        # Get current version
        current_version = get_version()

        # Get previous version
        result = subprocess.run(
            ["git", "show", "HEAD~1:pyproject.toml"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("Error: Could not get previous version")
            sys.exit(1)

        previous_content = result.stdout
        match = re.search(r'^version = "([^"]+)"', previous_content, re.MULTILINE)
        if not match:
            print("Error: Previous version not found")
            sys.exit(1)

        previous_version = match.group(1)

        if current_version != previous_version:
            print(f"Version changed: {previous_version} → {current_version}")
            print(f"version_changed=true")
            print(f"current_version={current_version}")
            print(f"previous_version={previous_version}")
        else:
            print(f"Version unchanged: {current_version}")
            print(f"version_changed=false")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Version management for idflow")
    parser.add_argument("--get", action="store_true", help="Get current version")
    parser.add_argument("--set", type=str, help="Set version to specified value")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], help="Bump version")
    parser.add_argument("--check-change", action="store_true", help="Check if version changed (for CI)")

    args = parser.parse_args()

    if args.get:
        print(get_version())
    elif args.set:
        set_version(args.set)
    elif args.bump:
        new_version = bump_version(args.bump)
        print(f"Version bumped to {new_version}")
    elif args.check_change:
        check_version_change()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
