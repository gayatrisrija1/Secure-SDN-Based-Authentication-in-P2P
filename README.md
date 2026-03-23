# SDN-Based Anonymous P2P Communication System

## Project Overview
A complete SDN security system with progressive attack-triggered self-destruct mechanism.

## Architecture
- **SDN Controller**: Python Flask API (Port 5000) + Ubuntu WSL2 for network simulation
- **Peer Applications**: Windows Python Flask backends + React frontends
- **Security**: Anonymous authentication, encrypted sessions, progressive response

## How to Run the Application

### Prerequisites
**Install Dependencies:**
```cmd
REM Python dependencies
pip install flask flask-cors pycryptodome requests

REM Node.js dependencies
cd peer-dashboard
npm install
cd ..
```

### Step 1: Ubuntu WSL2 Setup (One-time)
Open Ubuntu terminal (run `wsl -d Ubuntu-22.04` in cmd):
```bash
# Create virtual network bridge
sudo ovs-vsctl add-br br0
```
This creates the virtual network bridge for SDN simulation.

**Note:** You're already logged in as the correct user (sdn-user), so no need to switch users.

### Step 2: Start SDN Controller
Open Windows Command Prompt:
```cmd
cd sdn-controller
python api_server.py
```
- Controller runs on http://localhost:5000
- Handles peer registration, attack detection, security alerts
- **Note**: You'll see "Not Found" if you visit http://localhost:5000 in browser - this is normal! The controller only has API endpoints, no web interface.

### Step 3: Start All Peers

**Option A: Quick Start (All at Once)**
```cmd
start-multiple-peers.bat
```
This automatically starts all 3 peer backends + dashboards.

**Option B: Individual Peer Setup**
```cmd
start-peer1-dashboard.bat
start-peer2-dashboard.bat
start-peer3-dashboard.bat
```

**Option C: Manual Setup (If bat files don't work)**

**Start Backends (3 separate CMD windows):**
```cmd
REM Terminal 1 - Peer 1 Backend
cd peer-backend
python peer_app.py

REM Terminal 2 - Peer 2 Backend
python peer-backend-2.py

REM Terminal 3 - Peer 3 Backend
python peer-backend-3.py
```

**Start Dashboards (3 separate CMD windows):**
```cmd
REM Terminal 4 - Peer 1 Dashboard
cd peer-dashboard
set PORT=3000
set REACT_APP_PEER_API=http://localhost:8080
npm start

REM Terminal 5 - Peer 2 Dashboard
cd peer-dashboard
set PORT=3002
set REACT_APP_PEER_API=http://localhost:8081
npm start

REM Terminal 6 - Peer 3 Dashboard
cd peer-dashboard
set PORT=3003
set REACT_APP_PEER_API=http://localhost:8082
npm start
```

### Access Points
- **SDN Controller**: http://localhost:5000
- **Peer 1 Dashboard**: http://localhost:3000 (Normal Peer)
- **Peer 2 Dashboard**: http://localhost:3002 (Normal Peer)
- **Peer 3 Dashboard**: http://localhost:3003 (Attacker Interface)

### Step 4: Test the System

1. **Start All Peers:**
   - Click "Start Peer" on all 3 dashboards
   - Peers will register with controller and discover each other

2. **Establish P2P Connection:**
   - On Peer 1 or 2 dashboard, click "Discover Peers"
   - Click "Connect" to another peer
   - Accept the connection request on the target peer

3. **Test Messaging:**
   - Send encrypted messages between connected peers
   - Messages are encrypted end-to-end with AES

4. **Launch Attacks:**
   - On Peer 3 (attacker) dashboard, use the attack panel
   - Select attack type (Replay/Flooding) and intensity (Low/Medium/High/Critical)
   - Controller automatically detects attacks and triggers progressive responses

5. **Monitor Security:**
   - Check security alerts on victim peer dashboards
   - Controller logs show attack detection and response actions
   - Progressive responses: Monitoring → Session Termination → Key Destruction → Peer Isolation

## Required Dependencies

**System Requirements:**
- Windows 10/11 with WSL2 enabled
- Ubuntu WSL2 distribution
- Python 3.7+
- Node.js 14+

**Python (Backend):**
```cmd
pip install flask flask-cors pycryptodome requests
```

**Node.js (Frontend):**
```cmd
cd peer-dashboard
npm install
cd ..
```

**Ubuntu WSL2 (Network Simulation):**
```cmd
REM Open Ubuntu WSL2
wsl -d Ubuntu-22.04

REM Then run these commands in Ubuntu:
REM sudo apt update
REM sudo apt install openvswitch-switch
REM sudo ovs-vsctl add-br br0
```

## Security Features
- Anonymous peer discovery via UDP broadcast
- Session-based AES-256 encryption
- Real-time attack detection (replay, flooding)
- Progressive self-destruct mechanism
- Victim notification system
- Network monitoring and logging
- SDN-based traffic control

## Attack Detection
- **Replay Attacks**: Duplicate nonce detection across all peers
- **Flooding Attacks**: High packet rate detection
- **Automatic Response**: Progressive severity-based actions
- **Victim Alerts**: Real-time security notifications
- **Network Isolation**: SDN controller can isolate malicious peers

## Development Status
- [x] WSL2 Setup
- [x] SDN Controller Implementation
- [x] Peer Backend Development
- [x] React UI Development
- [x] Security Integration
- [x] Demo Preparation
- [x] Attack Detection System
- [x] Progressive Response Mechanism
