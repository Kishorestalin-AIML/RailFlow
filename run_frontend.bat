@echo off
set "PATH=C:\Users\kisho\AppData\Local\Programs\nodejs;%PATH%"
cd /d "%~dp0frontend"
echo Starting RailMind React/Vite Frontend on http://localhost:5173 ...
npm run dev -- --host 127.0.0.1 --port 5173
pause
