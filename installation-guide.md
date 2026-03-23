# Complete Installation and Setup Guide

## Prerequisites Check

### Windows Requirements
- Windows 11 (or Windows 10 version 2004+)
- Administrator privileges
- At least 8GB RAM
- 20GB free disk space

### Software Requirements
- Node.js 18 LTS
- Python 3.10
- Git (optional but recommended)

## Step 1: Install Node.js and Python

### Install Node.js 18 LTS
1. Download from: https://nodejs.org/en/download/
2. Run installer with default settings
3. Verify installation:
```cmd
node --version
npm --version
```

### Install Python 3.10
1. Download from: https://www.python.org/downloads/
2. **IMPORTANT**: Check "Add Python to PATH" during installation
3. Verify installation:
```cmd
python --version
pip --version
```

## Step 2: WSL2 Setup (For SDN Controller)

### Enable WSL2
Open PowerShell as Administrator:
```powershell
# Enable WSL feature
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart Windows (REQUIRED)
```

After restart, open PowerShell as Administrator:
```powershell
# Set WSL2 as default
wsl --set-default-version 2

# Install Ubuntu 22.04
wsl --install -d Ubuntu-22.04
```

### Configure Ubuntu
When Ubuntu starts for the first time:
1. Create username: `sdn-user`
2. Create password
3. Update system:
```bash
sudo apt update && sudo apt upgrade -y
```

### Install SDN Components in WSL2
```bash
# Install Python and development tools
sudo apt install -y python3.10 python3-pip python3-venv git curl

# Install SDN components
sudo apt install -y openvswitch-switch openvswitch-common

# Install network tools
sudo apt install -y net-tools iproute2 tcpdump

# Try to install Ryu (may have compatibility issues)
pip3 install --user eventlet==0.33.3 ryu==4.34

# Install Flask and dependencies
pip3 install flask flask-cors pycryptodome

# Verify installations
python3 --version
sudo ovs-vsctl show

# Test Ryu (if this fails, we'll use simple controller)
python3 -c "import ryu; print('Ryu OK')" || echo "Ryu failed - will use simple controller"
```

## Step 3: Project Setup

### Clone/Copy Project Files
In Windows Command Prompt:
```cmd
cd "C:\Users\%USERNAME%\OneDrive\Desktop\Final Year Projects\SDN"
```

### Install Peer Dashboard Dependencies
```cmd
cd peer-dashboard
npm install
```

### Install Controller Dashboard Dependencies
```cmd
cd ..\controller-dashboard
npm install
```

### Install Python Dependencies for Peer Backend
```cmd
cd ..\peer-backend
pip install flask flask-cors pycryptodome
```

### Install Attack Simulator Dependencies
```cmd
cd ..\attack-scripts
pip install scapy requests
```

## Step 4: Network Configuration

### Find WSL2 IP Address
In WSL2 terminal:
```bash
ip addr show eth0
```
Note the IP address (e.g., 172.x.x.x)

### Configure Windows Firewall
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Click "Change Settings" → "Allow another app"
4. Add Python.exe and Node.js
5. Enable for both Private and Public networks

## Step 5: Start the System

### Terminal 1: Start SDN Controller (WSL2)
```bash
cd /mnt/c/Users/[USERNAME]/OneDrive/Desktop/Final\ Year\ Projects/SDN/sdn-controller
python3 api_server.py
```

### Terminal 2: Start SDN Controller (WSL2)
```bash
cd /mnt/c/Users/[USERNAME]/OneDrive/Desktop/Final\ Year\ Projects/SDN/sdn-controller

# Try Ryu first
ryu-manager security_controller.py

# If Ryu fails, use simple controller:
# python3 simple_controller.py
```

### Terminal 3: Start Peer Backend (Windows)
```cmd
cd "C:\Users\%USERNAME%\OneDrive\Desktop\Final Year Projects\SDN\peer-backend"
python peer_app.py
```

### Terminal 4: Start Peer Dashboard (Windows)
```cmd
cd "C:\Users\%USERNAME%\OneDrive\Desktop\Final Year Projects\SDN\peer-dashboard"
npm start
```

### Terminal 5: Start Controller Dashboard (Windows)
```cmd
cd "C:\Users\%USERNAME%\OneDrive\Desktop\Final Year Projects\SDN\controller-dashboard"
npm start
```

## Step 6: Access the Applications

### Peer Dashboard
- URL: http://localhost:3000
- Use this to discover peers and chat securely

### Controller Dashboard  
- URL: http://localhost:3001
- Use this to monitor network and attacks

### API Endpoints
- Peer API: http://localhost:8080/api/
- Controller API: http://localhost:5000/api/

## Step 7: Test Attack Scenarios

### Run Attack Simulations
In a new Windows Command Prompt:
```cmd
cd "C:\Users\%USERNAME%\OneDrive\Desktop\Final Year Projects\SDN\attack-scripts"

# Test replay attack
python attack_simulator.py --attack replay --duration 30

# Test flood attack  
python attack_simulator.py --attack flood --duration 20 --rate 150

# Test progressive attack (all levels)
python attack_simulator.py --attack progressive
```

## Troubleshooting

### Common Issues

#### WSL2 Not Starting
- Check Windows version (requires 2004+)
- Restart Windows after enabling features
- Run `wsl --shutdown` then `wsl` to restart

#### Port Conflicts
- Peer Dashboard: Change port in package.json
- Controller Dashboard: Change port in package.json  
- APIs: Change port in Python files

#### Network Issues
- Check Windows Firewall settings
- Verify WSL2 IP address
- Test connectivity: `ping [WSL2_IP]`

#### Python Import Errors
- Verify Python PATH
- Reinstall packages: `pip install --upgrade [package]`
- Use virtual environment if needed

#### React Build Errors
- Clear npm cache: `npm cache clean --force`
- Delete node_modules: `rmdir /s node_modules`
- Reinstall: `npm install`

### Verification Commands

#### Check All Services
```cmd
# Check if ports are listening
netstat -an | findstr "3000 3001 8080 5000"

# Check Python processes
tasklist | findstr python

# Check Node.js processes  
tasklist | findstr node
```

#### Test API Connectivity
```cmd
# Test Controller API
curl http://localhost:5000/api/status

# Test Peer API
curl http://localhost:8080/api/peer/status
```

## Demo Preparation

### Before Presentation
1. Start all services in correct order
2. Open both dashboards in separate browser windows
3. Test peer discovery and connection
4. Prepare attack scenarios
5. Check all logs are working

### Demo Flow
1. Show system architecture
2. Demonstrate peer discovery
3. Establish secure session
4. Show encrypted messaging
5. Trigger attacks and show progressive response
6. Highlight security features

### Key Points to Emphasize
- Anonymous authentication
- End-to-end encryption
- Real-time attack detection
- Progressive self-destruct mechanism
- Professional UI/UX
- Complete SDN integration