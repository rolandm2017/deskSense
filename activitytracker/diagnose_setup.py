#!/usr/bin/env python3

import subprocess
import sys
import os
import platform
import json
from pathlib import Path


def run_command(command):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(
            command, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"


def collect_environment_info():
    """Collect information about the Python environment"""
    info = {}

    # System and Python info
    info["platform"] = platform.platform()
    info["python_version"] = platform.python_version()
    info["python_path"] = sys.executable
    info["python_implementation"] = platform.python_implementation()

    # Python paths
    info["sys_path"] = sys.path

    # Environment variables
    py_env_vars = {k: v for k, v in os.environ.items() if 'py' in k.lower()}
    info["python_env_vars"] = py_env_vars

    # Get installed packages using pip instead of pkg_resources
    pip_list = run_command("pip list --format=json")
    try:
        info["installed_packages"] = json.loads(pip_list)
    except:
        info["installed_packages"] = f"Error parsing pip list output: {pip_list}"

    # Pytest specific info
    pytest_path = run_command("which pytest")
    info["pytest_path"] = pytest_path

    if "Error" not in pytest_path:
        pytest_version = run_command("pytest --version")
        info["pytest_version"] = pytest_version

        # Test collection info (if pytest is available)
        try:
            collect_only = run_command("pytest --collect-only -v")
            info["pytest_collection"] = collect_only
        except:
            info["pytest_collection"] = "Failed to collect tests"

    # Check for the project package
    try:
        activitytracker_info = run_command("pip show activitytracker")
        info["project_package_info"] = activitytracker_info
    except:
        info["project_package_info"] = "Package not found"

    # Directory structure
    cwd = os.getcwd()
    info["current_dir"] = cwd

    # List project files
    try:
        file_list = run_command(
            f"find {cwd} -type f -name '*.py' -not -path '*/\\.*/*' | sort")
        info["python_files"] = file_list.split('\n') if file_list else []
    except:
        info["python_files"] = []

    # Check for configuration files
    pytest_configs = []
    for config_file in ["pytest.ini", "pyproject.toml", "conftest.py", "setup.cfg"]:
        config_path = Path(cwd) / config_file
        if config_path.exists():
            pytest_configs.append(str(config_path))
            with open(config_path, 'r') as f:
                info[f"{config_file}_content"] = f.read()

    info["pytest_config_files"] = pytest_configs

    return info


if __name__ == "__main__":
    info = collect_environment_info()

    # Save to a JSON file
    output_file = f"pytest_env_report_{platform.node()}.json"
    with open(output_file, 'w') as f:
        json.dump(info, f, indent=2, default=str)

    print(f"Environment information saved to {output_file}")

    # Also print key information to console
    print("\n=== Python Environment Report ===")
    print(f"Python: {info['python_version']} ({info['python_path']})")
    print(f"Platform: {info['platform']}")
    print(f"Pytest: {info.get('pytest_version', 'Not found')}")
    print(f"Current directory: {info['current_dir']}")

    print("\nPython path:")
    for path in info['sys_path'][:15]:
        print(f"  - {path}")
    if len(info['sys_path']) > 5:
        print(f"  - ... and {len(info['sys_path']) - 5} more")

    print("\nInstalled packages (first 10):")
    if isinstance(info['installed_packages'], list):
        for pkg in info['installed_packages'][:10]:
            print(f"  - {pkg.get('name')} {pkg.get('version')}")
        if len(info['installed_packages']) > 10:
            print(f"  - ... and {len(info['installed_packages']) - 10} more")
    else:
        print(f"  Error retrieving packages: {info['installed_packages']}")

    print("\nPytest collection:")
    collection = info.get('pytest_collection', 'Not available')
    collection_preview = '\n'.join(collection.split(
        '\n')[:10]) if isinstance(collection, str) else collection
    print(collection_preview)
    if isinstance(collection, str) and len(collection.split('\n')) > 10:
        print(f"  ... and {len(collection.split('\n')) - 10} more lines")

    print(f"\nFull details saved to {output_file}")
