"""Run MkDocs and rebuild generated pages when source notes change."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


PROJECT = Path(__file__).resolve().parents[1]
CONTENT = PROJECT / "content"
BUILD_SCRIPT = PROJECT / "scripts" / "build_docs.py"


def build_docs() -> None:
    subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=PROJECT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def report(message: str) -> None:
    if sys.stdout is not None:
        print(message, flush=True)


class ContentChangeHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self.last_rebuild = 0.0

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory or event.event_type not in {"created", "modified", "moved", "deleted"}:
            return
        # Editors often save a file through several near-simultaneous events.
        if time.monotonic() - self.last_rebuild < 0.5:
            return
        self.last_rebuild = time.monotonic()
        try:
            build_docs()
            report("Source files changed — local site updated.")
        except subprocess.CalledProcessError as error:
            report(f"Could not update local site: {error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8005)
    args = parser.parse_args()

    build_docs()
    mkdocs = subprocess.Popen(
        [sys.executable, "-m", "mkdocs", "serve", "--dev-addr", f"127.0.0.1:{args.port}"],
        cwd=PROJECT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    observer = Observer()
    observer.schedule(ContentChangeHandler(), str(CONTENT), recursive=True)
    observer.start()
    report(f"Development site: http://127.0.0.1:{args.port}/")

    try:
        while mkdocs.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        if mkdocs.poll() is None:
            mkdocs.terminate()


if __name__ == "__main__":
    main()
