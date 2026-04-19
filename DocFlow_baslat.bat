@echo off
title cborn DocFlow
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Sanal ortam yok. Once surayi calistirin:
  echo   python -m venv .venv
  echo   .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
