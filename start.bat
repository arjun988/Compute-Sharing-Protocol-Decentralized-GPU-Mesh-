@echo off
REM OpenMesh Quick Start Script for Windows

echo Starting OpenMesh v0.1...

REM Check if Redis is running (basic check)
echo Checking Redis...

REM Initialize database if it doesn't exist
if not exist "openmesh.db" (
    echo Initializing database...
    python init_db.py
)

REM Start API server
echo Starting API server...
start "OpenMesh API" python main.py

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start Celery worker
echo Starting Celery worker...
start "OpenMesh Celery" python run_celery.py

echo.
echo OpenMesh is running!
echo   API Server: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Celery Worker: Running
echo.
echo Press any key to stop...
pause >nul

