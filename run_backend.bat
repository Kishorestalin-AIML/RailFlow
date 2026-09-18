@echo off
set PYTHONPATH=%~dp0
echo Starting RailMind FastAPI Backend on http://127.0.0.1:8000 ...
"%~dp0backend\venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
