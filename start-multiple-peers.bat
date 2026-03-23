@echo off
echo Starting Multiple Peer Testing Environment
echo ==========================================

echo.
echo Starting Peer 1 (Port 8080)...
start "Peer 1" cmd /k "cd /d "%~dp0peer-backend" && python peer_app.py"

timeout /t 3 /nobreak >nul

echo Starting Peer 2 (Port 8081)...
start "Peer 2" cmd /k "cd /d "%~dp0" && python peer-backend-2.py"

timeout /t 3 /nobreak >nul

echo Starting Peer 3 - Attacker (Port 8082)...
start "Peer 3 Attacker" cmd /k "cd /d "%~dp0" && python peer-backend-3.py"

timeout /t 3 /nobreak >nul

echo.
echo Starting Peer Dashboards...
echo.

echo Starting Peer 1 Dashboard (Port 3000)...
start "Peer 1 Dashboard" cmd /k "cd /d "%~dp0peer-dashboard" && set PORT=3000 && set REACT_APP_PEER_API=http://localhost:8080 && npm start"

timeout /t 5 /nobreak >nul

echo Starting Peer 2 Dashboard (Port 3002)...
start "Peer 2 Dashboard" cmd /k "cd /d "%~dp0peer-dashboard" && set PORT=3002 && set REACT_APP_PEER_API=http://localhost:8081 && npm start"

timeout /t 5 /nobreak >nul

echo Starting Peer 3 Dashboard (Port 3003)...
start "Peer 3 Dashboard" cmd /k "cd /d "%~dp0peer-dashboard" && set PORT=3003 && set REACT_APP_PEER_API=http://localhost:8082 && npm start"

echo.
echo ==========================================
echo Multi-Peer Testing Environment Started!
echo ==========================================
echo.
echo Open these URLs in your browser:
echo - Controller Dashboard: http://localhost:3001
echo - Peer 1 Dashboard: http://localhost:3000
echo - Peer 2 Dashboard: http://localhost:3002  
echo - Peer 3 Dashboard: http://localhost:3003
echo.
echo Press any key to exit...
pause >nul