#!/usr/bin/env python3
"""
Progressive Attack Demo Script
Demonstrates all 4 levels of the progressive self-destruct mechanism
"""

import subprocess
import time
import sys

def run_attack(attack_type, intensity):
    """Run attack simulation and wait"""
    print(f"\n{'='*50}")
    print(f"LEVEL {['low', 'medium', 'high', 'critical'].index(intensity) + 1}: {intensity.upper()} SEVERITY")
    print(f"Attack Type: {attack_type.upper()}")
    print(f"Attacker: Peer 3 (Malicious Peer)")
    print(f"{'='*50}")
    
    cmd = [sys.executable, "attack_simulator.py", "--attack-type", attack_type, "--intensity", intensity, "--attacker-peer", "3"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        print(f"SUCCESS: {intensity.upper()} attack triggered successfully")
    else:
        print(f"ERROR: Attack failed: {result.stderr}")
    
    print(f"\nWaiting 10 seconds before next attack...")
    time.sleep(10)

def main():
    print("SDN PROGRESSIVE SELF-DESTRUCT DEMONSTRATION")
    print("\nThis demo will trigger all 4 levels of progressive response:")
    print("1. LOW - Monitoring & Warning")
    print("2. MEDIUM - Session Termination") 
    print("3. HIGH - Key Destruction")
    print("4. CRITICAL - Peer Isolation")
    
    input("\nPress Enter to start the demonstration...")
    
    # Level 1: Low severity - Monitoring & Warning
    run_attack("replay", "low")
    
    # Level 2: Medium severity - Session Termination
    run_attack("flooding", "medium")
    
    # Level 3: High severity - Key Destruction
    run_attack("replay", "high")
    
    # Level 4: Critical severity - Peer Isolation
    run_attack("flooding", "critical")
    
    print(f"\n{'='*50}")
    print("DEMONSTRATION COMPLETE")
    print("Check the Controller Dashboard to see all security alerts")
    print("and the progressive response system in action!")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()