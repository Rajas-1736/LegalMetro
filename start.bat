@echo off
title VisionX - Legal Metrology Compliance System
echo ======================================================================
echo           STARTING VISIONX LEGAL METROLOGY SYSTEM
echo ======================================================================
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
) else if exist "..\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0..\venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

if exist "VisinoryX\run_server.py" (
    "%PYTHON_EXE%" "VisinoryX\run_server.py"
) else if exist "run_server.py" (
    "%PYTHON_EXE%" "run_server.py"
) else (
    echo Error: run_server.py not found!
)
pause
