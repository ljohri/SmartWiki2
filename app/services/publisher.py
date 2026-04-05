from __future__ import annotations

import shutil
import subprocess
import threading
import time
from pathlib import Path

from app.config import Settings
from app.util.fs import ensure_dir
from publisher.sync_to_quartz import sync_vault_content_to_quartz
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


def sync_content(settings: Settings, vault_root: Path) -> Path:
    quartz_root = settings.resolved_quartz_dir
    ensure_dir(quartz_root)
    return sync_vault_content_to_quartz(vault_root, quartz_root)


def build_site(settings: Settings) -> Path:
    quartz_root = settings.resolved_quartz_dir
    site_dir = settings.resolved_site_dir
    ensure_dir(site_dir)
    subprocess.run(["npm", "run", "build"], cwd=quartz_root, check=True)
    generated = quartz_root / "public"
    if generated.exists():
        if site_dir.exists():
            shutil.rmtree(site_dir)
        shutil.copytree(generated, site_dir, dirs_exist_ok=True)
    return site_dir


def sync_and_build(settings: Settings, vault_root: Path) -> Path:
    sync_content(settings, vault_root)
    return build_site(settings)


class _RebuildOnChangeHandler(FileSystemEventHandler):
    def __init__(self, settings: Settings, vault_root: Path) -> None:
        self._settings = settings
        self._vault_root = vault_root
        self._lock = threading.Lock()
        self._last_run = 0.0

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        now = time.time()
        with self._lock:
            # Basic debounce to avoid duplicate rebuild bursts during save storms.
            if now - self._last_run < 1.0:
                return
            self._last_run = now
        sync_and_build(self._settings, self._vault_root)


def start_dev_rebuild_watcher(settings: Settings, vault_root: Path) -> Observer:
    observer = Observer()
    handler = _RebuildOnChangeHandler(settings, vault_root)
    observer.schedule(handler, str(vault_root / "content"), recursive=True)
    observer.start()
    return observer
