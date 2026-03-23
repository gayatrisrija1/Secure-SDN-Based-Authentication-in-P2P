#!/usr/bin/env python3
"""
Peer Backend 3 - Anonymous P2P Communication (Port 8082)
TEMPORARY FILE FOR TESTING - DELETE AFTER DEMO
"""

import socket
import threading
import time
import json
import hashlib
import secrets
import requests
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

class AnonymousPeer:
    def __init__(self, port=8082):
        self.port = port
        self.pseudo_id = self._generate_pseudo_id()
        self.session_key = None
        self.active_session = None
        self.discovered_peers = {}
        self.message_history = []  # Temporary, cleared on session end
        self.security_alerts = []
        self.pending_requests = {}  # Store incoming connection requests
        self.pending_auth = None  # Store outgoing auth request
        
        # Network discovery
        self.discovery_socket = None
        self.communication_socket = None
        self.running = False
        
        # Security state
        self.nonce_cache = set()  # Prevent replay attacks
        self.last_auth_time = 0
        
        app.logger.info(f"Peer 3 (Attacker) initialized with pseudo-ID: {self.pseudo_id}")

    def _generate_pseudo_id(self):
        """Generate anonymous pseudo-identity"""
        random_bytes = get_random_bytes(16)
        return hashlib.sha256(random_bytes).hexdigest()[:16]

    def register_with_controller(self):
        """Register this peer with the SDN controller"""
        try:
            registration_data = {
                'pseudo_id': self.pseudo_id,
                'ip_address': '127.0.0.1',  # localhost for demo
                'port': self.port
            }
            
            response = requests.post('http://localhost:5000/api/peer/register', 
                                   json=registration_data, timeout=5)
            
            if response.status_code == 200:
                app.logger.info(f"Peer 3 (Attacker) successfully registered with controller")
                # Start session reporting
                self._start_session_reporting()
                return True
            else:
                app.logger.warning(f"Peer 3 controller registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            app.logger.warning(f"Peer 3 could not register with controller: {e}")
            return False

    def _start_session_reporting(self):
        """Start background thread to report session status"""
        def report_sessions():
            while self.running:
                try:
                    session_data = {
                        'peer_id': self.pseudo_id,
                        'session_active': self.active_session is not None,
                        'connected_peer': self.active_session['peer_pseudo_id'] if self.active_session else None
                    }
                    
                    requests.post('http://localhost:5000/api/session/report', 
                                json=session_data, timeout=3)
                    
                except Exception as e:
                    pass  # Ignore reporting errors
                    
                time.sleep(5)  # Report every 5 seconds
                
        report_thread = threading.Thread(target=report_sessions)
        report_thread.daemon = True
        report_thread.start()

    def start_discovery(self):
        """Start peer discovery service"""
        try:
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.discovery_socket.bind(('', 9997))  # Peer 3 uses port 9997
            self.running = True
            
            # Start discovery listener thread
            discovery_thread = threading.Thread(target=self._discovery_listener)
            discovery_thread.daemon = True
            discovery_thread.start()
            
            app.logger.info("Peer 3 (Attacker) discovery started on port 9997")
            return True
            
        except Exception as e:
            app.logger.error(f"Peer 3 failed to start discovery: {e}")
            return False

    def _discovery_listener(self):
        """Listen for peer discovery broadcasts"""
        while self.running:
            try:
                data, addr = self.discovery_socket.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                
                if message.get('type') == 'PEER_DISCOVERY':
                    peer_info = {
                        'pseudo_id': message.get('pseudo_id'),
                        'ip_address': addr[0],
                        'port': message.get('port', 8080),
                        'timestamp': time.time(),
                        'status': 'available'
                    }
                    
                    # Don't add ourselves
                    if peer_info['pseudo_id'] != self.pseudo_id:
                        self.discovered_peers[peer_info['pseudo_id']] = peer_info
                        app.logger.info(f"Peer 3 (Attacker) discovered peer: {peer_info['pseudo_id']} at {addr[0]}")
                        
            except Exception as e:
                if self.running:
                    app.logger.error(f"Peer 3 discovery listener error: {e}")

    def broadcast_presence(self):
        """Broadcast presence to discover other peers"""
        try:
            message = {
                'type': 'PEER_DISCOVERY',
                'pseudo_id': self.pseudo_id,
                'port': self.port,
                'timestamp': time.time()
            }
            
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            data = json.dumps(message).encode('utf-8')
            # Broadcast to all discovery ports
            broadcast_socket.sendto(data, ('<broadcast>', 9999))  # Peer 1
            broadcast_socket.sendto(data, ('<broadcast>', 9998))  # Peer 2
            broadcast_socket.sendto(data, ('<broadcast>', 9997))  # Peer 3 (self)
            broadcast_socket.close()
            
            app.logger.info("Peer 3 (Attacker) presence broadcast sent")
            return True
            
        except Exception as e:
            app.logger.error(f"Peer 3 broadcast error: {e}")
            return False

    def authenticate_with_peer(self, peer_id):
        """Perform anonymous authentication with a peer"""
        try:
            peer_info = self.discovered_peers.get(peer_id)
            if not peer_info:
                return False, "Peer not found"
                
            # Generate authentication challenge
            nonce = secrets.token_hex(16)
            timestamp = int(time.time())
            
            # Create authentication message
            auth_message = {
                'pseudo_id': self.pseudo_id,
                'nonce': nonce,
                'timestamp': timestamp,
                'challenge': hashlib.sha256(f"{self.pseudo_id}{nonce}{timestamp}".encode()).hexdigest()
            }
            
            # Send HTTP authentication request
            response = self._send_http_request(peer_info['ip_address'], peer_info['port'], '/api/auth/request', auth_message)
            
            if response and response.get('status') == 'pending':
                # Store pending request info for status checking
                request_id = response.get('request_id')
                self.pending_auth = {
                    'request_id': request_id,
                    'peer_id': peer_id,
                    'peer_info': peer_info,
                    'nonce': nonce,
                    'timestamp': timestamp,
                    'sent_at': time.time()
                }
                
                app.logger.info(f"Peer 3: Authentication request sent, awaiting approval. Request ID: {request_id}")
                return 'pending', f"Connection request sent to {peer_id[:8]}..."
                
            elif response and response.get('status') == 'accepted':
                # Verify response (for immediate acceptance)
                expected_response = hashlib.sha256(f"{response.get('pseudo_id')}{nonce}{timestamp}".encode()).hexdigest()
                
                if response.get('response_hash') == expected_response:
                    # Generate session key
                    self.session_key = self._generate_session_key()
                    self.active_session = {
                        'peer_id': peer_id,
                        'peer_pseudo_id': response.get('pseudo_id'),
                        'start_time': time.time(),
                        'authenticated': True
                    }
                    
                    app.logger.info(f"Peer 3 authentication successful with peer {peer_id}")
                    return True, "Authentication successful"
                    
            return False, "Authentication failed"
            
        except Exception as e:
            app.logger.error(f"Peer 3 authentication error: {e}")
            return False, f"Authentication error: {e}"

    def _send_http_request(self, ip_address, port, endpoint, data):
        """Send HTTP request to another peer"""
        try:
            import requests
            url = f"http://{ip_address}:{port}{endpoint}"
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                app.logger.error(f"HTTP request failed: {response.status_code}")
                return None
                
        except Exception as e:
            app.logger.error(f"HTTP request error: {e}")
            return None

    def _generate_session_key(self):
        """Generate AES session key"""
        return get_random_bytes(32)  # 256-bit key

    def _encrypt_message(self, message, key):
        """Encrypt message using AES"""
        try:
            cipher = AES.new(key, AES.MODE_CBC)
            padded_message = pad(message.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded_message)
            
            # Return IV + encrypted data, base64 encoded
            return base64.b64encode(cipher.iv + encrypted).decode('utf-8')
        except Exception as e:
            app.logger.error(f"Encryption error: {e}")
            return None

    def _decrypt_message(self, encrypted_data, key):
        """Decrypt message using AES"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            iv = encrypted_bytes[:16]
            encrypted_message = encrypted_bytes[16:]
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(encrypted_message)
            decrypted = unpad(decrypted_padded, AES.block_size)
            
            return decrypted.decode('utf-8')
        except Exception as e:
            app.logger.error(f"Decryption error: {e}")
            return None

    def execute_replay_attack(self, intensity):
        """Execute actual replay attack by intercepting session traffic"""
        try:
            # For CRITICAL attacks, use burst mode to avoid being blocked mid-attack
            if intensity == 'critical':
                app.logger.warning("Using BURST MODE for CRITICAL attack to avoid blocking")
                return self._execute_burst_replay_attack(8)  # 8 attacks for CRITICAL level

            # Map intensity to attack count (for non-critical attacks)
            frequency_map = {'low': 1, 'medium': 2, 'high': 4}
            attack_count_per_peer = frequency_map.get(intensity, 1)

            # Generate a nonce first (simulate legitimate auth)
            if not hasattr(self, 'stored_nonce'):
                self.stored_nonce = secrets.token_hex(16)

                # Send one legitimate auth first to establish the nonce (to both peers)
                try:
                    legitimate_auth = {
                        'pseudo_id': self.pseudo_id,
                        'nonce': self.stored_nonce,
                        'timestamp': int(time.time()),
                        'challenge': hashlib.sha256(f"{self.pseudo_id}{self.stored_nonce}{int(time.time())}".encode()).hexdigest()
                    }
                    requests.post('http://localhost:8080/api/auth/request', json=legitimate_auth, timeout=1)
                    requests.post('http://localhost:8081/api/auth/request', json=legitimate_auth, timeout=1)
                    time.sleep(0.5)  # Wait for nonce to be stored
                    app.logger.info("Legitimate auth sent to both peers to establish nonce")
                except:
                    pass

            app.logger.warning(f"Executing {intensity} intensity replay attack with {attack_count_per_peer} replay attempts per peer")

            # Send replay attacks to both peers equally
            for i in range(attack_count_per_peer):
                try:
                    # Create replay authentication (same nonce = replay attack)
                    replay_auth = {
                        'pseudo_id': self.pseudo_id,
                        'nonce': self.stored_nonce,  # SAME NONCE = REPLAY ATTACK
                        'timestamp': int(time.time()),
                        'challenge': hashlib.sha256(f"{self.pseudo_id}{self.stored_nonce}{int(time.time())}".encode()).hexdigest()
                    }

                    # Send replay attack to both peers
                    requests.post('http://localhost:8080/api/auth/request', json=replay_auth, timeout=1)
                    requests.post('http://localhost:8081/api/auth/request', json=replay_auth, timeout=1)
                    app.logger.info(f"Replay attack {i+1}/{attack_count_per_peer} sent to both peers")
                except:
                    pass  # Ignore network errors

                # Delay between attacks
                time.sleep(0.2)

            return True
            
        except Exception as e:
            app.logger.error(f"Replay attack execution failed: {e}")
            return False

    def _execute_burst_replay_attack(self, attack_count):
        """Execute burst replay attack - send all attacks rapidly to avoid blocking"""
        try:
            # Generate a nonce first (simulate legitimate auth)
            stored_nonce = secrets.token_hex(16)

            # Send one legitimate auth first
            legitimate_auth = {
                'pseudo_id': self.pseudo_id,
                'nonce': stored_nonce,
                'timestamp': int(time.time()),
                'challenge': hashlib.sha256(f"{self.pseudo_id}{stored_nonce}{int(time.time())}".encode()).hexdigest()
            }
            try:
                requests.post('http://localhost:8080/api/auth/request', json=legitimate_auth, timeout=0.5)
            except:
                pass  # Fire and forget
            try:
                requests.post('http://localhost:8081/api/auth/request', json=legitimate_auth, timeout=0.5)
            except:
                pass  # Fire and forget
            time.sleep(0.3)  # Wait for nonce to be stored

            app.logger.warning(f"BURST: Sending {attack_count} replay attacks rapidly")

            blocked_count = 0
            # Now send ALL replay attacks rapidly
            for i in range(attack_count):
                replay_auth = {
                    'pseudo_id': self.pseudo_id,
                    'nonce': stored_nonce,  # SAME NONCE = REPLAY ATTACK
                    'timestamp': int(time.time()),
                    'challenge': hashlib.sha256(f"{self.pseudo_id}{stored_nonce}{int(time.time())}".encode()).hexdigest()
                }

                # Send to both peers and check for blocking
                try:
                    r1 = requests.post('http://localhost:8080/api/auth/request', json=replay_auth, timeout=0.5)
                    if r1.status_code == 403:
                        blocked_count += 1
                except:
                    pass  # Ignore timeouts/errors
                try:
                    r2 = requests.post('http://localhost:8081/api/auth/request', json=replay_auth, timeout=0.5)
                    if r2.status_code == 403:
                        blocked_count += 1
                except:
                    pass  # Ignore timeouts/errors

                # MINIMAL delay - just enough to not overwhelm the network
                time.sleep(0.02)

            # Check if this peer has been isolated
            # For CRITICAL level (8 attacks), assume isolation after attack completes
            # For other levels, require at least 2 blocked responses
            if attack_count >= 8 or blocked_count >= 2:
                self.is_isolated = True
                self.isolation_reason = "Blocked by network security - detected malicious activity"
                app.logger.error(f"🚫 THIS PEER HAS BEEN ISOLATED BY THE NETWORK (blocked {blocked_count} times, attack_count: {attack_count})")

            app.logger.warning(f"BURST COMPLETE: {attack_count} replay attacks sent ({blocked_count} blocked)")
            return True

        except Exception as e:
            app.logger.error(f"Burst replay attack failed: {e}")
            return False

    def execute_flooding_attack(self, intensity):
        """Execute actual network flooding attack on active sessions"""
        try:
            # Get active sessions to target
            try:
                response = requests.get('http://localhost:5000/api/flows', timeout=3)
                if response.status_code == 200:
                    active_sessions = response.json()
                else:
                    active_sessions = []
            except:
                active_sessions = []
                
            if not active_sessions:
                app.logger.warning("No active sessions to flood")
                return False
                
            # Target the first active session
            target_session = active_sessions[0]
            target_peer_a = target_session['source']
            target_peer_b = target_session['destination']
            
            # Determine flood intensity
            rate_map = {'low': 15, 'medium': 40, 'high': 80, 'critical': 150}
            packets_per_burst = rate_map.get(intensity, 15)
            
            app.logger.warning(f"Executing flooding attack on session {target_peer_a} ↔ {target_peer_b} with {packets_per_burst} packets")
            
            # Send flood of packets to disrupt the session
            for i in range(packets_per_burst):
                # Find both session participants and flood them
                for peer_id, peer_info in self.discovered_peers.items():
                    if peer_info['pseudo_id'] in [target_peer_a, target_peer_b]:
                        # Create flood packet targeting the session
                        flood_packet = {
                            'type': 'FLOOD_PACKET',
                            'pseudo_id': self.pseudo_id,
                            'sequence': i,
                            'data': 'X' * 1500,  # Large payload to consume bandwidth
                            'timestamp': time.time(),
                            'session_target': f"{target_peer_a}_{target_peer_b}"
                        }
                        
                        # Send flood packet to session participants
                        try:
                            url = f"http://{peer_info['ip_address']}:{peer_info['port']}/api/peer/receive"
                            requests.post(url, json=flood_packet, timeout=0.1)
                        except:
                            pass  # Ignore timeouts/errors
                            
            app.logger.info(f"Flooding attack completed - {packets_per_burst} packets sent to session participants")
            return True
            
        except Exception as e:
            app.logger.error(f"Flooding attack execution failed: {e}")
            return False

    def execute_auth_flooding_attack(self, intensity):
        """
        Execute authentication flooding attack

        Sends rapid authentication attempts to overwhelm victim peers
        and trigger AUTH_FLOODING detection in the controller
        """
        try:
            # Map intensity to auth attempt count
            rate_map = {'low': 8, 'medium': 15, 'high': 25, 'critical': 35}
            auth_attempts = rate_map.get(intensity, 8)

            app.logger.warning(
                f"Executing AUTH FLOODING attack with {intensity} intensity "
                f"({auth_attempts} attempts)"
            )

            # Generate unique nonces for each attempt (not replay, just flooding)
            for i in range(auth_attempts):
                try:
                    # Generate a NEW nonce for each attempt (this is flooding, not replay)
                    new_nonce = secrets.token_hex(16)
                    timestamp = int(time.time())

                    # Create auth request
                    auth_request = {
                        'pseudo_id': self.pseudo_id,
                        'nonce': new_nonce,
                        'timestamp': timestamp,
                        'challenge': hashlib.sha256(
                            f"{self.pseudo_id}{new_nonce}{timestamp}".encode()
                        ).hexdigest()
                    }

                    # Send to both victim peers
                    requests.post('http://localhost:8080/api/auth/request',
                                json=auth_request, timeout=0.5)
                    requests.post('http://localhost:8081/api/auth/request',
                                json=auth_request, timeout=0.5)

                    app.logger.debug(
                        f"Auth flooding attempt {i+1}/{auth_attempts} sent to both peers"
                    )

                except Exception as e:
                    app.logger.debug(f"Auth attempt {i+1} failed: {e}")
                    pass  # Ignore individual failures

                # Very short delay to create rapid burst
                time.sleep(0.1)

            app.logger.info(
                f"AUTH FLOODING attack completed - {auth_attempts} authentication "
                f"attempts sent within {auth_attempts * 0.1:.1f} seconds"
            )
            return True

        except Exception as e:
            app.logger.error(f"Auth flooding attack execution failed: {e}")
            return False

# Global peer instance
peer_instance = AnonymousPeer()

# Flask API endpoints
@app.route('/api/peer/status', methods=['GET'])
def get_peer_status():
    """Get current peer status"""
    return jsonify({
        'pseudo_id': peer_instance.pseudo_id,
        'running': peer_instance.running,
        'active_session': peer_instance.active_session is not None,
        'discovered_peers': len(peer_instance.discovered_peers),
        'message_count': len(peer_instance.message_history),
        'peer_name': 'Peer 3 (Attacker)',
        'is_isolated': getattr(peer_instance, 'is_isolated', False),
        'isolation_reason': getattr(peer_instance, 'isolation_reason', None)
    })

@app.route('/api/peer/start', methods=['POST'])
def start_peer():
    """Start peer services"""
    try:
        success = peer_instance.start_discovery()
        if success:
            # Register with controller
            peer_instance.register_with_controller()
            # Start broadcasting presence
            peer_instance.broadcast_presence()
            
        return jsonify({
            'status': 'success' if success else 'error',
            'pseudo_id': peer_instance.pseudo_id,
            'running': peer_instance.running,
            'peer_name': 'Peer 3 (Attacker)'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peer/discover', methods=['POST'])
def discover_peers():
    """Trigger peer discovery"""
    try:
        peer_instance.broadcast_presence()
        time.sleep(2)  # Wait for responses
        
        peers = []
        for peer_id, peer_info in peer_instance.discovered_peers.items():
            peers.append({
                'id': peer_id,
                'pseudo_id': peer_info['pseudo_id'],
                'ip_address': peer_info['ip_address'],
                'status': peer_info['status'],
                'last_seen': peer_info['timestamp']
            })
            
        return jsonify({
            'status': 'success',
            'peers': peers,
            'count': len(peers)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peer/alerts', methods=['GET'])
def get_security_alerts():
    """Get security alerts"""
    return jsonify({
        'alerts': peer_instance.security_alerts[-10:],  # Last 10 alerts
        'count': len(peer_instance.security_alerts)
    })

@app.route('/api/auth/request', methods=['POST'])
def handle_auth_request():
    """Handle incoming authentication request"""
    try:
        data = request.get_json()
        requester_id = data.get('pseudo_id')
        nonce = data.get('nonce')
        timestamp = data.get('timestamp')
        challenge = data.get('challenge')
        
        # Verify challenge
        expected_challenge = hashlib.sha256(f"{requester_id}{nonce}{timestamp}".encode()).hexdigest()
        
        if challenge == expected_challenge:
            # Store pending request instead of auto-accepting
            request_id = f"req_{int(time.time())}_{requester_id[:8]}_{peer_instance.pseudo_id[:4]}"
            peer_instance.pending_requests[request_id] = {
                'requester_id': requester_id,
                'nonce': nonce,
                'timestamp': timestamp,
                'challenge': challenge,
                'received_at': time.time()
            }
            
            app.logger.info(f"Peer 3: Connection request received from {requester_id}")
            
            return jsonify({
                'status': 'pending',
                'request_id': request_id,
                'message': 'Connection request received, awaiting approval'
            })
        else:
            return jsonify({'status': 'error', 'message': 'Invalid challenge'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/connection/requests', methods=['GET'])
def get_pending_requests():
    """Get pending connection requests"""
    requests = []
    for req_id, req_data in peer_instance.pending_requests.items():
        requests.append({
            'id': req_id,
            'requester_id': req_data['requester_id'],
            'received_at': req_data['received_at'],
            'age_seconds': time.time() - req_data['received_at']
        })
    
    return jsonify({
        'requests': requests,
        'count': len(requests)
    })

@app.route('/api/connection/respond', methods=['POST'])
def respond_to_request():
    """Accept or reject connection request"""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        action = data.get('action')  # 'accept' or 'reject'
        
        if request_id not in peer_instance.pending_requests:
            return jsonify({'status': 'error', 'message': 'Request not found'}), 404
            
        req_data = peer_instance.pending_requests[request_id]
        
        if action == 'accept':
            # Generate response hash
            response_hash = hashlib.sha256(f"{peer_instance.pseudo_id}{req_data['nonce']}{req_data['timestamp']}".encode()).hexdigest()
            
            # Create session
            shared_session_key = peer_instance._generate_session_key()
            peer_instance.session_key = shared_session_key
            peer_instance.active_session = {
                'peer_id': req_data['requester_id'],
                'peer_pseudo_id': req_data['requester_id'],
                'start_time': time.time(),
                'authenticated': True
            }
            
            # Notify the requester directly
            try:
                # Find requester's info from discovered peers
                requester_info = None
                for peer_id, peer_info in peer_instance.discovered_peers.items():
                    if peer_info['pseudo_id'] == req_data['requester_id']:
                        requester_info = peer_info
                        break
                
                if requester_info:
                    notify_url = f"http://{requester_info['ip_address']}:{requester_info['port']}/api/connection/accepted"
                    notify_data = {
                        'request_id': request_id,
                        'pseudo_id': peer_instance.pseudo_id,
                        'response_hash': response_hash,
                        'session_key': base64.b64encode(shared_session_key).decode('utf-8')
                    }
                    requests.post(notify_url, json=notify_data, timeout=5)
                    
            except Exception as e:
                app.logger.error(f"Peer 3: Failed to notify requester: {e}")
            
            # Remove from pending
            del peer_instance.pending_requests[request_id]
            
            app.logger.info(f"Peer 3: Connection accepted from {req_data['requester_id']}")
            
            return jsonify({
                'status': 'accepted',
                'pseudo_id': peer_instance.pseudo_id,
                'response_hash': response_hash
            })
            
        elif action == 'reject':
            # Remove from pending
            del peer_instance.pending_requests[request_id]
            
            app.logger.info(f"Peer 3: Connection rejected from {req_data['requester_id']}")
            
            return jsonify({
                'status': 'rejected',
                'message': 'Connection request rejected'
            })
            
        else:
            return jsonify({'status': 'error', 'message': 'Invalid action'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/connection/accepted', methods=['POST'])
def handle_connection_accepted():
    """Handle notification that our request was accepted"""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        pseudo_id = data.get('pseudo_id')
        response_hash = data.get('response_hash')
        
        # Check if this matches our pending auth
        if (hasattr(peer_instance, 'pending_auth') and 
            peer_instance.pending_auth and 
            peer_instance.pending_auth['request_id'] == request_id):
            
            # Verify response hash
            nonce = peer_instance.pending_auth['nonce']
            timestamp = peer_instance.pending_auth['timestamp']
            expected_response = hashlib.sha256(f"{pseudo_id}{nonce}{timestamp}".encode()).hexdigest()
            
            if response_hash == expected_response:
                # Use shared session key
                session_key_b64 = data.get('session_key')
                if session_key_b64:
                    peer_instance.session_key = base64.b64decode(session_key_b64.encode('utf-8'))
                else:
                    peer_instance.session_key = peer_instance._generate_session_key()
                    
                peer_instance.active_session = {
                    'peer_id': peer_instance.pending_auth['peer_id'],
                    'peer_pseudo_id': pseudo_id,
                    'start_time': time.time(),
                    'authenticated': True
                }
                
                # Clear pending auth
                peer_instance.pending_auth = None
                
                app.logger.info(f"Peer 3: Connection accepted by {pseudo_id}")
                
                return jsonify({'status': 'success', 'message': 'Session established'})
            
        return jsonify({'status': 'error', 'message': 'Invalid notification'}), 400
        
    except Exception as e:
        app.logger.error(f"Peer 3: Error handling connection acceptance: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peer/receive', methods=['POST'])
def receive_peer_message():
    """Receive encrypted message from another peer"""
    try:
        data = request.get_json()
        encrypted_content = data.get('encrypted_content')
        sender_pseudo_id = data.get('sender_pseudo_id')
        
        app.logger.info(f"Received message from {sender_pseudo_id}")
        
        if not peer_instance.active_session or not peer_instance.session_key:
            app.logger.error("No active session for receiving message")
            return jsonify({'status': 'error', 'message': 'No active session'}), 400
            
        # Decrypt message
        decrypted_message = peer_instance._decrypt_message(encrypted_content, peer_instance.session_key)
        if not decrypted_message:
            app.logger.error("Failed to decrypt received message")
            return jsonify({'status': 'error', 'message': 'Decryption failed'}), 500
            
        # Add to message history
        peer_instance.message_history.append({
            'type': 'received',
            'content': decrypted_message,
            'timestamp': time.time(),
            'encrypted': True,
            'sender': sender_pseudo_id
        })
        
        app.logger.info(f"Message received and decrypted: {decrypted_message[:50]}...")
        
        return jsonify({'status': 'received', 'message': 'Message received'})
        
    except Exception as e:
        app.logger.error(f"Error receiving message: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peer/send', methods=['POST'])
def send_peer_message():
    """Send encrypted message"""
    try:
        data = request.get_json()
        message_text = data.get('message')
        
        if not message_text:
            return jsonify({'status': 'error', 'message': 'Message text required'}), 400
            
        if not peer_instance.active_session or not peer_instance.session_key:
            return jsonify({'status': 'error', 'message': 'No active session'}), 400
            
        # Encrypt message
        encrypted_message = peer_instance._encrypt_message(message_text, peer_instance.session_key)
        if not encrypted_message:
            return jsonify({'status': 'error', 'message': 'Encryption failed'}), 500
            
        # Send to other peer
        peer_id = peer_instance.active_session['peer_id']
        peer_info = peer_instance.discovered_peers.get(peer_id)
        
        if peer_info:
            try:
                send_url = f"http://{peer_info['ip_address']}:{peer_info['port']}/api/peer/receive"
                send_data = {
                    'encrypted_content': encrypted_message,
                    'sender_pseudo_id': peer_instance.pseudo_id
                }
                requests.post(send_url, json=send_data, timeout=5)
            except Exception as e:
                app.logger.error(f"Failed to send to peer: {e}")
            
        # Add to local message history
        peer_instance.message_history.append({
            'type': 'sent',
            'content': message_text,
            'timestamp': time.time(),
            'encrypted': True
        })
        
        # Report message to controller
        try:
            requests.post('http://localhost:5000/api/message/report', 
                        json={'message_size': len(message_text)}, timeout=2)
        except:
            pass  # Ignore reporting errors
        
        return jsonify({
            'status': 'success',
            'message': 'Message sent successfully'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peer/messages', methods=['GET'])
def get_messages():
    """Get message history for current session"""
    return jsonify({
        'messages': peer_instance.message_history,
        'session_active': peer_instance.active_session is not None
    })

@app.route('/api/peer/terminate', methods=['POST'])
def terminate_session():
    """Terminate current session"""
    try:
        success = peer_instance.terminate_session()
        return jsonify({
            'status': 'success' if success else 'error',
            'message': 'Session terminated' if success else 'No active session'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peer/authenticate', methods=['POST'])
def authenticate_peer():
    """Authenticate with a specific peer"""
    try:
        data = request.get_json()
        peer_id = data.get('peer_id')
        
        if not peer_id:
            return jsonify({'status': 'error', 'message': 'Peer ID required'}), 400
            
        success, message = peer_instance.authenticate_with_peer(peer_id)
        
        return jsonify({
            'status': 'success' if success else 'error',
            'message': message,
            'session_active': peer_instance.active_session is not None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/attack/launch', methods=['POST'])
def launch_attack():
    """
    Launch REAL attack from Peer 3 dashboard

    Executes actual attack behavior that will be detected by the
    SDN controller based on network patterns, not reported data
    """
    try:
        # Check if this peer has been isolated
        if getattr(peer_instance, 'is_isolated', False):
            app.logger.error("🚫 Attack launch blocked - this peer has been isolated")
            return jsonify({
                'status': 'error',
                'message': 'Cannot launch attack - this peer has been isolated by the network security system',
                'isolated': True,
                'isolation_reason': getattr(peer_instance, 'isolation_reason', 'Unknown')
            }), 403

        data = request.get_json()
        attack_type = data.get('attack_type', 'replay')
        intensity = data.get('intensity', 'low')

        app.logger.warning(
            f"🚨 ATTACK LAUNCH REQUESTED | "
            f"Type: {attack_type} | "
            f"Intensity: {intensity}"
        )

        # Map intensity to expected severity
        severity_map = {
            'low': 'LOW',
            'medium': 'MEDIUM',
            'high': 'HIGH',
            'critical': 'CRITICAL'
        }
        expected_severity = severity_map.get(intensity, 'LOW')

        if attack_type == 'replay':
            # Execute actual replay attack (duplicate nonces)
            success = peer_instance.execute_replay_attack(intensity)
        elif attack_type == 'flooding':
            # Execute actual network flooding attack
            success = peer_instance.execute_flooding_attack(intensity)
        elif attack_type == 'auth_flooding':
            # Execute authentication flooding attack
            success = peer_instance.execute_auth_flooding_attack(intensity)
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unknown attack type: {attack_type}'
            }), 400

        if success:
            return jsonify({
                'status': 'success',
                'attack_type': attack_type,
                'intensity': intensity,
                'severity': expected_severity,
                'message': f'{attack_type.title()} attack launched - controller will detect automatically'
            })
        else:
            return jsonify({'status': 'error', 'message': 'Attack launch failed'}), 500
            
    except Exception as e:
        app.logger.error(f"Attack launch error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/attack/burst', methods=['POST'])
def launch_burst_attack():
    """
    Launch BURST attack - sends all attacks rapidly to reach target severity level

    This is useful for testing progressive defense without blocking interruption
    Sends all required attacks for the target level in rapid succession
    """
    try:
        # Check if this peer has been isolated
        if getattr(peer_instance, 'is_isolated', False):
            app.logger.error("🚫 Burst attack blocked - this peer has been isolated")
            return jsonify({
                'status': 'error',
                'message': 'Cannot launch attack - this peer has been isolated by the network security system',
                'isolated': True,
                'isolation_reason': getattr(peer_instance, 'isolation_reason', 'Unknown')
            }), 403

        data = request.get_json()
        attack_type = data.get('attack_type', 'replay')
        target_level = data.get('target_level', 'CRITICAL')  # LOW, MEDIUM, HIGH, CRITICAL

        # Map target level to required attack count (for replay attacks)
        level_to_count = {
            'LOW': 2,
            'MEDIUM': 3,
            'HIGH': 5,
            'CRITICAL': 8  # Extra attacks to ensure CRITICAL is reached
        }

        attack_count = level_to_count.get(target_level, 8)

        app.logger.warning(
            f"BURST ATTACK MODE | "
            f"Type: {attack_type} | "
            f"Target Level: {target_level} | "
            f"Attacks: {attack_count}"
        )

        if attack_type == 'replay':
            # Send all replay attacks in rapid burst
            try:
                # Generate a nonce first (simulate legitimate auth)
                stored_nonce = secrets.token_hex(16)

                # Send one legitimate auth first
                legitimate_auth = {
                    'pseudo_id': peer_instance.pseudo_id,
                    'nonce': stored_nonce,
                    'timestamp': int(time.time()),
                    'challenge': hashlib.sha256(f"{peer_instance.pseudo_id}{stored_nonce}{int(time.time())}".encode()).hexdigest()
                }
                try:
                    requests.post('http://localhost:8080/api/auth/request', json=legitimate_auth, timeout=0.5)
                except:
                    pass  # Fire and forget
                try:
                    requests.post('http://localhost:8081/api/auth/request', json=legitimate_auth, timeout=0.5)
                except:
                    pass  # Fire and forget
                time.sleep(0.3)  # Wait for nonce to be stored

                # Now send ALL replay attacks rapidly
                for i in range(attack_count):
                    replay_auth = {
                        'pseudo_id': peer_instance.pseudo_id,
                        'nonce': stored_nonce,  # SAME NONCE = REPLAY ATTACK
                        'timestamp': int(time.time()),
                        'challenge': hashlib.sha256(f"{peer_instance.pseudo_id}{stored_nonce}{int(time.time())}".encode()).hexdigest()
                    }

                    # Send to both peers - fire and forget
                    try:
                        requests.post('http://localhost:8080/api/auth/request', json=replay_auth, timeout=0.5)
                    except:
                        pass  # Ignore timeouts/errors
                    try:
                        requests.post('http://localhost:8081/api/auth/request', json=replay_auth, timeout=0.5)
                    except:
                        pass  # Ignore timeouts/errors

                    # MINIMAL delay - just enough to not overwhelm the network
                    time.sleep(0.02)

                app.logger.warning(f"BURST COMPLETE: {attack_count} replay attacks sent to both peers")

                return jsonify({
                    'status': 'success',
                    'attack_type': attack_type,
                    'target_level': target_level,
                    'attacks_sent': attack_count,
                    'message': f'Burst attack complete - {attack_count} {attack_type} attacks sent rapidly to reach {target_level} level'
                })

            except Exception as e:
                app.logger.error(f"Burst attack failed: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        else:
            return jsonify({
                'status': 'error',
                'message': f'Burst mode not yet implemented for {attack_type}'
            }), 400

    except Exception as e:
        app.logger.error(f"Burst attack error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/security/notify', methods=['POST'])
def receive_security_alert():
    """Receive security alert from controller"""
    try:
        alert_data = request.get_json()
        
        # Create security alert for this peer
        security_alert = {
            'timestamp': alert_data.get('timestamp', time.time()),
            'type': alert_data.get('attack_type', 'UNKNOWN'),
            'severity': alert_data.get('severity', 'LOW'),
            'message': alert_data.get('message', 'Security threat detected'),
            'attacker_id': alert_data.get('attacker_id', 'unknown'),
            'action_recommended': alert_data.get('action_recommended', 'Stay vigilant'),
            'source': 'SDN_CONTROLLER'
        }
        
        # Add to peer's security alerts
        peer_instance.security_alerts.append(security_alert)
        
        # Keep only last 20 alerts
        if len(peer_instance.security_alerts) > 20:
            peer_instance.security_alerts = peer_instance.security_alerts[-20:]
            
        app.logger.warning(f"Peer 3 SECURITY ALERT RECEIVED: {security_alert['type']} - {security_alert['severity']} - {security_alert['message']}")
        
        return jsonify({'status': 'success', 'alert_received': True})
        
    except Exception as e:
        app.logger.error(f"Peer 3 error receiving security alert: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=8082, debug=True)