#!/bin/bash
# Start SDN Controller from WSL with Windows Host Configuration
# This script automatically detects the Windows host IP and configures the controller

echo "=========================================="
echo "  SDN Controller Startup (WSL → Windows)"
echo "=========================================="
echo ""

# Get Windows host IP from WSL2
# Method 1: From /etc/resolv.conf (WSL2)
WINDOWS_HOST=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}')

if [ -z "$WINDOWS_HOST" ]; then
    # Method 2: Try hostname resolution
    WINDOWS_HOST=$(hostname -I | awk '{print $1}' | sed 's/\.[0-9]*$/.1/')
fi

if [ -z "$WINDOWS_HOST" ]; then
    echo "[ERROR] Could not detect Windows host IP automatically"
    echo "Please enter your Windows host IP manually:"
    read WINDOWS_HOST
fi

echo "[INFO] Windows Host IP: $WINDOWS_HOST"
echo ""

# Verify connectivity
echo "[INFO] Testing connectivity to Windows peer backends..."
echo ""

# Test Peer 1 (port 8080)
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/$WINDOWS_HOST/8080" 2>/dev/null; then
    echo "[OK] Peer 1 (port 8080) is reachable"
else
    echo "[WARNING] Peer 1 (port 8080) is NOT reachable"
    echo "         Make sure peer-backend (peer_app.py) is running on Windows"
fi

# Test Peer 2 (port 8081)
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/$WINDOWS_HOST/8081" 2>/dev/null; then
    echo "[OK] Peer 2 (port 8081) is reachable"
else
    echo "[WARNING] Peer 2 (port 8081) is NOT reachable"
    echo "         Make sure peer-backend-2.py is running on Windows"
fi

echo ""
echo "[INFO] Starting controller with VICTIM_PEER_HOST=$WINDOWS_HOST"
echo ""
echo "=========================================="
echo ""

# Export the environment variable and start the controller
export VICTIM_PEER_HOST=$WINDOWS_HOST
python3 api_server.py
