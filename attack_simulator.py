#!/usr/bin/env python3
"""
Attack Simulation Scripts for SDN Security Testing
Simulates various attack patterns to test progressive self-destruct mechanism
"""

import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description='SDN Attack Simulator')
    parser.add_argument('--attack-type', choices=['replay', 'flooding'], 
                       required=True, help='Attack type to simulate')
    parser.add_argument('--intensity', choices=['low', 'medium', 'high', 'critical'], 
                       required=True, help='Attack intensity level')
    parser.add_argument('--attacker-peer', default='3', choices=['1', '2', '3'],
                       help='Which peer is the attacker (default: 3)')
    parser.add_argument('--controller', default='http://localhost:5000',
                       help='SDN Controller API URL')
    
    args = parser.parse_args()
    
    # Get attacker peer info
    peer_ports = {'1': 8080, '2': 8081, '3': 8082}
    attacker_port = peer_ports[args.attacker_peer]
    
    # Get attacker's pseudo_id from their backend
    try:
        peer_response = requests.get(f'http://localhost:{attacker_port}/api/peer/status', timeout=3)
        if peer_response.status_code == 200:
            attacker_pseudo_id = peer_response.json().get('pseudo_id', f'peer_{args.attacker_peer}')
        else:
            attacker_pseudo_id = f'peer_{args.attacker_peer}'
    except:
        attacker_pseudo_id = f'peer_{args.attacker_peer}'
    
    # Map intensity to severity
    severity_map = {
        'low': 'LOW',
        'medium': 'MEDIUM', 
        'high': 'HIGH',
        'critical': 'CRITICAL'
    }
    
    severity = severity_map[args.intensity]
    
    # Create attack alert with real peer info
    alert_data = {
        'peer_mac': f'02:00:00:00:00:0{args.attacker_peer}',  # Real peer MAC
        'alert_type': f'{args.attack_type.upper()}_ATTACK',
        'severity': severity,
        'message': f'{args.attack_type.title()} attack detected from Peer {args.attacker_peer} ({attacker_pseudo_id[:8]}...) - {severity} severity',
        'action_taken': 'monitoring' if severity == 'LOW' else 'blocking',
        'attacker_peer_id': attacker_pseudo_id,
        'attacker_port': attacker_port
    }
    
    try:
        print(f"Simulating {args.attack_type} attack from Peer {args.attacker_peer} with {args.intensity} intensity...")
        print(f"Attacker: {attacker_pseudo_id} on port {attacker_port}")
        
        response = requests.post(f'{args.controller}/api/security/alert', 
                               json=alert_data, timeout=5)
        
        if response.status_code == 200:
            print(f"Attack simulation successful - {severity} alert created")
            print(f"Peer {args.attacker_peer} identified as attacker")
            print(f"Check Controller Dashboard for progressive response")
            
            # For critical attacks, also mark the peer as isolated
            if severity == 'CRITICAL':
                try:
                    isolation_data = {
                        'peer_id': attacker_pseudo_id,
                        'action': 'isolate',
                        'reason': 'Critical security threat detected'
                    }
                    requests.post(f'{args.controller}/api/peer/isolate', json=isolation_data, timeout=3)
                    print(f"Peer {args.attacker_peer} has been ISOLATED from the network")
                except:
                    pass
        else:
            print(f"Failed to create alert: {response.status_code}")
            
    except Exception as e:
        print(f"Attack simulation failed: {e}")

if __name__ == '__main__':
    main()