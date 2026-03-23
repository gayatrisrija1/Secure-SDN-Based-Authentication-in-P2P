#!/usr/bin/env python3
"""
Session Key Diagnostic Tool
Shows the actual encryption key used in P2P sessions
"""

import requests
import json

def check_peer_session(peer_name, port):
    """Check session status and key for a peer"""
    print(f"\n{'='*60}")
    print(f"  {peer_name} (Port {port})")
    print(f"{'='*60}\n")

    try:
        # Get peer status
        response = requests.get(f'http://localhost:{port}/api/peer/status', timeout=2)
        status = response.json()

        print(f"Running: {status.get('running')}")
        print(f"Active Session: {status.get('active_session')}")
        print(f"Pseudo ID: {status.get('pseudo_id', 'N/A')}")
        print(f"Messages: {status.get('message_count', 0)}")

        if status.get('active_session'):
            print(f"\n✅ SECURE SESSION ACTIVE")
            print(f"   Encryption: AES-256")
            print(f"   Session Key: [PRESENT] ← This is the encryption key")
            print(f"   Note: The actual key bytes are not exposed via API for security")
        else:
            print(f"\n❌ NO ACTIVE SESSION")
            print(f"   Session Key: [NONE]")
            print(f"   No encryption key = Can't send/receive encrypted messages")

    except Exception as e:
        print(f"Error checking {peer_name}: {e}")

def main():
    print("\n" + "="*60)
    print("  SESSION KEY DIAGNOSTIC TOOL")
    print("="*60)
    print("\nThis tool shows whether peers have active encryption keys.")
    print("When keys are DESTROYED, peers can't communicate securely.\n")

    # Check all peers
    check_peer_session("Peer 1 (Victim)", 8080)
    check_peer_session("Peer 2 (Victim)", 8081)
    check_peer_session("Peer 3 (Attacker)", 8082)

    print("\n" + "="*60)
    print("  KEY DESTRUCTION TESTING")
    print("="*60)
    print("\nTo test key destruction:")
    print("1. Connect Peer 1 to Peer 3")
    print("2. Check status → Both show 'Session Key: [PRESENT]'")
    print("3. Peer 3 launches HIGH attack (5 attacks)")
    print("4. Check status again → Peer 1 shows 'Session Key: [NONE]'")
    print("5. Peer 1 can't send messages anymore!")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
