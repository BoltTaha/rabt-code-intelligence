"""
Change detection: discover changed Python files via git and trigger graph rebuild.
Keeps the graph "living" by re-parsing when the repo changes.
"""

import subprocess
from pathlib import Path
from typing import List


def get_changed_python_files(repo_path: str | Path, ref: str = "HEAD") -> List[Path]:
    """
    Return list of Python file paths under repo_path that have changed since ref.
    Uses `git diff --name-only ref`; if not a git repo or git unavailable, returns [].
    """
    repo = Path(repo_path).resolve()
    if not repo.exists() or not repo.is_dir():
        return []

    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", ref, "--", str(repo)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []

    if out.returncode != 0:
        return []

    changed: List[Path] = []
    for line in (out.stdout or "").strip().splitlines():
        line = line.strip()
        if not line or not line.endswith(".py"):
            continue
        p = (repo / line).resolve()
        if p.exists() and p.is_file():
            changed.append(p)
    return changed


def get_untracked_python_files(repo_path: str | Path) -> List[Path]:
    """Return list of untracked .py files under repo_path."""
    repo = Path(repo_path).resolve()
    if not repo.exists() or not repo.is_dir():
        return []

    try:
        out = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", str(repo)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=repo,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []

    if out.returncode != 0:
        return []

    untracked: List[Path] = []
    for line in (out.stdout or "").strip().splitlines():
        line = line.strip()
        if not line or not line.endswith(".py"):
            continue
        p = (repo / line).resolve()
        if p.exists() and p.is_file():
            untracked.append(p)
    return untracked


def has_python_changes(repo_path: str | Path, ref: str = "HEAD") -> bool:
    """True if any .py file under repo_path is changed or untracked."""
    changed = get_changed_python_files(repo_path, ref)
    untracked = get_untracked_python_files(repo_path)
    return len(changed) > 0 or len(untracked) > 0


def is_git_repo(path: str | Path) -> bool:
    """True if path is inside a git repository."""
    p = Path(path).resolve()
    for _ in range(20):
        if (p / ".git").exists():
            return True
        if p == p.parent:
            break
        p = p.parent
    return False
