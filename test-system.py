#!/usr/bin/env python3
"""
Diagnostic Test Script for Progressive Self-Destruct System
Tests all components to identify what's not working
"""

import requests
import json
import time

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_service(name, url):
    """Test if a service is running"""
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"✅ {name} is RUNNING")
            return True
        else:
            print(f"⚠️  {name} responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is NOT RUNNING - Connection refused")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {name} TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {name} ERROR: {e}")
        return False

def test_attack_launch():
    """Test launching an attack"""
    print_header("Testing Attack Launch")

    try:
        attack_data = {
            'attack_type': 'replay',
            'intensity': 'low'
        }

        print(f"Launching LOW replay attack from Peer 3...")
        response = requests.post(
            'http://localhost:8082/api/attack/launch',
            json=attack_data,
            timeout=5
        )

        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {json.dumps(response.json(), indent=2)}")

        return response.status_code == 200
    except Exception as e:
        print(f"❌ Attack launch FAILED: {e}")
        return False

def test_controller_detection():
    """Check if controller detected attacks"""
    print_header("Checking Controller Attack Detection")

    try:
        response = requests.get('http://localhost:5000/api/status/comprehensive', timeout=2)
        data = response.json()

        print(f"Total Attacks Detected: {data['attack_statistics']['total_attacks']}")
        print(f"Replay Attacks: {data['attack_statistics']['total_replay_attacks']}")
        print(f"Flood Attacks: {data['attack_statistics']['total_flood_attacks']}")
        print(f"Auth Failures: {data['attack_statistics']['total_auth_failures']}")
        print(f"\nIsolated Peers: {data['threat_landscape']['isolated_peers']}")
        print(f"Suspicious Peers: {data['threat_landscape']['suspicious_peers']}")

        print(f"\nProgressive Defense Levels:")
        print(f"  Level 1 (Monitoring): {data['progressive_defense_levels']['level_1_monitoring']}")
        print(f"  Level 2 (Session Term): {data['progressive_defense_levels']['level_2_session_termination']}")
        print(f"  Level 3 (Key Dest): {data['progressive_defense_levels']['level_3_key_destruction']}")
        print(f"  Level 4 (Isolation): {data['progressive_defense_levels']['level_4_peer_isolation']}")

        return data['attack_statistics']['total_attacks'] > 0
    except Exception as e:
        print(f"❌ Failed to get controller status: {e}")
        return False

def test_victim_alerts(port, peer_name):
    """Check if victim received alerts"""
    print(f"\nChecking {peer_name} alerts...")

    try:
        response = requests.get(f'http://localhost:{port}/api/peer/alerts', timeout=2)
        data = response.json()

        print(f"  Total Alerts: {data['count']}")
        if data['count'] > 0:
            print(f"  Recent Alerts:")
            for alert in data['alerts'][-3:]:  # Show last 3
                print(f"    - {alert['severity']}: {alert['type']}")
            return True
        else:
            print(f"  ⚠️  No alerts received yet")
            return False
    except Exception as e:
        print(f"  ❌ Failed to get alerts: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  PROGRESSIVE SELF-DESTRUCT DIAGNOSTIC TEST")
    print("="*60)

    # Test 1: Check all services
    print_header("Step 1: Testing All Services")
    services = {
        'Controller': 'http://localhost:5000/api/status',
        'Peer 1 Backend': 'http://localhost:8080/api/peer/status',
        'Peer 2 Backend': 'http://localhost:8081/api/peer/status',
        'Peer 3 Backend (Attacker)': 'http://localhost:8082/api/peer/status'
    }

    all_running = True
    for name, url in services.items():
        if not test_service(name, url):
            all_running = False

    if not all_running:
        print("\n❌ CRITICAL: Not all services are running!")
        print("Please start missing services before testing attacks.")
        return

    print("\n✅ All services are running!")

    # Test 2: Launch attack
    print_header("Step 2: Launching Test Attack")
    if not test_attack_launch():
        print("❌ Attack launch failed!")
        return

    print("\n✅ Attack launched successfully!")
    print("Waiting 2 seconds for controller to detect...")
    time.sleep(2)

    # Test 3: Check controller detection
    if not test_controller_detection():
        print("\n❌ Controller did not detect attack!")
        print("\nPossible issues:")
        print("  1. Victim peers not reporting to controller")
        print("  2. Controller monitoring endpoint not working")
        print("  3. Attack not reaching victim peers")
    else:
        print("\n✅ Controller detected attack!")

    # Test 4: Check victim notifications
    print_header("Step 3: Checking Victim Notifications")
    peer1_ok = test_victim_alerts(8080, "Peer 1")
    peer2_ok = test_victim_alerts(8081, "Peer 2")

    if not (peer1_ok or peer2_ok):
        print("\n❌ Victims did not receive alerts!")
        print("\nPossible issues:")
        print("  1. Controller not sending notifications")
        print("  2. Victim notification endpoints not working")
        print("  3. CORS or network issues")
    else:
        print("\n✅ Victims received alerts!")

    # Final summary
    print_header("Test Summary")
    print(f"{'Services Running:':<30} ✅")
    print(f"{'Attack Launch:':<30} ✅")
    print(f"{'Controller Detection:':<30} {'✅' if test_controller_detection() else '❌'}")
    print(f"{'Victim Notifications:':<30} {'✅' if (peer1_ok or peer2_ok) else '❌'}")

    print("\n" + "="*60)
    print("  For detailed logs, check:")
    print("    - Controller: Terminal running api_server.py")
    print("    - Peer logs: Check backend Python output")
    print("    - Browser: F12 Developer Console")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
