#!/usr/bin/env python3
"""
SDN Security System - Health Check Script
Verifies all components are running and communicating properly
"""

import requests
import socket
import time
import json
from datetime import datetime

def check_component(name, url, timeout=5):
    """Check if a component is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name}: RUNNING (Status: {response.status_code})")
            return True
        else:
            print(f"⚠️  {name}: RESPONDING but status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: NOT RESPONDING ({str(e)})")
        return False

def check_port(name, host, port):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✅ {name}: Port {port} OPEN")
            return True
        else:
            print(f"❌ {name}: Port {port} CLOSED")
            return False
    except Exception as e:
        print(f"❌ {name}: Port check failed ({str(e)})")
        return False

def main():
    print("=" * 60)
    print("SDN Security System - Health Check")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Component health checks
    components = [
        ("Controller Backend API", "http://localhost:5000/api/status"),
        ("Peer Backend API", "http://localhost:8080/api/peer/status"),
        ("Controller Dashboard", "http://localhost:3001"),
        ("Peer Dashboard", "http://localhost:3000"),
    ]
    
    print("🔍 Checking Component Health...")
    print("-" * 40)
    
    results = []
    for name, url in components:
        results.append(check_component(name, url))
    
    print()
    print("🔍 Checking Port Availability...")
    print("-" * 40)
    
    ports = [
        ("SDN Controller API", "localhost", 5000),
        ("Peer Backend", "localhost", 8080),
        ("Controller UI", "localhost", 3001),
        ("Peer UI", "localhost", 3000),
    ]
    
    for name, host, port in ports:
        results.append(check_port(name, host, port))
    
    print()
    print("📊 System Status Summary")
    print("-" * 40)
    
    healthy_count = sum(results)
    total_count = len(results)
    
    if healthy_count == total_count:
        print(f"🎉 ALL SYSTEMS OPERATIONAL ({healthy_count}/{total_count})")
        print("✅ Ready for testing!")
    elif healthy_count >= total_count * 0.75:
        print(f"⚠️  MOSTLY OPERATIONAL ({healthy_count}/{total_count})")
        print("🔧 Some components need attention")
    else:
        print(f"❌ SYSTEM ISSUES ({healthy_count}/{total_count})")
        print("🚨 Multiple components not responding")
    
    print()
    print("📋 Next Steps:")
    if healthy_count == total_count:
        print("1. Open Controller Dashboard: http://localhost:3001")
        print("2. Open Peer Dashboard: http://localhost:3000")
        print("3. Follow TESTING-GUIDE.md for complete testing")
    else:
        print("1. Check which components failed above")
        print("2. Restart failed components")
        print("3. Re-run this health check")
        print("4. Refer to installation-guide.md if needed")

if __name__ == "__main__":
    main()