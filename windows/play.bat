@echo off
rem Starts CP Controller. Gets the latest version first when git is installed.
cd /d "%~dp0.."
where git >nul 2>nul && git pull --ff-only
uv run main.py
