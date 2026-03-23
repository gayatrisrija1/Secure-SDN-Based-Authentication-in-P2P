@echo off
echo Starting Peer 2 (Backend + Dashboard)
echo ========================================
echo Starting Peer 2 Backend on Port 8081...
start "Peer 2 Backend" cmd /k "cd /d "%~dp0" && python peer-backend-2.py"

timeout /t 3 /nobreak >nul

echo Starting Peer 2 Dashboard on Port 3002...
echo Connecting to backend: http://localhost:8081
cd /d "%~dp0peer-dashboard"
set PORT=3002
set REACT_APP_PEER_API=http://localhost:8081
npm start