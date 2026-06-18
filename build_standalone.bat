@echo off
setlocal

set PYTHONPATH=%CD%\.build-tools
C:\Users\musiq\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m PyInstaller trade-bot.spec --noconfirm --clean --distpath dist\standalone --workpath build\pyinstaller
