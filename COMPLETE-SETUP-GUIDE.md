# Complete SDN Project Setup Guide

## Overview
This guide covers setting up the SDN-Based Anonymous P2P Communication System on a new laptop with both Windows and Ubuntu (WSL2).

---

## System Requirements

| Component | Minimum Version | Recommended Version |
|-----------|-----------------|---------------------|
| Windows | Windows 10 (2004+) | Windows 11 |
| Ubuntu (WSL2) | Ubuntu 20.04 | Ubuntu 22.04 |
| Python | 3.8+ | 3.12.x |
| Node.js | 14.x | 18.x (LTS) |
| npm | 6.x | 10.x |

---

## Part 1: Windows Setup

### Step 1.1: Install Python 3.12

1. Download Python from: https://www.python.org/downloads/
2. **IMPORTANT**: During installation, check:
   - [x] "Add Python to PATH"
   - [x] "Install pip"
3. Verify installation:
   ```cmd
   python --version
   # Should show: Python 3.12.x

   pip --version
   # Should show: pip 24.x
   ```

### Step 1.2: Install Node.js 18 LTS

1. Download Node.js LTS from: https://nodejs.org/
2. Run the installer with default settings
3. Verify installation:
   ```cmd
   node --version
   # Should show: v18.x.x

   npm --version
   # Should show: 10.x.x
   ```

### Step 1.3: Install Python Dependencies

Open Command Prompt (Admin recommended) and run:

```cmd
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install pycryptodome==3.20.0
pip install requests==2.31.0
```

**Or install all at once:**
```cmd
pip install flask flask-cors pycryptodome requests
```

**Verify installations:**
```cmd
pip list | findstr flask
pip list | findstr pycryptodome
pip list | findstr requests
```

### Step 1.4: Clone/Copy the Project

Copy the SDN folder to your desired location:
```
C:\Users\<YourUsername>\Desktop\SDN\
```

### Step 1.5: Install Node.js Dependencies

Open Command Prompt and run:

```cmd
REM Install peer-dashboard dependencies
cd C:\Users\<YourUsername>\Desktop\SDN\peer-dashboard
npm install

REM Install controller-dashboard dependencies
cd C:\Users\<YourUsername>\Desktop\SDN\controller-dashboard
npm install
```

---

## Part 2: Ubuntu (WSL2) Setup

### Step 2.1: Enable WSL2 on Windows

Open **PowerShell as Administrator** and run:

```powershell
# Enable WSL feature
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**Restart your computer after this step.**

### Step 2.2: Set WSL2 as Default

After restart, open PowerShell as Administrator:

```powershell
# Set WSL 2 as default
wsl --set-default-version 2

# Update WSL
wsl --update
```

### Step 2.3: Install Ubuntu 22.04

```powershell
# Install Ubuntu 22.04
wsl --install -d Ubuntu-22.04
```

**Follow the prompts to:**
1. Create a username (e.g., `sdn-user`)
2. Create a password

### Step 2.4: Configure Ubuntu

Open Ubuntu terminal (search "Ubuntu" in Start menu or run `wsl -d Ubuntu-22.04`):

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Python dependencies
pip3 install flask flask-cors requests

# Install Ryu SDN Controller
pip3 install ryu

# Install Open vSwitch (for network simulation)
sudo apt install openvswitch-switch -y

# Install additional networking tools
sudo apt install net-tools iproute2 -y

# Verify installations
python3 --version
pip3 list | grep -E "(flask|ryu|requests)"
```

### Step 2.5: Create Network Bridge (One-time)

```bash
# Start Open vSwitch service
sudo service openvswitch-switch start

# Create virtual bridge
sudo ovs-vsctl add-br br0

# Verify bridge creation
sudo ovs-vsctl show
```

---

## Part 3: Project Directory Structure

After setup, your project should look like:

```
SDN/
├── sdn-controller/           # SDN Controller (runs in WSL2)
│   ├── api_server.py         # Flask API Server
│   ├── security_controller.py # Ryu SDN Controller
│   └── simple_controller.py  # Simple Ryu Controller
│
├── peer-backend/             # Peer 1 Backend
│   └── peer_app.py           # Flask backend (Port 8080)
│
├── peer-backend-2.py         # Peer 2 Backend (Port 8081)
├── peer-backend-3.py         # Peer 3/Attacker Backend (Port 8082)
│
├── peer-dashboard/           # React Frontend (shared)
│   ├── package.json
│   ├── src/
│   └── node_modules/
│
├── controller-dashboard/     # Controller Dashboard
│   ├── package.json
│   ├── src/
│   └── node_modules/
│
└── start-*.bat               # Startup scripts
```

