@echo off
setlocal

if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe scripts\build_release.py
  exit /b %errorlevel%
)

py -3.12 scripts\build_release.py
