# WSL Networking Fix - Controller Cannot Reach Windows Peers

## The Problem

Your controller logs show:
```
ERROR:api_server:  ❌ Failed to notify port 8080: HTTPConnectionPool(host='localhost', port=8080):
Max retries exceeded with url: /api/security/notify (Caused by NewConnectionError(
'Failed to establish a new connection: [Errno 111] Connection refused'))
```

**Root Cause:** Your SDN controller runs in **Ubuntu/WSL** but your peer backends run on **Windows**. When the controller tries to connect to `localhost:8080`, it looks for services inside WSL, not on the Windows host!

```
┌─────────────────────────────────────┐
│         Windows Host                │
│  ┌──────────────────────────────┐   │
│  │ Peer 1: port 8080           │   │
│  │ Peer 2: port 8081           │   │
│  │ Peer 3: port 8082           │   │
│  └──────────────────────────────┘   │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ WSL2 / Ubuntu                │   │
│  │                              │   │
│  │  Controller: port 5000       │   │
│  │  (trying localhost:8080 ❌)  │   │
│  │                              │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

## The Solution

I've updated the controller to support configuring the peer host address via environment variable.

### Option 1: Automatic Setup (Recommended)

Use the startup script that automatically detects your Windows host IP:

```bash
cd ~/sdn-controller  # or wherever your controller is
chmod +x start-with-windows-host.sh
./start-with-windows-host.sh
```

The script will:
1. Automatically detect your Windows host IP
2. Test connectivity to both peer backends
3. Start the controller with the correct configuration

### Option 2: Manual Setup

1. **Find your Windows host IP from WSL:**
   ```bash
   # Method 1: From resolv.conf (WSL2)
   cat /etc/resolv.conf | grep nameserver | awk '{print $2}'

   # Method 2: Or manually check Windows IP
   # In Windows PowerShell: ipconfig
   # Look for "Ethernet adapter vEthernet (WSL)" or your main network adapter
   ```

2. **Set the environment variable and start controller:**
   ```bash
   export VICTIM_PEER_HOST=172.28.240.1  # Replace with YOUR Windows IP
   cd ~/sdn-controller
   python3 api_server.py
   ```

### Option 3: Run Everything on Windows

Alternative solution - run the controller on Windows instead of WSL:

```powershell
# In Windows PowerShell or Command Prompt
cd c:\Users\charan27\OneDrive\Desktop\SDN\sdn-controller
python api_server.py
```

This way everything runs on Windows and `localhost` works correctly.

## Testing the Fix

After starting the controller with the correct host configuration:

1. **Launch a test attack** from Peer 3

2. **Check controller terminal** - you should now see:
   ```
   DEBUG:api_server:  → Sending alert to port 8080
   INFO:api_server:  ✅ Alert sent to peer on port 8080
   DEBUG:api_server:  → Sending alert to port 8081
   INFO:api_server:  ✅ Alert sent to peer on port 8081
   ```

3. **Check peer dashboards** - Security Alerts tab should now show alerts!

## Verification Commands

### From WSL (check if Windows peers are reachable):
```bash
# Test Peer 1
curl http://172.28.240.1:8080/api/peer/status  # Replace with your Windows IP

# Test Peer 2
curl http://172.28.240.1:8081/api/peer/status

# If these work, your networking is configured correctly
```

### From Windows (check if controller is running):
```powershell
curl http://localhost:5000/api/status
```

## Common Windows Host IP Addresses in WSL

Depending on your WSL configuration, the Windows host IP is typically:
- **WSL2:** `172.x.x.1` (check `/etc/resolv.conf` for exact IP)
- **WSL1:** `127.0.0.1` might work
- **Bridge mode:** Actual Windows network IP (192.168.x.x or 10.x.x.x)

## Firewall Note

If connectivity still fails, you may need to allow WSL through Windows Firewall:

1. Open **Windows Defender Firewall**
2. Click **"Allow an app through firewall"**
3. Make sure **Python** is allowed for **Private networks**

Or temporarily test by disabling the firewall (not recommended for production).

## What Changed in the Code

I added this configuration to [api_server.py](sdn-controller/api_server.py#L130-L135):

```python
# WSL/Docker Network Configuration
# When running controller in WSL/Ubuntu and peers on Windows, use Windows host IP
# Get Windows host IP from environment variable or default to localhost
import os
VICTIM_PEER_HOST = os.environ.get('VICTIM_PEER_HOST', 'localhost')
```

And updated all notification URLs from:
```python
f'http://localhost:{port}/api/security/notify'
```

To:
```python
f'http://{VICTIM_PEER_HOST}:{port}/api/security/notify'
```

## Next Steps

1. **Stop your current controller** (Ctrl+C in WSL terminal)

2. **Start with the new script:**
   ```bash
   cd ~/sdn-controller
   ./start-with-windows-host.sh
   ```

3. **Launch a test attack** and verify alerts now appear!

The notification system will now work correctly across WSL/Windows boundary!
