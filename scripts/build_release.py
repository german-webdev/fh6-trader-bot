from __future__ import annotations

from pathlib import Path
import os
import shutil
import stat
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
RELEASE_DIR = DIST / "fh6-trader-bot"
ZIP_PATH = DIST / "fh6-trader-bot-release.zip"
STANDALONE_DIR = DIST / "standalone" / "fh6-trader-bot"
STANDALONE_ZIP_PATH = DIST / "fh6-trader-bot-standalone.zip"

FILES_TO_COPY = (
    ROOT / "README.md",
    ROOT / "config.toml",
    ROOT / "requirements.txt",
    ROOT / "run_bot.bat",
    ROOT / "pyproject.toml",
)

DIRS_TO_COPY = (
    ROOT / "bot",
)


def reset_release_dir() -> None:
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR, onerror=_on_rmtree_error)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)


def _on_rmtree_error(func, path, exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def copy_project_files() -> None:
    for path in FILES_TO_COPY:
        shutil.copy2(path, RELEASE_DIR / path.name)

    for directory in DIRS_TO_COPY:
        shutil.copytree(
            directory,
            RELEASE_DIR / directory.name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )


def write_release_notes() -> None:
    (RELEASE_DIR / "RELEASE.txt").write_text(
        "\n".join(
            [
                "FH6 Trader Bot Release Bundle",
                "",
                "Quick start:",
                "1. Install Python 3.12.",
                "2. Install dependencies with: py -3.12 -m pip install -r requirements.txt",
                "3. Start the bot with: run_bot.bat run",
                "4. Validate detection with: run_bot.bat detect",
                "",
                "Runtime hotkeys:",
                "F6 - resume",
                "F7 - pause/resume",
                "F8 - stop",
            ]
        ),
        encoding="utf-8",
    )


def zip_release() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in RELEASE_DIR.rglob("*"):
            archive.write(path, path.relative_to(RELEASE_DIR.parent))


def zip_standalone_if_present() -> None:
    if not STANDALONE_DIR.exists():
        return

    if STANDALONE_ZIP_PATH.exists():
        STANDALONE_ZIP_PATH.unlink()

    with zipfile.ZipFile(
        STANDALONE_ZIP_PATH,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in STANDALONE_DIR.rglob("*"):
            archive.write(path, path.relative_to(STANDALONE_DIR.parent))


def main() -> None:
    reset_release_dir()
    copy_project_files()
    write_release_notes()
    zip_release()
    zip_standalone_if_present()
    print(f"Release directory: {RELEASE_DIR}")
    print(f"Release zip: {ZIP_PATH}")
    if STANDALONE_DIR.exists():
        print(f"Standalone zip: {STANDALONE_ZIP_PATH}")


if __name__ == "__main__":
    main()
