

### WSL2 Terminal 1 (current): Start API Server
Open another Command Prompt and run:
```cmd
wsl -d Ubuntu-22.04
```
Then:
```bash
cd /mnt/c/Users/Gayatri/Desktop/sdn_project/sdn_project/sdn-controller
python3 api_server.py

./start-with-windows-host.sh
```

### WSL2 Terminal 2: Start SDN Controller
Open another Command Prompt and run:
```cmd
wsl -d Ubuntu-22.04
```
Then:
```bash
cd /mnt/c/Users/Gayatri/Desktop/sdn_project/sdn_project
python3 simple_controller.py
```

C:\Users\Gayatri\Desktop\sdn_project\sdn_project\start-peer1-dashboard.bat

C:\Users\Gayatri\Desktop\sdn_project\sdn_project\start-peer2-dashboard.bat
C:\Users\Gayatri\Desktop\sdn_project\sdn_project\start-peer3-dashboard.bat




C:\Users\Gayatri\Desktop\sdn_project\sdn_project>python test-burst-attack.py