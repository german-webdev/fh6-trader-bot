from __future__ import annotations

from pathlib import Path
import os
import shutil
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
FINAL_DIST = DIST / "standalone"
TEMP_DIST = DIST / "_standalone_build"
BUILD_ROOT = ROOT / "build"
PYTHON = Path(
    r"C:\Users\musiq\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)


def _on_rmtree_error(func, path, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, onerror=_on_rmtree_error)


def main() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / ".build-tools")

    workpath = BUILD_ROOT / f"pyinstaller-{os.getpid()}"
    safe_rmtree(TEMP_DIST)
    workpath.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            str(PYTHON),
            "-m",
            "PyInstaller",
            "trade-bot.spec",
            "--noconfirm",
            "--clean",
            "--distpath",
            str(TEMP_DIST),
            "--workpath",
            str(workpath),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )

    safe_rmtree(FINAL_DIST)
    FINAL_DIST.mkdir(parents=True, exist_ok=True)
    shutil.move(
        str(TEMP_DIST / "fh6-trader-bot.exe"),
        str(FINAL_DIST / "fh6-trader-bot.exe"),
    )
    safe_rmtree(TEMP_DIST)
    print(f"Standalone build output: {FINAL_DIST / 'fh6-trader-bot.exe'}")


if __name__ == "__main__":
    main()
