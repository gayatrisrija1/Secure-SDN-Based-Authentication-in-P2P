@echo off
echo Cleaning up Multi-Peer Testing Files
echo ====================================

echo.
echo Deleting temporary peer backends...
if exist "peer-backend-2.py" (
    del "peer-backend-2.py"
    echo ✓ Deleted peer-backend-2.py
) else (
    echo ✗ peer-backend-2.py not found
)

if exist "peer-backend-3.py" (
    del "peer-backend-3.py"
    echo ✓ Deleted peer-backend-3.py
) else (
    echo ✗ peer-backend-3.py not found
)

if exist "start-multiple-peers.bat" (
    del "start-multiple-peers.bat"
    echo ✓ Deleted start-multiple-peers.bat
) else (
    echo ✗ start-multiple-peers.bat not found
)

echo.
echo ====================================
echo Cleanup Complete!
echo ====================================
echo.
echo Your original system is restored:
echo - peer-backend/peer_app.py (unchanged)
echo - peer-dashboard/ (unchanged)  
echo - controller-dashboard/ (unchanged)
echo - sdn-controller/ (unchanged)
echo.
echo Press any key to exit...
pause >nul

:: Self-delete this cleanup script
del "%~f0"