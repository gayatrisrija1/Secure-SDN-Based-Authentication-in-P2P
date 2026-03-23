@echo off
echo Starting Peer 1 (Backend + Dashboard)
echo ========================================
echo Starting Peer 1 Backend on Port 8080...
start "Peer 1 Backend" cmd /k "cd /d "%~dp0peer-backend" && python peer_app.py"

timeout /t 3 /nobreak >nul

echo Starting Peer 1 Dashboard on Port 3000...
echo Connecting to backend: http://localhost:8080
cd /d "%~dp0peer-dashboard"
set PORT=3000
set REACT_APP_PEER_API=http://localhost:8080
npm start