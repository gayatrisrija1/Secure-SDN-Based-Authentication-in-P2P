@echo off
echo Fixing Ryu compatibility issue...
pip install --upgrade dnspython==2.1.0
echo Done! Now try running: ryu-manager simple_controller.py
pause