---

## Part 4: Required Package Versions

### Python Packages (Windows - Peer Backends)

| Package | Version | Purpose |
|---------|---------|---------|
| flask | 3.0.0 | Web framework for backends |
| flask-cors | 4.0.0 | CORS support for React frontends |
| pycryptodome | 3.20.0 | AES-256 encryption |
| requests | 2.31.0 | HTTP client for controller communication |

**Install command:**
```cmd
pip install flask==3.0.0 flask-cors==4.0.0 pycryptodome==3.20.0 requests==2.31.0
```

### Python Packages (Ubuntu/WSL2 - SDN Controller)

| Package | Version | Purpose |
|---------|---------|---------|
| flask | 3.0.0 | API server |
| flask-cors | 4.0.0 | CORS support |
| requests | 2.31.0 | HTTP client |
| ryu | 4.34 | SDN controller framework |

**Install command:**
```bash
pip3 install flask==3.0.0 flask-cors==4.0.0 requests==2.31.0 ryu
```

### Node.js Packages (React Dashboards)

**peer-dashboard/package.json:**
| Package | Version | Purpose |
|---------|---------|---------|
| react | ^18.2.0 | UI framework |
| react-dom | ^18.2.0 | React DOM rendering |
| react-router-dom | ^6.8.0 | Routing |
| react-scripts | 5.0.1 | Build scripts |
| axios | ^1.3.0 | HTTP client |
| lucide-react | ^0.263.1 | Icons |
| tailwindcss | ^3.2.0 | CSS framework |
| autoprefixer | ^10.4.13 | CSS processing |
| postcss | ^8.4.21 | CSS processing |

**controller-dashboard/package.json (additional):**
| Package | Version | Purpose |
|---------|---------|---------|
| recharts | ^2.5.0 | Charts and graphs |

---

## Part 5: Quick Setup Commands

### One-Time Setup (Copy & Paste)

**Windows Command Prompt (Admin):**
```cmd
REM Install all Python packages
pip install flask==3.0.0 flask-cors==4.0.0 pycryptodome==3.20.0 requests==2.31.0

REM Navigate to project and install Node packages
cd C:\Users\<YourUsername>\Desktop\SDN\peer-dashboard
npm install

cd C:\Users\<YourUsername>\Desktop\SDN\controller-dashboard
npm install
```

**Ubuntu/WSL2 Terminal:**
```bash
# Update and install system packages
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip openvswitch-switch net-tools -y

# Install Python packages
pip3 install flask flask-cors requests ryu

# Setup network bridge
sudo service openvswitch-switch start
sudo ovs-vsctl add-br br0
```

---

## Part 6: Running the Application

### Terminal Layout (7 terminals needed)

```
┌─────────────────────────────────────────────────────────────────┐
│  Terminal 1: WSL2 - API Server (Port 5000)                      │
│  Terminal 2: WSL2 - SDN Controller (Optional - Ryu)             │
├─────────────────────────────────────────────────────────────────┤
│  Terminal 3: Windows - Peer 1 Backend (Port 8080)               │
│  Terminal 4: Windows - Peer 2 Backend (Port 8081)               │
│  Terminal 5: Windows - Peer 3 Backend (Port 8082)               │
├─────────────────────────────────────────────────────────────────┤
│  Terminal 6: Windows - Peer Dashboard (Port 3000, 3002, 3003)   │
│  Terminal 7: Windows - Controller Dashboard (Port 3001)         │
└─────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Startup

**1. Start API Server (WSL2):**
```cmd
wsl -d Ubuntu-22.04
```
Then in Ubuntu:
```bash
cd /mnt/c/Users/<YourUsername>/Desktop/SDN/sdn-controller
export VICTIM_PEER_HOST=$(hostname -I | awk '{print $1}')  # Get Windows IP
python3 api_server.py
```

**2. Start Peer Backends (Windows CMD - 3 separate terminals):**
```cmd
REM Terminal 1 - Peer 1
cd C:\Users\<YourUsername>\Desktop\SDN\peer-backend
python peer_app.py

REM Terminal 2 - Peer 2
cd C:\Users\<YourUsername>\Desktop\SDN
python peer-backend-2.py

