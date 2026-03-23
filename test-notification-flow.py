#!/usr/bin/env python3
"""
Test Notification Flow - Verify alerts reach victim peers
"""

import requests
import json
import time

def test_manual_notification():
    """Manually send a notification to peers to test if endpoints work"""
    print("\n" + "="*60)
    print("  TESTING MANUAL NOTIFICATION TO PEERS")
    print("="*60 + "\n")

    test_alert = {
        'type': 'REPLAY_ATTACK',
        'severity': 'LOW',
        'attack_type': 'REPLAY_ATTACK',
        'message': '[MANUAL TEST] Testing notification delivery',
        'attacker_id': 'test_attacker_123',
        'timestamp': int(time.time()),
        'threat_score': 25.0,
        'action_recommended': 'Monitor network activity - stay alert',
        'detection_method': 'MANUAL_TEST',
        'security_state': 'SUSPICIOUS'
    }

    # Test Peer 1 (port 8080)
    print("Testing Peer 1 (port 8080)...")
    try:
        response = requests.post(
            'http://localhost:8080/api/security/notify',
            json=test_alert,
            timeout=5
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
        if response.status_code == 200:
            print("  [OK] Peer 1 notification endpoint WORKS")
        else:
            print(f"  [ERROR] Peer 1 returned error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("  [ERROR] Peer 1 NOT RUNNING - Connection refused")
    except Exception as e:
        print(f"  [ERROR] Peer 1 ERROR: {e}")

    print()

    # Test Peer 2 (port 8081)
    print("Testing Peer 2 (port 8081)...")
    try:
        response = requests.post(
            'http://localhost:8081/api/security/notify',
            json=test_alert,
            timeout=5
        )
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
        if response.status_code == 200:
            print("  [OK] Peer 2 notification endpoint WORKS")
        else:
            print(f"  [ERROR] Peer 2 returned error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("  [ERROR] Peer 2 NOT RUNNING - Connection refused")
    except Exception as e:
        print(f"  [ERROR] Peer 2 ERROR: {e}")

    print()

    # Wait a moment for alerts to be stored
    time.sleep(1)

    # Check if alerts were stored
    print("\n" + "="*60)
    print("  CHECKING IF ALERTS WERE STORED")
    print("="*60 + "\n")

    # Check Peer 1 alerts
    try:
        response = requests.get('http://localhost:8080/api/peer/alerts', timeout=2)
        data = response.json()
        print(f"Peer 1 Alert Count: {data['count']}")
        if data['count'] > 0:
            print("  [OK] Peer 1 stored the alert!")
            print(f"  Latest alert: {data['alerts'][-1]['type']} - {data['alerts'][-1]['severity']}")
        else:
            print("  [ERROR] Peer 1 did NOT store the alert")
    except Exception as e:
        print(f"  [ERROR] Failed to check Peer 1 alerts: {e}")

    print()

    # Check Peer 2 alerts
    try:
        response = requests.get('http://localhost:8081/api/peer/alerts', timeout=2)
        data = response.json()
        print(f"Peer 2 Alert Count: {data['count']}")
        if data['count'] > 0:
            print("  [OK] Peer 2 stored the alert!")
            print(f"  Latest alert: {data['alerts'][-1]['type']} - {data['alerts'][-1]['severity']}")
        else:
            print("  [ERROR] Peer 2 did NOT store the alert")
    except Exception as e:
        print(f"  [ERROR] Failed to check Peer 2 alerts: {e}")

def check_controller_config():
    """Check if victim notification is enabled in controller"""
    print("\n" + "="*60)
    print("  CHECKING CONTROLLER CONFIGURATION")
    print("="*60 + "\n")

    try:
        response = requests.get('http://localhost:5000/api/status/comprehensive', timeout=2)
        data = response.json()

        victim_notif = data.get('configuration', {}).get('victim_notification', False)

        print(f"Victim Notification Enabled: {victim_notif}")

        if victim_notif:
            print("  [OK] Victim notification is ENABLED")
        else:
            print("  [ERROR] Victim notification is DISABLED - THIS IS THE PROBLEM!")
            print("     The controller won't send notifications to peers")

        print(f"\nController Attack Statistics:")
        print(f"  Total Attacks: {data['attack_statistics']['total_attacks']}")
        print(f"  Replay Attacks: {data['attack_statistics']['total_replay_attacks']}")
        print(f"  Flood Attacks: {data['attack_statistics']['total_flood_attacks']}")

    except Exception as e:
        print(f"  [ERROR] Failed to check controller config: {e}")

def main():
    print("\n" + "="*60)
    print("  NOTIFICATION FLOW DIAGNOSTIC TEST")
    print("="*60)

    # Step 1: Check controller configuration
    check_controller_config()

    # Step 2: Test manual notifications
    test_manual_notification()

    print("\n" + "="*60)
    print("  INSTRUCTIONS:")
    print("="*60)
    print()
    print("If manual test WORKS but real attacks DON'T:")
    print("  1. Check controller terminal for 'Sending alert to port' messages")
    print("  2. Make sure controller logs '[OK] Alert sent to peer on port'")
    print("  3. Check if controller is actually calling notify_victim_peers()")
    print()
    print("If manual test FAILS:")
    print("  1. Peer backends may not be running")
    print("  2. Notification endpoint may have errors")
    print("  3. Check peer backend terminal logs")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
