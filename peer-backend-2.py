#!/usr/bin/env python3
"""
Peer Backend 2 - Anonymous P2P Communication (Port 8081)
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
    def __init__(self, port=8081):
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
        
        app.logger.info(f"Peer 2 initialized with pseudo-ID: {self.pseudo_id}")

    def _generate_pseudo_id(self):
        """Generate anonymous pseudo-identity"""
        random_bytes = get_random_bytes(16)
        return hashlib.sha256(random_bytes).hexdigest()[:16]

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
                app.logger.info(f"Peer 2 successfully registered with controller")
                # Start session reporting
                self._start_session_reporting()
                return True
            else:
                app.logger.warning(f"Peer 2 controller registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            app.logger.warning(f"Peer 2 could not register with controller: {e}")
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
            self.discovery_socket.bind(('', 9998))  # Peer 2 uses port 9998
            self.running = True
            
            # Start discovery listener thread
            discovery_thread = threading.Thread(target=self._discovery_listener)
            discovery_thread.daemon = True
            discovery_thread.start()
            
            app.logger.info("Peer 2 discovery started on port 9998")
            return True
            
        except Exception as e:
            app.logger.error(f"Peer 2 failed to start discovery: {e}")
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
                        app.logger.info(f"Peer 2 discovered peer: {peer_info['pseudo_id']} at {addr[0]}")
                        
            except Exception as e:
                if self.running:
                    app.logger.error(f"Peer 2 discovery listener error: {e}")

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
            broadcast_socket.sendto(data, ('<broadcast>', 9998))  # Peer 2 (self)
            broadcast_socket.sendto(data, ('<broadcast>', 9997))  # Peer 3
            broadcast_socket.close()
            
            app.logger.info("Peer 2 presence broadcast sent")
            return True
            
        except Exception as e:
            app.logger.error(f"Peer 2 broadcast error: {e}")
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
                
                app.logger.info(f"Peer 2: Authentication request sent, awaiting approval. Request ID: {request_id}")
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
                    
                    app.logger.info(f"Peer 2 authentication successful with peer {peer_id}")
                    return True, "Authentication successful"
                    
            return False, "Authentication failed"
            
        except Exception as e:
            app.logger.error(f"Peer 2 authentication error: {e}")
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

    def terminate_session(self):
        """Terminate active session and clear keys"""
        if self.active_session:
            app.logger.info(f"Peer 2 terminating session with {self.active_session['peer_id']}")
            
            # Clear session data
            self.session_key = None
            self.active_session = None
            self.message_history.clear()  # Clear chat history
            self.nonce_cache.clear()
            
            return True
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
        'peer_name': 'Peer 2'
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
            'peer_name': 'Peer 2'
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
    app.logger.info(f"Peer 2 security alerts requested - count: {len(peer_instance.security_alerts)}")
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

        # ALWAYS report to controller first (even if blocked) - controller needs to see all attacks
        try:
            monitor_data = {
                'event_type': 'AUTH_ATTEMPT',
                'peer_id': requester_id,  # Use the requester's ID (attacker)
                'nonce': nonce,
                'timestamp': timestamp,
                'target_peer': peer_instance.pseudo_id
            }
            requests.post('http://localhost:5000/api/network/monitor',
                        json=monitor_data, timeout=1)
            app.logger.debug(f"✓ Peer 2: Reported auth attempt to controller (requester: {requester_id[:8]}...)")
        except Exception as e:
            app.logger.error(f"✗ Peer 2: Failed to report to controller: {e}")
            pass  # Don't fail auth if monitoring fails

        # Check if requester is blocked (AFTER reporting to controller)
        if hasattr(peer_instance, 'blocked_peers') and requester_id in peer_instance.blocked_peers:
            app.logger.warning(f"🚫 Peer 2: BLOCKED connection request from {requester_id[:8]}... (peer is isolated/blocked)")
            return jsonify({
                'status': 'blocked',
                'message': 'Connection refused - peer has been blocked by security system'
            }), 403
        
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
            
            app.logger.info(f"Peer 2: Connection request received from {requester_id}")
            
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
                app.logger.error(f"Peer 2: Failed to notify requester: {e}")
            
            # Remove from pending
            del peer_instance.pending_requests[request_id]
            
            app.logger.info(f"Peer 2: Connection accepted from {req_data['requester_id']}")
            
            return jsonify({
                'status': 'accepted',
                'pseudo_id': peer_instance.pseudo_id,
                'response_hash': response_hash
            })
            
        elif action == 'reject':
            # Remove from pending
            del peer_instance.pending_requests[request_id]
            
            app.logger.info(f"Peer 2: Connection rejected from {req_data['requester_id']}")
            
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
                
                app.logger.info(f"Peer 2: Connection accepted by {pseudo_id}")
                
                return jsonify({'status': 'success', 'message': 'Session established'})
            
        return jsonify({'status': 'error', 'message': 'Invalid notification'}), 400
        
    except Exception as e:
        app.logger.error(f"Peer 2: Error handling connection acceptance: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peer/receive', methods=['POST'])
def receive_peer_message():
    """Receive encrypted message from another peer"""
    try:
        data = request.get_json()

        # Check if this is a flood attack packet
        if data.get('flood_packet'):
            sender_id = data.get('sender_pseudo_id', 'unknown')

            # Report flooding to controller
            try:
                monitor_data = {
                    'event_type': 'PACKET_FLOOD',
                    'peer_id': sender_id,
                    'packet_count': 1,
                    'target_peer': peer_instance.pseudo_id
                }
                requests.post('http://localhost:5000/api/network/monitor',
                            json=monitor_data, timeout=1)
            except:
                pass

            app.logger.warning(f"Flood packet received from {sender_id}")
            return jsonify({'status': 'dropped', 'message': 'Flood packet detected'}), 429

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

@app.route('/api/security/notify', methods=['POST'])
def receive_security_alert():
    """Receive security alert from controller and take action"""
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

        app.logger.warning(f"Peer 2 SECURITY ALERT RECEIVED: {security_alert['type']} - {security_alert['severity']} - {security_alert['message']}")

        # ============================================
        # TAKE ACTION BASED ON NOTIFICATION TYPE
        # ============================================
        notification_type = alert_data.get('type')
        attacker_id = alert_data.get('attacker_id')

        app.logger.info(f"Peer 2 processing progressive action notification: {notification_type} for attacker {attacker_id[:8] if attacker_id else 'unknown'}...")

        if notification_type == 'SESSION_TERMINATED':
            # LEVEL 2: Terminate session if connected to attacker
            if peer_instance.active_session:
                if peer_instance.active_session.get('peer_id') == attacker_id or \
                   peer_instance.active_session.get('peer_pseudo_id') == attacker_id:
                    peer_instance.active_session = None
                    peer_instance.session_key = None
                    peer_instance.message_history = []
                    app.logger.warning(f"🔒 Peer 2 SESSION TERMINATED by controller (attacker: {attacker_id[:8]}...)")
                else:
                    app.logger.info(f"Peer 2 SESSION_TERMINATED notification received but not connected to attacker (connected to {peer_instance.active_session.get('peer_id', 'unknown')[:8]}...)")
            else:
                app.logger.info(f"Peer 2 SESSION_TERMINATED notification received but no active session")

            # Block future connection requests from attacker
            if not hasattr(peer_instance, 'blocked_peers'):
                peer_instance.blocked_peers = set()
            peer_instance.blocked_peers.add(attacker_id)

            # Remove any existing pending requests from attacker
            requests_to_remove = [req_id for req_id, req_data in peer_instance.pending_requests.items()
                                if req_data.get('requester_id') == attacker_id]
            for req_id in requests_to_remove:
                del peer_instance.pending_requests[req_id]
                app.logger.info(f"Peer 2 removed pending connection request from blocked attacker {attacker_id[:8]}...")

            app.logger.info(f"Peer 2 blocked future connections from {attacker_id[:8]}...")

        elif notification_type == 'KEYS_DESTROYED':
            # LEVEL 3: Destroy keys and terminate session
            if peer_instance.active_session:
                if peer_instance.active_session.get('peer_id') == attacker_id or \
                   peer_instance.active_session.get('peer_pseudo_id') == attacker_id:
                    peer_instance.active_session = None
                    peer_instance.session_key = None
                    peer_instance.message_history = []
                    app.logger.error(f"🔐 Peer 2 KEYS DESTROYED by controller (attacker: {attacker_id[:8]}...)")
                else:
                    app.logger.info(f"Peer 2 KEYS_DESTROYED notification received but not connected to attacker (connected to {peer_instance.active_session.get('peer_id', 'unknown')[:8]}...)")
            else:
                app.logger.info(f"Peer 2 KEYS_DESTROYED notification received but no active session")

            # Block future connection requests from attacker
            if not hasattr(peer_instance, 'blocked_peers'):
                peer_instance.blocked_peers = set()
            peer_instance.blocked_peers.add(attacker_id)

            # Remove any existing pending requests from attacker
            requests_to_remove = [req_id for req_id, req_data in peer_instance.pending_requests.items()
                                if req_data.get('requester_id') == attacker_id]
            for req_id in requests_to_remove:
                del peer_instance.pending_requests[req_id]
                app.logger.info(f"Peer 2 removed pending connection request from blocked attacker {attacker_id[:8]}...")

            app.logger.info(f"Peer 2 blocked future connections from {attacker_id[:8]}...")

        elif notification_type == 'PEER_ISOLATED':
            # LEVEL 4: Block attacker completely
            if peer_instance.active_session:
                if peer_instance.active_session.get('peer_id') == attacker_id or \
                   peer_instance.active_session.get('peer_pseudo_id') == attacker_id:
                    peer_instance.active_session = None
                    peer_instance.session_key = None
                    peer_instance.message_history = []
                    app.logger.critical(f"🚫 Peer 2 SESSION with attacker TERMINATED (attacker: {attacker_id[:8]}...)")
                else:
                    app.logger.info(f"Peer 2 PEER_ISOLATED notification received but not connected to attacker (connected to {peer_instance.active_session.get('peer_id', 'unknown')[:8]}...)")

            # Remove attacker from discovered peers
            peers_to_remove = [pid for pid, pdata in peer_instance.discovered_peers.items()
                             if pdata.get('pseudo_id') == attacker_id]
            for pid in peers_to_remove:
                del peer_instance.discovered_peers[pid]
                app.logger.info(f"Peer 2 removed attacker from discovered peers list")

            # Block future connection requests from attacker
            if not hasattr(peer_instance, 'blocked_peers'):
                peer_instance.blocked_peers = set()
            peer_instance.blocked_peers.add(attacker_id)

            # Remove any existing pending requests from attacker
            requests_to_remove = [req_id for req_id, req_data in peer_instance.pending_requests.items()
                                if req_data.get('requester_id') == attacker_id]
            for req_id in requests_to_remove:
                del peer_instance.pending_requests[req_id]
                app.logger.info(f"Peer 2 removed pending connection request from isolated attacker {attacker_id[:8]}...")

            app.logger.critical(f"🚫 Peer 2 ATTACKER ISOLATED AND BLOCKED (attacker: {attacker_id[:8]}...)")

        return jsonify({'status': 'success', 'alert_received': True, 'action_taken': True})

    except Exception as e:
        app.logger.error(f"Peer 2 error receiving security alert: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=8081, debug=True)