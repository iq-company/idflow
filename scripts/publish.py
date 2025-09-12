#!/usr/bin/env python3
"""
Publishing script for idflow package.

This script helps with the publishing process to PyPI.
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse

def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def clean_build():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    run_command("rm -rf build/ dist/ *.egg-info/")
    run_command("find . -name '*.pyc' -delete")
    run_command("find . -name '__pycache__' -type d -exec rm -rf {} +")

def build_package():
    """Build the package."""
    print("Building package...")
    run_command("python -m pip install --upgrade build")
    run_command("python -m build")

def check_package():
    """Check the package."""
    print("Checking package...")
    run_command("python -m pip install --upgrade twine")
    run_command("twine check dist/*")

def publish_to_testpypi():
    """Publish to TestPyPI."""
    print("Publishing to TestPyPI...")
    run_command("twine upload --repository testpypi dist/*")

def publish_to_pypi():
    """Publish to PyPI."""
    print("Publishing to PyPI...")
    run_command("twine upload dist/*")

def test_installation():
    """Test installation from PyPI."""
    print("Testing installation...")
    run_command("pip install --upgrade pip")
    run_command("pip install idflow")
    run_command("idflow --help")

def main():
    parser = argparse.ArgumentParser(description="Publish idflow package")
    parser.add_argument("--test", action="store_true", help="Publish to TestPyPI")
    parser.add_argument("--pypi", action="store_true", help="Publish to PyPI")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--build", action="store_true", help="Build package")
    parser.add_argument("--check", action="store_true", help="Check package")
    parser.add_argument("--test-install", action="store_true", help="Test installation")
    parser.add_argument("--all", action="store_true", help="Run all steps")

    args = parser.parse_args()

    if args.all:
        clean_build()
        build_package()
        check_package()
        if input("Publish to TestPyPI? (y/N): ").lower() == 'y':
            publish_to_testpypi()
        if input("Publish to PyPI? (y/N): ").lower() == 'y':
            publish_to_pypi()
        test_installation()
    else:
        if args.clean:
            clean_build()
        if args.build:
            build_package()
        if args.check:
            check_package()
        if args.test:
            publish_to_testpypi()
        if args.pypi:
            publish_to_pypi()
        if args.test_install:
            test_installation()

if __name__ == "__main__":
    main()
