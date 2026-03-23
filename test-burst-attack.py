#!/usr/bin/env python3
"""
Quick Burst Attack Tester
Sends rapid-fire attacks to test progressive defense at all levels
"""

import requests
import json
import time
import sys

def launch_burst(target_level):
    """Launch a burst attack to reach the specified level"""
    print(f"\n{'='*60}")
    print(f"  LAUNCHING BURST ATTACK - Target: {target_level}")
    print(f"{'='*60}\n")

    try:
        response = requests.post(
            'http://localhost:8082/api/attack/burst',
            headers={'Content-Type': 'application/json'},
            json={
                'attack_type': 'replay',
                'target_level': target_level
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS!")
            print(f"  Status: {data['status']}")
            print(f"  Target Level: {data['target_level']}")
            print(f"  Attacks Sent: {data['attacks_sent']}")
            print(f"  Message: {data['message']}")
            print(f"\nCheck controller and peer logs for progressive defense activation!")
            return True
        else:
            print(f"✗ FAILED!")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"✗ ERROR: Cannot connect to Peer 3 (port 8082)")
        print(f"  Make sure Peer 3 backend is running!")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

def check_alerts():
    """Check if alerts were received by victim peers"""
    print(f"\n{'='*60}")
    print(f"  CHECKING VICTIM PEER ALERTS")
    print(f"{'='*60}\n")

    # Check Peer 1
    try:
        response = requests.get('http://localhost:8080/api/peer/alerts', timeout=2)
        data = response.json()
        print(f"Peer 1 Alerts: {data['count']}")
        if data['count'] > 0:
            latest = data['alerts'][-1]
            print(f"  Latest: {latest['type']} - {latest['severity']}")
    except Exception as e:
        print(f"Peer 1: Could not check alerts - {e}")

    # Check Peer 2
    try:
        response = requests.get('http://localhost:8081/api/peer/alerts', timeout=2)
        data = response.json()
        print(f"Peer 2 Alerts: {data['count']}")
        if data['count'] > 0:
            latest = data['alerts'][-1]
            print(f"  Latest: {latest['type']} - {latest['severity']}")
    except Exception as e:
        print(f"Peer 2: Could not check alerts - {e}")

def clear_alerts():
    """Clear previous alerts for clean testing"""
    print(f"\n{'='*60}")
    print(f"  CLEARING PREVIOUS ALERTS")
    print(f"{'='*60}\n")

    try:
        requests.delete('http://localhost:8080/api/peer/alerts')
        print("✓ Peer 1 alerts cleared")
    except:
        print("✗ Peer 1 alerts not cleared")

    try:
        requests.delete('http://localhost:8081/api/peer/alerts')
        print("✓ Peer 2 alerts cleared")
    except:
        print("✗ Peer 2 alerts not cleared")

def main():
    print("\n" + "="*60)
    print("  BURST ATTACK TESTING TOOL")
    print("="*60)

    if len(sys.argv) > 1:
        # Level specified as command line argument
        level = sys.argv[1].upper()
        if level not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            print(f"\nInvalid level: {level}")
            print("Valid levels: LOW, MEDIUM, HIGH, CRITICAL")
            print("\nUsage:")
            print("  python test-burst-attack.py CRITICAL")
            print("  python test-burst-attack.py HIGH")
            print("  python test-burst-attack.py MEDIUM")
            return

        # Clear previous alerts
        clear_alerts()
        time.sleep(1)

        # Launch burst attack
        success = launch_burst(level)

        if success:
            # Wait for controller to process
            print("\nWaiting 2 seconds for controller to process...")
            time.sleep(2)

            # Check alerts
            check_alerts()
    else:
        # Interactive mode
        print("\nAvailable Tests:")
        print("  1. LOW      - 2 attacks  (Monitoring only)")
        print("  2. MEDIUM   - 3 attacks  (Session termination)")
        print("  3. HIGH     - 5 attacks  (Key destruction)")
        print("  4. CRITICAL - 8 attacks  (Peer isolation)")
        print("  5. Clear alerts and exit")
        print("  0. Exit")

        while True:
            choice = input("\nSelect test (0-5): ").strip()

            if choice == '0':
                break
            elif choice == '1':
                clear_alerts()
                time.sleep(1)
                launch_burst('LOW')
                time.sleep(2)
                check_alerts()
            elif choice == '2':
                clear_alerts()
                time.sleep(1)
                launch_burst('MEDIUM')
                time.sleep(2)
                check_alerts()
            elif choice == '3':
                clear_alerts()
                time.sleep(1)
                launch_burst('HIGH')
                time.sleep(2)
                check_alerts()
            elif choice == '4':
                clear_alerts()
                time.sleep(1)
                launch_burst('CRITICAL')
                time.sleep(2)
                check_alerts()
            elif choice == '5':
                clear_alerts()
            else:
                print("Invalid choice!")

    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60)
    print("\nCheck controller terminal for progressive defense logs!")
    print("Check peer 1 & 2 Security Alerts tabs for notifications!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
