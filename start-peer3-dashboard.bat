@echo off
echo Starting Peer 3 (Backend + Dashboard)
echo ========================================
echo Starting Peer 3 Backend on Port 8082...
start "Peer 3 Backend" cmd /k "cd /d "%~dp0" && python peer-backend-3.py"

timeout /t 3 /nobreak >nul

echo Starting Peer 3 Dashboard on Port 3003...
echo Connecting to backend: http://localhost:8082
cd /d "%~dp0peer-dashboard"
set PORT=3003
set REACT_APP_PEER_API=http://localhost:8082
npm start