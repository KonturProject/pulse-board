@echo off
cd /d "%~dp0admin"
if not exist .venv\Scripts\pythonw.exe (
  echo Устанавливаю окружение, это один раз...
  python -m venv .venv && .venv\Scripts\python -m pip install -q -e .
)
start "" .venv\Scripts\pythonw.exe -m npsr_admin
