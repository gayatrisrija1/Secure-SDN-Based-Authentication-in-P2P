#!/usr/bin/env python3
"""
Simplified SDN Security Controller (Ryu-free version)
For demo purposes when Ryu has compatibility issues
"""

import socket
import threading
import time
import json
from collections import defaultdict
import logging

class SimpleSDNController:
    def __init__(self):
        self.peers = {}
        self.flows = {}
        self.security_events = []
        self.running = False
        
        # Security monitoring
        self.packet_counts = defaultdict(int)
        self.suspicious_peers = set()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        """Start the simplified controller"""
        self.running = True
        self.logger.info("Simple SDN Security Controller started")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_network)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Start packet capture simulation
        capture_thread = threading.Thread(target=self._simulate_packet_capture)
        capture_thread.daemon = True
        capture_thread.start()
        
        return True
        
    def _monitor_network(self):
        """Monitor network for security events"""
        while self.running:
            try:
                # Simulate network monitoring
                current_time = time.time()
                
                # Check for suspicious activity
                for peer_id, count in self.packet_counts.items():
                    if count > 100:  # Threshold for suspicious activity
                        if peer_id not in self.suspicious_peers:
                            self.suspicious_peers.add(peer_id)
                            self._log_security_event("SUSPICIOUS_ACTIVITY", peer_id, "High packet rate detected")
                            
                # Reset counters periodically
                if int(current_time) % 30 == 0:
                    self.packet_counts.clear()
                    
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                
    def _simulate_packet_capture(self):
        """Simulate packet capture for demo"""
        while self.running:
            try:
                # Listen for UDP packets (simulated network traffic)
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('0.0.0.0', 9998))  # Different port from peer discovery
                sock.settimeout(1)
                
                while self.running:
                    try:
                        data, addr = sock.recvfrom(1024)
                        self._process_packet(data, addr)
                    except socket.timeout:
                        continue
                        
            except Exception as e:
                self.logger.error(f"Packet capture error: {e}")
                
    def _process_packet(self, data, addr):
        """Process captured packet"""
        try:
            # Increment packet count for source
            source_ip = addr[0]
            self.packet_counts[source_ip] += 1
            
            # Try to parse as JSON (our protocol)
            try:
                packet = json.loads(data.decode('utf-8'))
                packet_type = packet.get('type', 'UNKNOWN')
                
                # Log different packet types
                if packet_type in ['FLOOD_PACKET', 'AUTH_REQUEST']:
                    self._log_security_event("PACKET_DETECTED", source_ip, f"{packet_type} from {source_ip}")
                    
            except:
                # Not JSON, treat as raw packet
                pass
                
        except Exception as e:
            self.logger.error(f"Packet processing error: {e}")
            
    def _log_security_event(self, event_type, peer_id, message):
        """Log security event"""
        event = {
            'timestamp': time.time(),
            'event_type': event_type,
            'peer_id': peer_id,
            'message': message
        }
        
        self.security_events.append(event)
        self.logger.warning(f"Security Event: {event_type} - {message}")
        
        # Keep only last 100 events
        if len(self.security_events) > 100:
            self.security_events = self.security_events[-100:]
            
    def get_status(self):
        """Get controller status"""
        return {
            'active': self.running,
            'peers_monitored': len(self.peers),
            'security_events': len(self.security_events),
            'suspicious_peers': len(self.suspicious_peers)
        }
        
    def simulate_attack_detection(self, attack_type, target_peer):
        """Simulate attack detection for demo"""
        severity_map = {
            'replay': 'MEDIUM',
            'flood': 'HIGH', 
            'progressive': 'CRITICAL'
        }
        
        severity = severity_map.get(attack_type, 'LOW')
        
        self._log_security_event(
            f"{attack_type.upper()}_ATTACK_DETECTED",
            target_peer,
            f"{attack_type.title()} attack detected against {target_peer}"
        )
        
        # Simulate progressive response
        if severity == 'MEDIUM':
            self._log_security_event("SESSION_TERMINATION", target_peer, "Session terminated due to replay attack")
        elif severity == 'HIGH':
            self._log_security_event("KEY_DESTRUCTION", target_peer, "Encryption keys destroyed due to flood attack")
        elif severity == 'CRITICAL':
            self._log_security_event("PEER_ISOLATION", target_peer, "Peer isolated due to critical attack")
            
        return True

def main():
    """Main function to run the controller"""
    controller = SimpleSDNController()
    
    try:
        controller.start()
        print("Simple SDN Controller running. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nController stopped by user.")
        controller.running = False

if __name__ == '__main__':
    main()