REM Terminal 3 - Peer 3 (Attacker)
cd C:\Users\<YourUsername>\Desktop\SDN
python peer-backend-3.py
```

**3. Start Dashboards (Windows CMD - 3 terminals):**
```cmd
REM Peer 1 Dashboard (Port 3000)
cd C:\Users\<YourUsername>\Desktop\SDN\peer-dashboard
set PORT=3000
set REACT_APP_PEER_API=http://localhost:8080
npm start

REM Peer 2 Dashboard (Port 3002)
cd C:\Users\<YourUsername>\Desktop\SDN\peer-dashboard
set PORT=3002
set REACT_APP_PEER_API=http://localhost:8081
npm start

REM Peer 3 Dashboard (Port 3003)
cd C:\Users\<YourUsername>\Desktop\SDN\peer-dashboard
set PORT=3003
set REACT_APP_PEER_API=http://localhost:8082
npm start
```

### Access URLs

| Component | URL |
|-----------|-----|
| Peer 1 Dashboard | http://localhost:3000 |
| Peer 2 Dashboard | http://localhost:3002 |
| Peer 3 Dashboard (Attacker) | http://localhost:3003 |
| Controller API | http://localhost:5000 |
| Controller Dashboard | http://localhost:3001 |

---

## Part 7: Troubleshooting

### Common Issues

**1. Python not found:**
```cmd
REM Add Python to PATH
set PATH=%PATH%;C:\Python312;C:\Python312\Scripts
```

**2. npm install fails:**
```cmd
REM Clear npm cache and retry
npm cache clean --force
rd /s /q node_modules
npm install
```

**3. WSL not starting:**
```powershell
# Restart WSL
wsl --shutdown
wsl -d Ubuntu-22.04
```

**4. Port already in use:**
```cmd
REM Find and kill process on port
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

**5. Controller can't reach peers (WSL network issue):**
```bash
# In WSL, get Windows host IP
cat /etc/resolv.conf | grep nameserver
# Use this IP for VICTIM_PEER_HOST
export VICTIM_PEER_HOST=<Windows_IP>
```

---

## Part 8: Verification Checklist

Run these commands to verify your setup:

### Windows
```cmd
REM Check Python
python --version
# Expected: Python 3.12.x

REM Check packages
pip show flask pycryptodome requests flask-cors

REM Check Node.js
node --version
# Expected: v18.x.x

npm --version
# Expected: 10.x.x
```

### Ubuntu/WSL2
```bash
# Check Python
python3 --version
# Expected: Python 3.10.x or 3.12.x

# Check packages
pip3 show flask ryu requests

# Check Open vSwitch
sudo ovs-vsctl show
# Should show br0 bridge
```

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────┐
│                    QUICK START                          │
├────────────────────────────────────────────────────────┤
│ INSTALL (Windows):                                      │
│   pip install flask flask-cors pycryptodome requests   │
│   cd peer-dashboard && npm install                      │
│                                                         │
│ INSTALL (WSL2):                                         │
│   pip3 install flask flask-cors requests ryu           │
│   sudo apt install openvswitch-switch                  │
│                                                         │
│ RUN (Order matters!):                                   │
│   1. WSL2: python3 api_server.py                       │
│   2. Windows: python peer_app.py                       │
│   3. Windows: python peer-backend-2.py                 │
│   4. Windows: python peer-backend-3.py                 │
│   5. Windows: npm start (peer-dashboard)               │
│                                                         │
│ PORTS:                                                  │
│   API Server:    5000 (WSL2)                           │
│   Peer 1:        8080 (Backend) / 3000 (Dashboard)     │
│   Peer 2:        8081 (Backend) / 3002 (Dashboard)     │
│   Peer 3:        8082 (Backend) / 3003 (Dashboard)     │
└────────────────────────────────────────────────────────┘
```

---

## Version Summary

| Component | Version Used |
|-----------|--------------|
| Python | 3.12.6 |
| Node.js | 18.20.8 (LTS) |
| npm | 10.8.2 |
| Flask | 3.0.0 |
| Flask-CORS | 4.0.0 |
| PyCryptodome | 3.20.0 |
| Requests | 2.31.0 |
| Ryu | 4.34 |
| React | 18.2.0 |
| Tailwind CSS | 3.2.0 |
| Ubuntu WSL | 22.04 LTS |
