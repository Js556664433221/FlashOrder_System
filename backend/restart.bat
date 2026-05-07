@echo off
echo Killing processes on port 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001.*LISTEN"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 3 /nobreak >nul
echo Starting server...
cd "C:\Users\limji\OneDrive\Desktop\cart system\backend"
.\venv\Scripts\python.exe run_server.py