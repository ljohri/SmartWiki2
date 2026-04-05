from __future__ import annotations

import subprocess
from pathlib import Path


def clone_repo(repo_url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", repo_url, str(destination)], check=True)


def fetch_repo(repo_path: Path) -> None:
    subprocess.run(["git", "-C", str(repo_path), "fetch", "--all"], check=True)
