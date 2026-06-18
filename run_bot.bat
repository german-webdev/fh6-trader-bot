@echo off
setlocal

if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -m bot %*
  exit /b %errorlevel%
)

py -3.12 -m bot %*
