"""
Git utilities for change detection.
Used by incremental graph update: detect which files changed (unstaged + staged).
"""

import subprocess
from pathlib import Path
from typing import List


def get_changed_files(repo_path: str) -> List[str]:
    """
    Return a list of modified Python files (paths relative to repo_path).
    Uses 'git diff --name-only' (unstaged) and 'git diff --name-only HEAD' (staged).
    """
    repo = Path(repo_path).resolve()
    changed: set[str] = set()

    commands = [
        ["git", "diff", "--name-only"],  # Unstaged changes
        ["git", "diff", "--name-only", "HEAD"],  # Staged changes
    ]

    for cmd in commands:
        try:
            out = subprocess.check_output(
                cmd,
                cwd=repo,
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            for line in out.splitlines():
                line = line.strip()
                if line.endswith(".py"):
                    changed.add(line)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return sorted(changed)
