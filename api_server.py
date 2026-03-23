#!/usr/bin/env python3
"""
Flask API Server for SDN Security Controller
Provides REST endpoints for React dashboards
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import time
import threading
import requests
from collections import defaultdict
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from datetime import datetime

# ========================================
# SECURITY ENUMS AND CLASSES
# ========================================

class AttackType(Enum):
    """Types of attacks that can be detected"""
    REPLAY_ATTACK = "REPLAY_ATTACK"
    FLOODING_ATTACK = "FLOODING_ATTACK"
    AUTH_FLOODING = "AUTH_FLOODING"
    SPOOFING_ATTACK = "SPOOFING_ATTACK"
    MAN_IN_MIDDLE = "MAN_IN_MIDDLE"
    KEY_COMPROMISE = "KEY_COMPROMISE"
    UNKNOWN = "UNKNOWN"

class SeverityLevel(Enum):
    """Progressive severity levels"""
    LOW = 1       # Monitoring & Warning
    MEDIUM = 2    # Session Termination
    HIGH = 3      # Key Destruction
    CRITICAL = 4  # Peer Isolation

class SecurityAction(Enum):
    """Actions taken in response to attacks"""
    MONITORING = "monitoring"
    WARNING = "warning"
    SESSION_TERMINATION = "session_termination"
    KEY_DESTRUCTION = "key_destruction"
    PEER_ISOLATION = "peer_isolation"
    NETWORK_QUARANTINE = "network_quarantine"

class PeerSecurityState(Enum):
    """Security states for peers"""
    NORMAL = "normal"
    SUSPICIOUS = "suspicious"
    THREAT_DETECTED = "threat_detected"
    COMPROMISED = "compromised"
    ISOLATED = "isolated"
    QUARANTINED = "quarantined"

@dataclass
class AttackMetrics:
    """Metrics for tracking attack patterns per peer"""
    peer_id: str
    total_replay_attempts: int = 0
    total_flood_events: int = 0
    total_auth_failures: int = 0
    suspicious_patterns: int = 0
    first_attack_time: Optional[float] = None
    last_attack_time: Optional[float] = None
    current_severity: SeverityLevel = SeverityLevel.LOW
    state: PeerSecurityState = PeerSecurityState.NORMAL
    sessions_terminated: int = 0
    keys_destroyed: bool = False
    isolated: bool = False
    isolation_time: Optional[float] = None
    threat_score: float = 0.0

    def update_threat_score(self):
        """Calculate threat score based on attack patterns"""
        score = 0.0
        score += self.total_replay_attempts * 15  # High weight for replay
        score += self.total_flood_events * 10
        score += self.total_auth_failures * 5
        score += self.suspicious_patterns * 3

        # Time-based decay
        if self.last_attack_time:
            time_since = time.time() - self.last_attack_time
            decay_factor = max(0.5, 1.0 - (time_since / 3600))  # Decay over 1 hour
            score *= decay_factor

        self.threat_score = min(100.0, score)
        return self.threat_score

@dataclass
class SecurityConfiguration:
    """Configuration for progressive self-destruct thresholds"""
    # Replay attack thresholds
    replay_low_threshold: int = 2
    replay_medium_threshold: int = 3
    replay_high_threshold: int = 5
    replay_critical_threshold: int = 7

    # Flooding attack thresholds (packets per 10 seconds)
    flood_low_threshold: int = 15
    flood_medium_threshold: int = 30
    flood_high_threshold: int = 50
    flood_critical_threshold: int = 100

    # Authentication flooding thresholds (attempts per minute)
    auth_low_threshold: int = 5
    auth_medium_threshold: int = 10
    auth_high_threshold: int = 15
    auth_critical_threshold: int = 20

    # Time windows
    flood_detection_window: int = 10  # seconds
    auth_detection_window: int = 60   # seconds
    cleanup_interval: int = 300       # 5 minutes
    alert_retention: int = 3600       # 1 hour

    # Progressive response settings
    auto_escalation_enabled: bool = True
    victim_notification_enabled: bool = True
    auto_recovery_enabled: bool = False
    recovery_cooldown: int = 1800  # 30 minutes

# Global configuration
SECURITY_CONFIG = SecurityConfiguration()

# WSL/Docker Network Configuration
# When running controller in WSL/Ubuntu and peers on Windows, use Windows host IP
# Get Windows host IP from environment variable or default to localhost
import os
VICTIM_PEER_HOST = os.environ.get('VICTIM_PEER_HOST', '192.168.1.2')

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# ========================================
# GLOBAL STATE MANAGEMENT
# ========================================

# Global state (in production, use proper state management)
controller_state = {
    'active': False,
    'start_time': time.time(),  # Track controller start time
    'flows': {},
    'peers': {},
    'sessions': {},  # Track active peer sessions
    'alerts': [],
    'security_events': [],
    'message_count': 0,  # Track total messages
    'total_bytes': 0,    # Track total bytes
    'network_monitor': {  # Real-time attack detection
        'auth_attempts': {},  # Track authentication attempts per peer
        'packet_rates': {},   # Track packet rates per peer
        'nonce_history': {},  # Track nonces to detect replays (global)
        'last_cleanup': time.time()
    }
}

# Security event storage
security_events = []
active_alerts = []

# Attack metrics per peer (professional tracking)
attack_metrics: Dict[str, AttackMetrics] = {}

# Peer security states
peer_security_states: Dict[str, PeerSecurityState] = {}

def get_or_create_metrics(peer_id: str) -> AttackMetrics:
    """Get or create attack metrics for a peer"""
    if peer_id not in attack_metrics:
        attack_metrics[peer_id] = AttackMetrics(peer_id=peer_id)
        peer_security_states[peer_id] = PeerSecurityState.NORMAL
    return attack_metrics[peer_id]

def update_peer_security_state(peer_id: str, new_state: PeerSecurityState):
    """Update peer security state with logging"""
    old_state = peer_security_states.get(peer_id, PeerSecurityState.NORMAL)
    peer_security_states[peer_id] = new_state

    app.logger.info(f"🔐 Peer {peer_id[:8]}... security state: {old_state.value} → {new_state.value}")

    # Update metrics
    metrics = get_or_create_metrics(peer_id)
    metrics.state = new_state

    # Log security event
    security_events.append({
        'timestamp': time.time(),
        'event_type': 'STATE_TRANSITION',
        'details': {
            'peer_id': peer_id,
            'old_state': old_state.value,
            'new_state': new_state.value,
            'threat_score': metrics.threat_score
        }
    })

# ========================================
# FLASK ROUTES
# ========================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get overall system status"""
    return jsonify({
        'active': controller_state['active'],
        'timestamp': time.time(),
        'active_peers': len(controller_state['peers']),
        'active_flows': len(controller_state['sessions']),  # Use sessions instead of flows
        'recent_alerts': len([a for a in active_alerts if time.time() - a['timestamp'] < 300])
    })

@app.route('/api/status/comprehensive', methods=['GET'])
def get_comprehensive_status():
    """
    Get comprehensive SDN Progressive Self-Destruct system status

    Returns detailed overview of:
    - System health
    - Threat landscape
    - Progressive defense levels
    - Attack statistics
    - Peer security states
    """
    try:
        current_time = time.time()

        # Calculate threat statistics
        total_threats = len(attack_metrics)
        isolated_peers = sum(1 for m in attack_metrics.values() if m.isolated)
        suspicious_peers = sum(1 for m in attack_metrics.values()
                              if m.state in [PeerSecurityState.SUSPICIOUS,
                                           PeerSecurityState.THREAT_DETECTED,
                                           PeerSecurityState.COMPROMISED])

        # Calculate attack statistics
        total_replay_attacks = sum(m.total_replay_attempts for m in attack_metrics.values())
        total_flood_attacks = sum(m.total_flood_events for m in attack_metrics.values())
        total_auth_failures = sum(m.total_auth_failures for m in attack_metrics.values())

        # Get active alerts by severity
        recent_alerts = [a for a in active_alerts if current_time - a['timestamp'] < 300]
        alerts_by_severity = {
            'LOW': sum(1 for a in recent_alerts if a.get('severity') == 'LOW'),
            'MEDIUM': sum(1 for a in recent_alerts if a.get('severity') == 'MEDIUM'),
            'HIGH': sum(1 for a in recent_alerts if a.get('severity') == 'HIGH'),
            'CRITICAL': sum(1 for a in recent_alerts if a.get('severity') == 'CRITICAL')
        }

        # Count actions taken
        sessions_terminated = sum(m.sessions_terminated for m in attack_metrics.values())
        keys_destroyed_count = sum(1 for m in attack_metrics.values() if m.keys_destroyed)

        # Progressive defense level counts
        peers_by_severity = {
            'LOW': sum(1 for m in attack_metrics.values() if m.current_severity == SeverityLevel.LOW),
            'MEDIUM': sum(1 for m in attack_metrics.values() if m.current_severity == SeverityLevel.MEDIUM),
            'HIGH': sum(1 for m in attack_metrics.values() if m.current_severity == SeverityLevel.HIGH),
            'CRITICAL': sum(1 for m in attack_metrics.values() if m.current_severity == SeverityLevel.CRITICAL)
        }

        # Security state distribution
        state_distribution = {}
        for state in PeerSecurityState:
            count = sum(1 for m in attack_metrics.values() if m.state == state)
            state_distribution[state.value] = count

        # Top threats
        top_threats = sorted(
            attack_metrics.values(),
            key=lambda m: m.threat_score,
            reverse=True
        )[:5]

        top_threats_list = [{
            'peer_id': m.peer_id[:8] + '...',
            'threat_score': m.threat_score,
            'security_state': m.state.value,
            'severity': m.current_severity.name,
            'isolated': m.isolated,
            'total_attacks': m.total_replay_attempts + m.total_flood_events + m.total_auth_failures
        } for m in top_threats]

        # System health score (0-100)
        health_score = 100.0
        health_score -= isolated_peers * 10  # -10 per isolated peer
        health_score -= suspicious_peers * 5  # -5 per suspicious peer
        health_score -= len(recent_alerts) * 2  # -2 per recent alert
        health_score = max(0.0, health_score)

        return jsonify({
            'status': 'success',
            'timestamp': current_time,
            'system': {
                'controller_active': controller_state['active'],
                'health_score': health_score,
                'uptime': current_time - controller_state.get('start_time', current_time)
            },
            'threat_landscape': {
                'total_monitored_peers': total_threats,
                'isolated_peers': isolated_peers,
                'suspicious_peers': suspicious_peers,
                'normal_peers': len(controller_state['peers']) - suspicious_peers - isolated_peers
            },
            'attack_statistics': {
                'total_replay_attacks': total_replay_attacks,
                'total_flood_attacks': total_flood_attacks,
                'total_auth_failures': total_auth_failures,
                'total_attacks': total_replay_attacks + total_flood_attacks + total_auth_failures
            },
            'progressive_defense_levels': {
                'level_1_monitoring': peers_by_severity['LOW'],
                'level_2_session_termination': peers_by_severity['MEDIUM'],
                'level_3_key_destruction': peers_by_severity['HIGH'],
                'level_4_peer_isolation': peers_by_severity['CRITICAL']
            },
            'security_states': state_distribution,
            'alerts': {
                'total_recent': len(recent_alerts),
                'by_severity': alerts_by_severity,
                'total_all_time': len(active_alerts)
            },
            'actions_taken': {
                'sessions_terminated': sessions_terminated,
                'keys_destroyed': keys_destroyed_count,
                'peers_isolated': isolated_peers
            },
            'top_threats': top_threats_list,
            'network': {
                'active_peers': len(controller_state['peers']),
                'active_sessions': len(controller_state['sessions']),
                'total_messages': controller_state['message_count'],
                'total_bytes': controller_state['total_bytes']
            },
            'configuration': {
                'auto_escalation': SECURITY_CONFIG.auto_escalation_enabled,
                'victim_notification': SECURITY_CONFIG.victim_notification_enabled,
                'auto_recovery': SECURITY_CONFIG.auto_recovery_enabled
            }
        })

    except Exception as e:
        app.logger.error(f"❌ Error in comprehensive status: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peers', methods=['GET'])
def get_peers():
    """Get list of discovered peers"""
    peers = []
    for peer_id, peer_data in controller_state['peers'].items():
        peers.append({
            'id': peer_id,
            'mac_address': peer_data.get('mac_address', 'unknown'),
            'ip_address': peer_data.get('ip_address', 'unknown'),
            'status': peer_data.get('status', 'active'),
            'security_level': peer_data.get('security_level', 'normal'),
            'last_seen': peer_data.get('last_seen', time.time())
        })
    return jsonify(peers)

@app.route('/api/flows', methods=['GET'])
def get_flows():
    """Get active network flows (sessions)"""
    flows = []
    for session_id, session_data in controller_state['sessions'].items():
        flows.append({
            'id': session_id,
            'source': session_data.get('peer_a', 'unknown'),
            'destination': session_data.get('peer_b', 'unknown'),
            'packet_count': 150,  # Simulated
            'byte_count': 75000,  # Simulated
            'duration': time.time() - session_data.get('start_time', time.time()),
            'suspicious': False
        })
    return jsonify(flows)

@app.route('/api/security/events', methods=['GET'])
def get_security_events():
    """Get recent security events"""
    # Return last 50 events
    recent_events = security_events[-50:] if len(security_events) > 50 else security_events
    return jsonify(recent_events)

@app.route('/api/security/alerts', methods=['GET'])
def get_active_alerts():
    """Get active security alerts"""
    # Filter alerts from last 10 minutes
    current_time = time.time()
    recent_alerts = [
        alert for alert in active_alerts 
        if current_time - alert['timestamp'] < 600
    ]
    return jsonify(recent_alerts)

@app.route('/api/security/alert', methods=['POST'])
def create_security_alert():
    """Create a new security alert (called by SDN controller)"""
    try:
        alert_data = request.get_json()
        
        alert = {
            'id': len(active_alerts) + 1,
            'timestamp': time.time(),
            'peer_mac': alert_data.get('peer_mac', 'unknown'),
            'alert_type': alert_data.get('alert_type', 'UNKNOWN'),
            'severity': alert_data.get('severity', 'LOW'),
            'message': alert_data.get('message', 'Security event detected'),
            'action_taken': alert_data.get('action_taken', 'none'),
            'attacker_peer_id': alert_data.get('attacker_peer_id')
        }
        
        active_alerts.append(alert)
        
        # Take progressive action based on severity
        attacker_peer_id = alert.get('attacker_peer_id')
        severity = alert.get('severity')
        
        if severity == 'MEDIUM' and attacker_peer_id:
            # Terminate only sessions involving the attacker
            sessions_to_remove = []
            for session_id, session in controller_state['sessions'].items():
                if attacker_peer_id in [session.get('peer_a'), session.get('peer_b')]:
                    sessions_to_remove.append(session_id)
                    
            for session_id in sessions_to_remove:
                del controller_state['sessions'][session_id]
                app.logger.warning(f"Terminated session {session_id} involving attacker {attacker_peer_id}")
                
        elif severity == 'HIGH' and attacker_peer_id:
            # Mark attacker's keys as destroyed
            if attacker_peer_id in controller_state['peers']:
                controller_state['peers'][attacker_peer_id]['keys_destroyed'] = True
                app.logger.warning(f"Destroyed keys for attacker {attacker_peer_id}")
                
        elif severity == 'CRITICAL' and attacker_peer_id:
            # Isolate the attacker peer
            if attacker_peer_id in controller_state['peers']:
                controller_state['peers'][attacker_peer_id]['status'] = 'isolated'
                controller_state['peers'][attacker_peer_id]['isolated_at'] = time.time()
                app.logger.warning(f"Isolated attacker peer {attacker_peer_id}")
        
        # Also add to security events log
        security_events.append({
            'timestamp': alert['timestamp'],
            'event_type': 'SECURITY_ALERT',
            'details': alert
        })
        
        app.logger.info(f"Security alert created: {alert['alert_type']} for {alert['peer_mac']}")
        
        return jsonify({'status': 'success', 'alert_id': alert['id']})
        
    except Exception as e:
        app.logger.error(f"Error creating security alert: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/peer/discover', methods=['POST'])
def discover_peers():
    """Simulate peer discovery (for demo purposes)"""
    try:
        # In a real implementation, this would scan the network
        discovered_peers = [
            {
                'id': 'peer_001',
                'mac_address': '02:00:00:00:00:01',
                'ip_address': '192.168.1.101',
                'hostname': 'peer-alice',
                'status': 'available'
            },
            {
                'id': 'peer_002', 
                'mac_address': '02:00:00:00:00:02',
                'ip_address': '192.168.1.102',
                'hostname': 'peer-bob',
                'status': 'available'
            }
        ]
        
        # Update controller state
        for peer in discovered_peers:
            controller_state['peers'][peer['id']] = {
                'mac_address': peer['mac_address'],
                'ip_address': peer['ip_address'],
                'hostname': peer['hostname'],
                'status': peer['status'],
                'security_level': 'normal',
                'last_seen': time.time()
            }
            
        return jsonify({
            'status': 'success',
            'peers_discovered': len(discovered_peers),
            'peers': discovered_peers
        })
        
    except Exception as e:
        app.logger.error(f"Error in peer discovery: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/session/start', methods=['POST'])
def start_session():
    """Start a secure session between peers"""
    try:
        session_data = request.get_json()
        peer_a = session_data.get('peer_a')
        peer_b = session_data.get('peer_b')
        
        if not peer_a or not peer_b:
            return jsonify({'status': 'error', 'message': 'Both peers required'}), 400
            
        session_id = f"session_{int(time.time())}"
        
        # Create session record
        session = {
            'id': session_id,
            'peer_a': peer_a,
            'peer_b': peer_b,
            'start_time': time.time(),
            'status': 'active',
            'encrypted': True,
            'anonymous': True
        }
        
        # Log security event
        security_events.append({
            'timestamp': time.time(),
            'event_type': 'SESSION_START',
            'details': session
        })
        
        app.logger.info(f"Session started: {session_id} between {peer_a} and {peer_b}")
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'session': session
        })
        
    except Exception as e:
        app.logger.error(f"Error starting session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/session/terminate', methods=['POST'])
def terminate_session():
    """Terminate a secure session"""
    try:
        session_data = request.get_json()
        session_id = session_data.get('session_id')
        reason = session_data.get('reason', 'user_request')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID required'}), 400
            
        # Log security event
        security_events.append({
            'timestamp': time.time(),
            'event_type': 'SESSION_TERMINATE',
            'details': {
                'session_id': session_id,
                'reason': reason,
                'terminated_by': 'system' if reason != 'user_request' else 'user'
            }
        })
        
        app.logger.info(f"Session terminated: {session_id}, reason: {reason}")
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'terminated': True
        })
        
    except Exception as e:
        app.logger.error(f"Error terminating session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/attack/simulate', methods=['POST'])
def simulate_attack():
    """Simulate an attack for demo purposes"""
    try:
        attack_data = request.get_json()
        attack_type = attack_data.get('type', 'flood')
        target_peer = attack_data.get('target', 'peer_001')
        
        # Create simulated attack event
        attack_event = {
            'timestamp': time.time(),
            'attack_type': attack_type,
            'target_peer': target_peer,
            'source': 'attacker_simulation',
            'detected': True,
            'severity': 'HIGH' if attack_type == 'replay' else 'MEDIUM'
        }
        
        # Create corresponding security alert
        alert = {
            'id': len(active_alerts) + 1,
            'timestamp': time.time(),
            'peer_mac': '02:00:00:00:00:99',  # Simulated attacker MAC
            'alert_type': f'{attack_type.upper()}_ATTACK',
            'severity': attack_event['severity'],
            'message': f'{attack_type.title()} attack detected targeting {target_peer}',
            'action_taken': 'monitoring'
        }
        
        active_alerts.append(alert)
        security_events.append({
            'timestamp': time.time(),
            'event_type': 'ATTACK_DETECTED',
            'details': attack_event
        })
        
        app.logger.warning(f"Simulated {attack_type} attack on {target_peer}")
        
        return jsonify({
            'status': 'success',
            'attack_simulated': True,
            'attack_event': attack_event,
            'alert_created': alert
        })
        
    except Exception as e:
        app.logger.error(f"Error simulating attack: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/network/monitor', methods=['POST'])
def monitor_network_activity():
    """
    Professional SDN Network Monitoring with Progressive Attack Detection

    Monitors network activity and detects:
    - Replay attacks (duplicate nonce detection)
    - Flooding attacks (packet rate analysis)
    - Authentication flooding (auth attempt frequency)
    - Suspicious patterns

    Uses progressive severity escalation based on configurable thresholds
    """
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        peer_id = data.get('peer_id')

        if not peer_id:
            return jsonify({'status': 'error', 'message': 'peer_id required'}), 400

        current_time = time.time()
        monitor = controller_state['network_monitor']
        metrics = get_or_create_metrics(peer_id)

        # ============================================
        # REPLAY ATTACK DETECTION
        # ============================================
        if event_type == 'AUTH_ATTEMPT':
            nonce = data.get('nonce')

            if not nonce:
                return jsonify({'status': 'error', 'message': 'nonce required for AUTH_ATTEMPT'}), 400

            # Initialize peer tracking
            if peer_id not in monitor['auth_attempts']:
                monitor['auth_attempts'][peer_id] = []
            if 'nonce_history' not in monitor:
                monitor['nonce_history'] = {}  # Global nonce tracking across ALL peers

            # Always track the attempt first
            monitor['auth_attempts'][peer_id].append(current_time)

            # Check for replay attack (duplicate nonce) - GLOBAL check across all peers
            is_replay = False
            original_peer = None

            for existing_peer_id, nonce_set in monitor['nonce_history'].items():
                if nonce in nonce_set:
                    is_replay = True
                    original_peer = existing_peer_id
                    break

            if is_replay:
                # REPLAY ATTACK DETECTED
                metrics.total_replay_attempts += 1
                metrics.last_attack_time = current_time

                if metrics.first_attack_time is None:
                    metrics.first_attack_time = current_time

                # Calculate severity based on ACTUAL replay count, not all auth attempts
                severity = calculate_replay_severity(metrics.total_replay_attempts)

                # Update current severity in metrics
                metrics.current_severity = severity

                # Update threat score
                metrics.update_threat_score()

                # Update security state based on severity
                update_security_state_from_severity(peer_id, severity)

                app.logger.warning(
                    f"🚨 REPLAY ATTACK detected from {peer_id[:8]}... | "
                    f"Total replays: {metrics.total_replay_attempts} | "
                    f"Severity: {severity.name} | "
                    f"Threat score: {metrics.threat_score:.1f} | "
                    f"Original nonce from: {original_peer[:8] if original_peer else 'unknown'}..."
                )

                create_automatic_alert(
                    peer_id,
                    AttackType.REPLAY_ATTACK,
                    severity,
                    f'Duplicate nonce detected: {nonce[:8]}... (Replay #{metrics.total_replay_attempts})'
                )

                # Don't add the duplicate nonce
                return jsonify({
                    'status': 'success',
                    'attack_detected': True,
                    'attack_type': 'REPLAY_ATTACK',
                    'severity': severity.name,
                    'threat_score': metrics.threat_score
                })
            else:
                # Valid new nonce - store it globally
                if peer_id not in monitor['nonce_history']:
                    monitor['nonce_history'][peer_id] = set()
                monitor['nonce_history'][peer_id].add(nonce)

            # Check for authentication flooding (even if not replay)
            recent_attempts = [t for t in monitor['auth_attempts'][peer_id]
                             if current_time - t < SECURITY_CONFIG.auth_detection_window]

            if len(recent_attempts) >= SECURITY_CONFIG.auth_low_threshold:
                metrics.total_auth_failures += 1
                metrics.last_attack_time = current_time

                severity = calculate_auth_flood_severity(len(recent_attempts))
                metrics.current_severity = severity
                metrics.update_threat_score()
                update_security_state_from_severity(peer_id, severity)

                app.logger.warning(
                    f"🚨 AUTH FLOODING detected from {peer_id[:8]}... | "
                    f"Attempts: {len(recent_attempts)}/{SECURITY_CONFIG.auth_detection_window}s | "
                    f"Severity: {severity.name} | "
                    f"Threat score: {metrics.threat_score:.1f}"
                )

                create_automatic_alert(
                    peer_id,
                    AttackType.AUTH_FLOODING,
                    severity,
                    f'Excessive authentication attempts: {len(recent_attempts)}/min'
                )

        # ============================================
        # PACKET FLOODING ATTACK DETECTION
        # ============================================
        elif event_type == 'PACKET_FLOOD':
            packet_count = data.get('packet_count', 1)

            if peer_id not in monitor['packet_rates']:
                monitor['packet_rates'][peer_id] = []

            monitor['packet_rates'][peer_id].append({
                'time': current_time,
                'count': packet_count
            })

            # Calculate packets in detection window
            recent_packets = [
                p for p in monitor['packet_rates'][peer_id]
                if current_time - p['time'] < SECURITY_CONFIG.flood_detection_window
            ]
            total_packets = sum(p['count'] for p in recent_packets)

            if total_packets >= SECURITY_CONFIG.flood_low_threshold:
                metrics.total_flood_events += 1
                metrics.last_attack_time = current_time

                if metrics.first_attack_time is None:
                    metrics.first_attack_time = current_time

                severity = calculate_flood_severity(total_packets)
                metrics.current_severity = severity
                metrics.update_threat_score()
                update_security_state_from_severity(peer_id, severity)

                app.logger.warning(
                    f"🚨 FLOODING ATTACK detected from {peer_id[:8]}... | "
                    f"Packets: {total_packets}/{SECURITY_CONFIG.flood_detection_window}s | "
                    f"Severity: {severity.name} | "
                    f"Threat score: {metrics.threat_score:.1f}"
                )

                create_automatic_alert(
                    peer_id,
                    AttackType.FLOODING_ATTACK,
                    severity,
                    f'Network flooding: {total_packets} packets/{SECURITY_CONFIG.flood_detection_window}sec'
                )

        # ============================================
        # PERIODIC CLEANUP
        # ============================================
        if current_time - monitor['last_cleanup'] > SECURITY_CONFIG.cleanup_interval:
            cleanup_monitor_data()
            monitor['last_cleanup'] = current_time

        return jsonify({
            'status': 'success',
            'monitored': True,
            'peer_threat_score': metrics.threat_score,
            'peer_state': metrics.state.value
        })

    except Exception as e:
        app.logger.error(f"❌ Network monitoring error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ========================================
# SEVERITY CALCULATION FUNCTIONS
# ========================================

def calculate_replay_severity(total_attempts: int) -> SeverityLevel:
    """Calculate severity level for replay attacks based on total attempts"""
    if total_attempts >= SECURITY_CONFIG.replay_critical_threshold:
        return SeverityLevel.CRITICAL
    elif total_attempts >= SECURITY_CONFIG.replay_high_threshold:
        return SeverityLevel.HIGH
    elif total_attempts >= SECURITY_CONFIG.replay_medium_threshold:
        return SeverityLevel.MEDIUM
    else:
        return SeverityLevel.LOW

def calculate_flood_severity(packet_count: int) -> SeverityLevel:
    """Calculate severity level for flooding attacks based on packet count"""
    if packet_count >= SECURITY_CONFIG.flood_critical_threshold:
        return SeverityLevel.CRITICAL
    elif packet_count >= SECURITY_CONFIG.flood_high_threshold:
        return SeverityLevel.HIGH
    elif packet_count >= SECURITY_CONFIG.flood_medium_threshold:
        return SeverityLevel.MEDIUM
    else:
        return SeverityLevel.LOW

def calculate_auth_flood_severity(attempt_count: int) -> SeverityLevel:
    """Calculate severity level for authentication flooding"""
    if attempt_count >= SECURITY_CONFIG.auth_critical_threshold:
        return SeverityLevel.CRITICAL
    elif attempt_count >= SECURITY_CONFIG.auth_high_threshold:
        return SeverityLevel.HIGH
    elif attempt_count >= SECURITY_CONFIG.auth_medium_threshold:
        return SeverityLevel.MEDIUM
    else:
        return SeverityLevel.LOW

def update_security_state_from_severity(peer_id: str, severity: SeverityLevel):
    """Update peer security state based on attack severity"""
    current_state = peer_security_states.get(peer_id, PeerSecurityState.NORMAL)

    # State machine transitions based on severity
    if severity == SeverityLevel.LOW:
        if current_state == PeerSecurityState.NORMAL:
            update_peer_security_state(peer_id, PeerSecurityState.SUSPICIOUS)
    elif severity == SeverityLevel.MEDIUM:
        if current_state in [PeerSecurityState.NORMAL, PeerSecurityState.SUSPICIOUS]:
            update_peer_security_state(peer_id, PeerSecurityState.THREAT_DETECTED)
    elif severity == SeverityLevel.HIGH:
        if current_state != PeerSecurityState.ISOLATED:
            update_peer_security_state(peer_id, PeerSecurityState.COMPROMISED)
    elif severity == SeverityLevel.CRITICAL:
        update_peer_security_state(peer_id, PeerSecurityState.ISOLATED)

# ========================================
# PROGRESSIVE ATTACK RESPONSE SYSTEM
# ========================================

def create_automatic_alert(peer_id: str, attack_type: AttackType, severity: SeverityLevel, message: str):
    """
    Professional SDN Progressive Self-Destruct Alert System

    Creates security alert and executes progressive response based on severity:

    Level 1 (LOW): Monitoring & Warning
        - Increase logging
        - Mark peer as suspicious
        - Continue session (no termination)

    Level 2 (MEDIUM): Session Termination
        - Terminate active sessions
        - Inform victim peers
        - Block current flows

    Level 3 (HIGH): Key Deletion
        - Delete session keys
        - Invalidate pseudo-identity
        - Prevent key reuse
        - Force re-authentication

    Level 4 (CRITICAL): Peer Isolation
        - Block all traffic
        - Isolate from P2P network
        - Permanent flow deny rules
    """
    try:
        metrics = get_or_create_metrics(peer_id)
        current_time = time.time()

        # Create professional alert record
        alert = {
            'id': len(active_alerts) + 1,
            'timestamp': current_time,
            'peer_mac': controller_state['peers'].get(peer_id, {}).get('mac_address', '02:00:00:00:00:03'),
            'alert_type': attack_type.value,
            'severity': severity.name,
            'message': f'[AUTO-DETECTED] {message}',
            'action_taken': get_action_for_severity(severity).value,
            'attacker_peer_id': peer_id,
            'detection_method': 'AUTOMATIC_SDN_CONTROLLER',
            'threat_score': metrics.threat_score,
            'security_state': metrics.state.value,
            'total_attacks': (metrics.total_replay_attempts +
                            metrics.total_flood_events +
                            metrics.total_auth_failures)
        }

        active_alerts.append(alert)

        # Notify victim peers IMMEDIATELY (if enabled)
        if SECURITY_CONFIG.victim_notification_enabled:
            notify_victim_peers(peer_id, alert)

        # ============================================
        # PROGRESSIVE SELF-DESTRUCT RESPONSE
        # ============================================

        sessions_terminated = 0

        if severity == SeverityLevel.LOW:
            # LEVEL 1: Monitoring & Warning
            app.logger.info(
                f"📊 [LEVEL 1 - MONITORING] {attack_type.value} from {peer_id[:8]}... | "
                f"Threat score: {metrics.threat_score:.1f} | "
                f"Action: Increased monitoring, peer marked as SUSPICIOUS"
            )
            # No immediate action, just monitoring

        elif severity == SeverityLevel.MEDIUM:
            # LEVEL 2: Session Termination
            sessions_terminated = terminate_peer_sessions(peer_id)
            metrics.sessions_terminated += sessions_terminated

            app.logger.warning(
                f"⚠️  [LEVEL 2 - SESSION TERMINATION] {attack_type.value} from {peer_id[:8]}... | "
                f"Terminated {sessions_terminated} session(s) | "
                f"Threat score: {metrics.threat_score:.1f} | "
                f"Victim peers notified"
            )

            if sessions_terminated > 0:
                notify_session_termination(peer_id, sessions_terminated, attack_type, severity)

        elif severity == SeverityLevel.HIGH:
            # LEVEL 3: Key Destruction + Session Termination
            sessions_terminated = terminate_peer_sessions(peer_id)
            metrics.sessions_terminated += sessions_terminated

            # Destroy encryption keys
            destroy_peer_keys(peer_id)
            metrics.keys_destroyed = True

            app.logger.error(
                f"🔥 [LEVEL 3 - KEY DESTRUCTION] {attack_type.value} from {peer_id[:8]}... | "
                f"Keys destroyed, {sessions_terminated} session(s) terminated | "
                f"Threat score: {metrics.threat_score:.1f} | "
                f"Re-authentication required"
            )

            notify_key_destruction(peer_id, sessions_terminated, attack_type, severity)

        elif severity == SeverityLevel.CRITICAL:
            # LEVEL 4: Complete Peer Isolation
            sessions_terminated = terminate_peer_sessions(peer_id)
            metrics.sessions_terminated += sessions_terminated

            # Destroy keys
            destroy_peer_keys(peer_id)
            metrics.keys_destroyed = True

            # Isolate peer completely
            isolate_peer_from_network(peer_id)
            metrics.isolated = True
            metrics.isolation_time = current_time

            app.logger.critical(
                f"🚫 [LEVEL 4 - PEER ISOLATION] {attack_type.value} from {peer_id[:8]}... | "
                f"PEER ISOLATED FROM NETWORK | "
                f"{sessions_terminated} session(s) terminated, keys destroyed | "
                f"Threat score: {metrics.threat_score:.1f} | "
                f"Network secured"
            )

            notify_peer_isolation(peer_id, sessions_terminated, attack_type, severity)

        # Log comprehensive security event
        security_events.append({
            'timestamp': current_time,
            'event_type': 'PROGRESSIVE_ATTACK_RESPONSE',
            'severity': severity.name,
            'details': {
                'alert': alert,
                'peer_id': peer_id,
                'attack_type': attack_type.value,
                'action_taken': get_action_for_severity(severity).value,
                'sessions_terminated': sessions_terminated,
                'keys_destroyed': metrics.keys_destroyed,
                'isolated': metrics.isolated,
                'threat_score': metrics.threat_score,
                'security_state': metrics.state.value,
                'metrics': {
                    'replay_attempts': metrics.total_replay_attempts,
                    'flood_events': metrics.total_flood_events,
                    'auth_failures': metrics.total_auth_failures
                }
            }
        })

        app.logger.warning(
            f"🚨 PROGRESSIVE SELF-DESTRUCT ACTIVATED | "
            f"Attack: {attack_type.value} | "
            f"Peer: {peer_id[:8]}... | "
            f"Severity: {severity.name} | "
            f"Action: {get_action_for_severity(severity).value} | "
            f"Threat: {metrics.threat_score:.1f}/100"
        )

    except Exception as e:
        app.logger.error(f"❌ Error in create_automatic_alert: {e}", exc_info=True)

# ========================================
# PROGRESSIVE RESPONSE ACTION FUNCTIONS
# ========================================

def terminate_peer_sessions(peer_id: str) -> int:
    """
    Terminate all sessions involving the specified peer

    Returns:
        Number of sessions terminated
    """
    sessions_to_remove = []
    for session_id, session in controller_state['sessions'].items():
        if peer_id in [session.get('peer_a'), session.get('peer_b')]:
            sessions_to_remove.append(session_id)

    for session_id in sessions_to_remove:
        del controller_state['sessions'][session_id]
        app.logger.info(f"  ↳ Terminated session: {session_id}")

    return len(sessions_to_remove)

def destroy_peer_keys(peer_id: str):
    """
    Destroy encryption keys for the specified peer

    Marks keys as destroyed and invalidates pseudo-identity
    Requires re-authentication for any future connections
    """
    if peer_id in controller_state['peers']:
        controller_state['peers'][peer_id]['keys_destroyed'] = True
        controller_state['peers'][peer_id]['key_destruction_time'] = time.time()
        controller_state['peers'][peer_id]['security_level'] = 'compromised'
        app.logger.info(f"  ↳ Destroyed encryption keys for peer: {peer_id[:8]}...")
    else:
        app.logger.warning(f"  ↳ Peer {peer_id[:8]}... not found in controller state")

def isolate_peer_from_network(peer_id: str):
    """
    Completely isolate peer from the P2P network

    Actions:
    - Block all traffic from/to peer
    - Mark peer status as 'isolated'
    - Install drop flow rules (in real SDN)
    - Prevent any future connections
    """
    if peer_id in controller_state['peers']:
        controller_state['peers'][peer_id]['status'] = 'isolated'
        controller_state['peers'][peer_id]['isolated_at'] = time.time()
        controller_state['peers'][peer_id]['security_level'] = 'isolated'
        app.logger.critical(f"  ↳ Peer {peer_id[:8]}... ISOLATED from network")
    else:
        # Create entry for unknown peer
        controller_state['peers'][peer_id] = {
            'pseudo_id': peer_id,
            'status': 'isolated',
            'isolated_at': time.time(),
            'security_level': 'isolated',
            'keys_destroyed': True
        }
        app.logger.critical(f"  ↳ Unknown peer {peer_id[:8]}... ISOLATED from network")

def get_action_for_severity(severity: SeverityLevel) -> SecurityAction:
    """Map severity level to security action"""
    action_map = {
        SeverityLevel.LOW: SecurityAction.MONITORING,
        SeverityLevel.MEDIUM: SecurityAction.SESSION_TERMINATION,
        SeverityLevel.HIGH: SecurityAction.KEY_DESTRUCTION,
        SeverityLevel.CRITICAL: SecurityAction.PEER_ISOLATION
    }
    return action_map.get(severity, SecurityAction.MONITORING)

def get_action_description(severity):
    """Legacy function - Get description of action taken for each severity level"""
    if isinstance(severity, str):
        # Handle legacy string severity
        actions = {
            'LOW': 'monitoring',
            'MEDIUM': 'session_termination',
            'HIGH': 'key_destruction',
            'CRITICAL': 'peer_isolation'
        }
        return actions.get(severity, 'monitoring')
    elif isinstance(severity, SeverityLevel):
        return get_action_for_severity(severity).value
    else:
        return 'monitoring'

# ========================================
# VICTIM NOTIFICATION SYSTEM
# ========================================

def notify_session_termination(attacker_id: str, sessions_count: int, attack_type: AttackType, severity: SeverityLevel):
    """
    Notify victim peers about session termination (Level 2 Response)

    Sends real-time alerts to victim peers informing them that their
    sessions were terminated due to security threats
    """
    victim_ports = [8080, 8081, 8082]
    metrics = get_or_create_metrics(attacker_id)

    for port in victim_ports:
        if port == 8082:  # Skip attacker peer (assumption: 8082 is attacker)
            continue

        try:
            notification = {
                'type': 'SESSION_TERMINATED',
                'severity': severity.name,
                'attack_type': attack_type.value,
                'level': '2',
                'level_description': 'Session Termination',
                'message': (
                    f'⚠️  [LEVEL 2] Your session was terminated for security reasons.\n'
                    f'Attack Type: {attack_type.value}\n'
                    f'Attacker: {attacker_id[:8]}...\n'
                    f'Sessions affected: {sessions_count}\n'
                    f'Threat Score: {metrics.threat_score:.1f}/100'
                ),
                'attacker_id': attacker_id,
                'timestamp': time.time(),
                'threat_score': metrics.threat_score,
                'action_recommended': 'Wait 30-60 seconds, then reconnect to establish new secure session',
                'next_steps': 'Your connection was terminated to protect you from an ongoing attack. Safe to reconnect.',
                'security_level': severity.name
            }

            response = requests.post(
                f'http://{VICTIM_PEER_HOST}:{port}/api/security/notify',
                json=notification,
                timeout=2
            )

            if response.status_code == 200:
                app.logger.info(f"  ✅ Notified victim on port {port}")
            else:
                app.logger.warning(f"  ⚠️  Failed to notify port {port}: {response.status_code}")

        except requests.exceptions.Timeout:
            app.logger.warning(f"  ⏱️  Timeout notifying port {port}")
        except Exception as e:
            app.logger.error(f"  ❌ Failed to notify port {port}: {e}")

def notify_key_destruction(attacker_id: str, sessions_count: int, attack_type: AttackType, severity: SeverityLevel):
    """
    Notify victim peers about key destruction (Level 3 Response)

    Informs peers that attacker's encryption keys have been destroyed
    and that they should re-authenticate
    """
    victim_ports = [8080, 8081, 8082]
    metrics = get_or_create_metrics(attacker_id)

    for port in victim_ports:
        if port == 8082:  # Skip attacker peer
            continue

        try:
            notification = {
                'type': 'KEYS_DESTROYED',
                'severity': severity.name,
                'attack_type': attack_type.value,
                'level': '3',
                'level_description': 'Key Destruction',
                'message': (
                    f'🔐 [LEVEL 3] Encryption keys destroyed due to severe attack.\n'
                    f'Attack Type: {attack_type.value}\n'
                    f'Attacker: {attacker_id[:8]}...\n'
                    f'Sessions terminated: {sessions_count}\n'
                    f'Threat Score: {metrics.threat_score:.1f}/100\n'
                    f'All compromised keys have been destroyed.'
                ),
                'attacker_id': attacker_id,
                'timestamp': time.time(),
                'threat_score': metrics.threat_score,
                'action_recommended': 'Re-authenticate with trusted peers to establish new encrypted sessions',
                'next_steps': 'Attacker\'s encryption keys destroyed. Safe to reconnect with other legitimate peers.',
                'security_level': severity.name
            }

            response = requests.post(
                f'http://{VICTIM_PEER_HOST}:{port}/api/security/notify',
                json=notification,
                timeout=2
            )

            if response.status_code == 200:
                app.logger.info(f"  ✅ Notified victim on port {port}")
            else:
                app.logger.warning(f"  ⚠️  Failed to notify port {port}: {response.status_code}")

        except requests.exceptions.Timeout:
            app.logger.warning(f"  ⏱️  Timeout notifying port {port}")
        except Exception as e:
            app.logger.error(f"  ❌ Failed to notify port {port}: {e}")

def notify_peer_isolation(attacker_id: str, sessions_count: int, attack_type: AttackType, severity: SeverityLevel):
    """
    Notify victim peers about complete peer isolation (Level 4 Response)

    Informs all peers that the malicious peer has been completely
    isolated from the network and threat neutralized
    """
    victim_ports = [8080, 8081, 8082]
    metrics = get_or_create_metrics(attacker_id)

    for port in victim_ports:
        if port == 8082:  # Skip attacker peer
            continue

        try:
            notification = {
                'type': 'PEER_ISOLATED',
                'severity': severity.name,
                'attack_type': attack_type.value,
                'level': '4',
                'level_description': 'Peer Isolation',
                'message': (
                    f'🚫 [LEVEL 4] CRITICAL: Malicious peer completely isolated.\n'
                    f'Attack Type: {attack_type.value}\n'
                    f'Attacker: {attacker_id[:8]}...\n'
                    f'Sessions terminated: {sessions_count}\n'
                    f'Threat Score: {metrics.threat_score:.1f}/100\n'
                    f'Peer has been blocked from all network communications.\n'
                    f'⚠️ THREAT NEUTRALIZED ⚠️'
                ),
                'attacker_id': attacker_id,
                'timestamp': time.time(),
                'threat_score': metrics.threat_score,
                'action_recommended': 'Network is now secure. Safe to discover and connect to other peers',
                'next_steps': 'Threat completely neutralized. All communications safe to resume.',
                'security_level': severity.name,
                'network_secured': True
            }

            response = requests.post(
                f'http://{VICTIM_PEER_HOST}:{port}/api/security/notify',
                json=notification,
                timeout=2
            )

            if response.status_code == 200:
                app.logger.info(f"  ✅ Notified victim on port {port}")
            else:
                app.logger.warning(f"  ⚠️  Failed to notify port {port}: {response.status_code}")

        except requests.exceptions.Timeout:
            app.logger.warning(f"  ⏱️  Timeout notifying port {port}")
        except Exception as e:
            app.logger.error(f"  ❌ Failed to notify port {port}: {e}")

def notify_victim_peers(attacker_id: str, alert: dict):
    """
    Notify all victim peers about detected attack

    Sends real-time alerts to all peers (except attacker) about
    ongoing security threats
    """
    try:
        victim_ports = [8080, 8081]  # Victim peer ports (exclude attacker)
        metrics = get_or_create_metrics(attacker_id)

        for port in victim_ports:
            try:
                victim_alert = {
                    'type': alert['alert_type'],
                    'severity': alert['severity'],
                    'attack_type': alert['alert_type'],
                    'message': alert['message'],
                    'attacker_id': attacker_id,
                    'timestamp': alert['timestamp'],
                    'threat_score': metrics.threat_score,
                    'action_recommended': get_action_recommendation(alert['severity']),
                    'detection_method': alert.get('detection_method', 'AUTOMATIC'),
                    'security_state': metrics.state.value
                }

                app.logger.debug(f"  → Sending alert to port {port}")
                app.logger.debug(f" Victim Peer Host: {VICTIM_PEER_HOST}")

                response = requests.post(
                    f'http://{VICTIM_PEER_HOST}:{port}/api/security/notify',
                    json=victim_alert,
                    timeout=5
                )

                if response.status_code == 200:
                    app.logger.info(f"  ✅ Alert sent to peer on port {port}")
                else:
                    app.logger.warning(
                        f"  ⚠️  Failed to notify port {port}: "
                        f"{response.status_code} - {response.text[:100]}"
                    )

            except requests.exceptions.Timeout:
                app.logger.warning(f"  ⏱️  Timeout sending alert to port {port}")
            except Exception as e:
                app.logger.error(f"  ❌ Failed to notify port {port}: {e}")

    except Exception as e:
        app.logger.error(f"❌ Error in notify_victim_peers: {e}", exc_info=True)

def get_action_recommendation(severity):
    """Get recommended action for peers based on attack severity"""
    if isinstance(severity, str):
        recommendations = {
            'LOW': 'Monitor network activity - stay alert',
            'MEDIUM': 'Session may be terminated for security - reconnect if needed',
            'HIGH': 'Re-authentication required - establish new secure sessions',
            'CRITICAL': 'Attacker isolated - network is now secure'
        }
        return recommendations.get(severity, 'Stay vigilant')
    elif isinstance(severity, SeverityLevel):
        recommendations = {
            SeverityLevel.LOW: 'Monitor network activity - stay alert',
            SeverityLevel.MEDIUM: 'Session may be terminated for security - reconnect if needed',
            SeverityLevel.HIGH: 'Re-authentication required - establish new secure sessions',
            SeverityLevel.CRITICAL: 'Attacker isolated - network is now secure'
        }
        return recommendations.get(severity, 'Stay vigilant')
    return 'Stay vigilant'

# ========================================
# PEER RECOVERY AND RESTORATION
# ========================================

@app.route('/api/peer/recover', methods=['POST'])
def recover_isolated_peer():
    """
    Recover an isolated peer after cooldown period

    Allows administrators to restore a previously isolated peer
    after investigation or cooldown period expires
    """
    try:
        data = request.get_json()
        peer_id = data.get('peer_id')
        force_recovery = data.get('force', False)

        if not peer_id:
            return jsonify({'status': 'error', 'message': 'peer_id required'}), 400

        metrics = get_or_create_metrics(peer_id)

        # Check if peer is actually isolated
        if not metrics.isolated:
            return jsonify({
                'status': 'error',
                'message': 'Peer is not isolated'
            }), 400

        # Check cooldown period
        if not force_recovery and metrics.isolation_time:
            time_isolated = time.time() - metrics.isolation_time
            if time_isolated < SECURITY_CONFIG.recovery_cooldown:
                remaining = SECURITY_CONFIG.recovery_cooldown - time_isolated
                return jsonify({
                    'status': 'error',
                    'message': f'Cooldown period not expired. {remaining:.0f} seconds remaining',
                    'cooldown_remaining': remaining
                }), 403

        # Restore peer
        if peer_id in controller_state['peers']:
            controller_state['peers'][peer_id]['status'] = 'active'
            controller_state['peers'][peer_id]['security_level'] = 'recovered'
            controller_state['peers'][peer_id]['recovered_at'] = time.time()
            controller_state['peers'][peer_id]['keys_destroyed'] = False
            del controller_state['peers'][peer_id]['isolated_at']

        # Reset metrics (partial reset - keep history)
        metrics.isolated = False
        metrics.isolation_time = None
        metrics.current_severity = SeverityLevel.LOW
        update_peer_security_state(peer_id, PeerSecurityState.NORMAL)

        # Log recovery event
        security_events.append({
            'timestamp': time.time(),
            'event_type': 'PEER_RECOVERED',
            'details': {
                'peer_id': peer_id,
                'forced': force_recovery,
                'previous_threat_score': metrics.threat_score,
                'recovery_method': 'MANUAL' if force_recovery else 'AUTOMATIC'
            }
        })

        app.logger.info(
            f"🔓 Peer {peer_id[:8]}... recovered from isolation | "
            f"Previous threat score: {metrics.threat_score:.1f} | "
            f"Forced: {force_recovery}"
        )

        return jsonify({
            'status': 'success',
            'peer_id': peer_id,
            'recovered': True,
            'new_state': 'active',
            'security_state': PeerSecurityState.NORMAL.value
        })

    except Exception as e:
        app.logger.error(f"❌ Error recovering peer: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/metrics/peer/<peer_id>', methods=['GET'])
def get_peer_metrics(peer_id):
    """
    Get detailed security metrics for a specific peer

    Returns comprehensive attack statistics and threat analysis
    """
    try:
        if peer_id not in attack_metrics:
            return jsonify({
                'status': 'error',
                'message': 'Peer not found or no metrics available'
            }), 404

        metrics = attack_metrics[peer_id]

        return jsonify({
            'status': 'success',
            'peer_id': peer_id,
            'metrics': {
                'total_replay_attempts': metrics.total_replay_attempts,
                'total_flood_events': metrics.total_flood_events,
                'total_auth_failures': metrics.total_auth_failures,
                'suspicious_patterns': metrics.suspicious_patterns,
                'first_attack_time': metrics.first_attack_time,
                'last_attack_time': metrics.last_attack_time,
                'current_severity': metrics.current_severity.name,
                'security_state': metrics.state.value,
                'sessions_terminated': metrics.sessions_terminated,
                'keys_destroyed': metrics.keys_destroyed,
                'isolated': metrics.isolated,
                'isolation_time': metrics.isolation_time,
                'threat_score': metrics.threat_score,
                'attack_duration': (
                    metrics.last_attack_time - metrics.first_attack_time
                    if metrics.first_attack_time and metrics.last_attack_time
                    else 0
                )
            }
        })

    except Exception as e:
        app.logger.error(f"❌ Error fetching peer metrics: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/metrics/all', methods=['GET'])
def get_all_metrics():
    """
    Get security metrics for all peers

    Returns summary of all peer threat levels and attack statistics
    """
    try:
        all_metrics = []

        for peer_id, metrics in attack_metrics.items():
            all_metrics.append({
                'peer_id': peer_id,
                'threat_score': metrics.threat_score,
                'security_state': metrics.state.value,
                'severity': metrics.current_severity.name,
                'total_attacks': (
                    metrics.total_replay_attempts +
                    metrics.total_flood_events +
                    metrics.total_auth_failures
                ),
                'isolated': metrics.isolated,
                'keys_destroyed': metrics.keys_destroyed,
                'last_attack': metrics.last_attack_time
            })

        # Sort by threat score (highest first)
        all_metrics.sort(key=lambda x: x['threat_score'], reverse=True)

        return jsonify({
            'status': 'success',
            'total_peers_monitored': len(all_metrics),
            'isolated_peers': sum(1 for m in all_metrics if m['isolated']),
            'suspicious_peers': sum(1 for m in all_metrics if m['security_state'] != 'normal'),
            'metrics': all_metrics
        })

    except Exception as e:
        app.logger.error(f"❌ Error fetching all metrics: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/security/config', methods=['GET'])
def get_security_config():
    """Get current security configuration"""
    try:
        return jsonify({
            'status': 'success',
            'configuration': {
                'replay_thresholds': {
                    'low': SECURITY_CONFIG.replay_low_threshold,
                    'medium': SECURITY_CONFIG.replay_medium_threshold,
                    'high': SECURITY_CONFIG.replay_high_threshold,
                    'critical': SECURITY_CONFIG.replay_critical_threshold
                },
                'flood_thresholds': {
                    'low': SECURITY_CONFIG.flood_low_threshold,
                    'medium': SECURITY_CONFIG.flood_medium_threshold,
                    'high': SECURITY_CONFIG.flood_high_threshold,
                    'critical': SECURITY_CONFIG.flood_critical_threshold
                },
                'auth_thresholds': {
                    'low': SECURITY_CONFIG.auth_low_threshold,
                    'medium': SECURITY_CONFIG.auth_medium_threshold,
                    'high': SECURITY_CONFIG.auth_high_threshold,
                    'critical': SECURITY_CONFIG.auth_critical_threshold
                },
                'time_windows': {
                    'flood_detection': SECURITY_CONFIG.flood_detection_window,
                    'auth_detection': SECURITY_CONFIG.auth_detection_window,
                    'cleanup_interval': SECURITY_CONFIG.cleanup_interval,
                    'alert_retention': SECURITY_CONFIG.alert_retention
                },
                'features': {
                    'auto_escalation': SECURITY_CONFIG.auto_escalation_enabled,
                    'victim_notification': SECURITY_CONFIG.victim_notification_enabled,
                    'auto_recovery': SECURITY_CONFIG.auto_recovery_enabled,
                    'recovery_cooldown': SECURITY_CONFIG.recovery_cooldown
                }
            }
        })
    except Exception as e:
        app.logger.error(f"❌ Error fetching security config: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/security/config', methods=['PUT'])
def update_security_config():
    """
    Update security configuration dynamically

    Allows runtime adjustment of detection thresholds
    """
    try:
        data = request.get_json()
        updated_fields = []

        # Update replay thresholds
        if 'replay_thresholds' in data:
            for level, value in data['replay_thresholds'].items():
                if hasattr(SECURITY_CONFIG, f'replay_{level}_threshold'):
                    setattr(SECURITY_CONFIG, f'replay_{level}_threshold', value)
                    updated_fields.append(f'replay_{level}_threshold')

        # Update flood thresholds
        if 'flood_thresholds' in data:
            for level, value in data['flood_thresholds'].items():
                if hasattr(SECURITY_CONFIG, f'flood_{level}_threshold'):
                    setattr(SECURITY_CONFIG, f'flood_{level}_threshold', value)
                    updated_fields.append(f'flood_{level}_threshold')

        # Update auth thresholds
        if 'auth_thresholds' in data:
            for level, value in data['auth_thresholds'].items():
                if hasattr(SECURITY_CONFIG, f'auth_{level}_threshold'):
                    setattr(SECURITY_CONFIG, f'auth_{level}_threshold', value)
                    updated_fields.append(f'auth_{level}_threshold')

        # Update time windows
        if 'time_windows' in data:
            for key, value in data['time_windows'].items():
                if hasattr(SECURITY_CONFIG, f'{key}'):
                    setattr(SECURITY_CONFIG, key, value)
                    updated_fields.append(key)

        # Update features
        if 'features' in data:
            for key, value in data['features'].items():
                if hasattr(SECURITY_CONFIG, f'{key}_enabled' if key != 'recovery_cooldown' else key):
                    attr_name = f'{key}_enabled' if key != 'recovery_cooldown' else key
                    setattr(SECURITY_CONFIG, attr_name, value)
                    updated_fields.append(attr_name)

        # Log configuration change
        security_events.append({
            'timestamp': time.time(),
            'event_type': 'CONFIG_UPDATE',
            'details': {
                'updated_fields': updated_fields,
                'updated_by': request.remote_addr
            }
        })

        app.logger.info(f"⚙️  Security configuration updated: {updated_fields}")

        return jsonify({
            'status': 'success',
            'updated_fields': updated_fields,
            'message': f'Updated {len(updated_fields)} configuration fields'
        })

    except Exception as e:
        app.logger.error(f"❌ Error updating security config: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ========================================
# CLEANUP AND MAINTENANCE
# ========================================

def cleanup_monitor_data():
    """Clean up old monitoring data"""
    current_time = time.time()
    monitor = controller_state['network_monitor']
    
    # Clean auth attempts older than 1 hour
    for peer_id in list(monitor['auth_attempts'].keys()):
        monitor['auth_attempts'][peer_id] = [
            t for t in monitor['auth_attempts'][peer_id] 
            if current_time - t < 3600
        ]
    
    # Clean packet rates older than 1 hour
    for peer_id in list(monitor['packet_rates'].keys()):
        monitor['packet_rates'][peer_id] = [
            p for p in monitor['packet_rates'][peer_id] 
            if current_time - p['time'] < 3600
        ]
@app.route('/api/peer/register', methods=['POST'])
def register_peer():
    """Register a peer with the controller"""
    try:
        peer_data = request.get_json()
        peer_id = peer_data.get('pseudo_id')
        
        if not peer_id:
            return jsonify({'status': 'error', 'message': 'Peer ID required'}), 400
            
        # Register peer in controller state
        controller_state['peers'][peer_id] = {
            'pseudo_id': peer_id,
            'ip_address': peer_data.get('ip_address', request.remote_addr),
            'port': peer_data.get('port', 8080),
            'status': 'active',
            'security_level': 'normal',
            'last_seen': time.time(),
            'registered_at': time.time()
        }
        
        # Log security event
        security_events.append({
            'timestamp': time.time(),
            'event_type': 'PEER_REGISTERED',
            'details': {
                'peer_id': peer_id,
                'ip_address': controller_state['peers'][peer_id]['ip_address']
            }
        })
        
        app.logger.info(f"Peer registered: {peer_id} from {request.remote_addr}")
        
        return jsonify({
            'status': 'success',
            'peer_id': peer_id,
            'registered': True
        })
        
    except Exception as e:
        app.logger.error(f"Error registering peer: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/message/report', methods=['POST'])
def report_message():
    """Report message sent between peers"""
    try:
        data = request.get_json()
        message_size = data.get('message_size', 50)  # Default 50 bytes
        
        controller_state['message_count'] += 1
        controller_state['total_bytes'] += message_size
        
        app.logger.info(f"Message reported: size={message_size}, total_messages={controller_state['message_count']}")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        app.logger.error(f"Error reporting message: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/traffic/stats', methods=['GET'])
def get_traffic_stats():
    """Get traffic statistics"""
    # Use actual message counts
    total_packets = controller_state['message_count']
    total_bytes = controller_state['total_bytes']
    suspicious_packets = 0  # No attacks detected yet
    
    # Calculate packets per second - simulate some activity if sessions exist
    active_sessions = len(controller_state['sessions'])
    if active_sessions > 0:
        packets_per_second = active_sessions * 5  # More visible activity
    elif total_packets > 0:
        packets_per_second = 3  # Show some activity if messages were sent
    else:
        packets_per_second = 1  # Baseline activity
    
    return jsonify({
        'total_packets': total_packets,
        'bytes_transferred': total_bytes,
        'packets_per_second': packets_per_second,
        'suspicious_packets': suspicious_packets,
        'active_flows': len(controller_state['flows'])
    })

@app.route('/api/security/attacks', methods=['GET'])
def get_attack_data():
    """Get attack detection data"""
    # Convert alerts to attack format
    attacks = []
    for alert in active_alerts:
        attacks.append({
            'id': alert['id'],
            'attack_type': alert['alert_type'].replace('_ATTACK', '').lower(),
            'source_ip': '192.168.1.99',  # Simulated attacker IP
            'severity': alert['severity'].lower(),
            'status': 'blocked' if alert['severity'] == 'HIGH' else 'active',
            'detected_at': alert['timestamp'],
            'response_action': alert.get('action_taken', 'monitoring')
        })
    
    return jsonify(attacks)

@app.route('/api/logs', methods=['GET'])
def get_system_logs():
    """Get system logs"""
    logs = []
    
    # Convert security events to log format
    for event in security_events[-50:]:  # Last 50 events
        log_level = 'info'
        if event['event_type'] in ['ATTACK_DETECTED', 'SECURITY_ALERT']:
            log_level = 'error'
        elif event['event_type'] in ['SESSION_TERMINATE']:
            log_level = 'warning'
        elif event['event_type'] in ['SESSION_START', 'PEER_REGISTERED']:
            log_level = 'success'
            
        logs.append({
            'timestamp': event['timestamp'],
            'level': log_level,
            'component': 'SDN Controller',
            'message': f"{event['event_type'].replace('_', ' ').title()}",
            'details': event.get('details', {})
        })
    
    return jsonify(logs)

@app.route('/api/session/report', methods=['POST'])
def report_session():
    """Report session status from peers"""
    try:
        session_data = request.get_json()
        peer_id = session_data.get('peer_id')
        session_active = session_data.get('session_active', False)
        connected_peer = session_data.get('connected_peer')
        
        app.logger.info(f"Session report from {peer_id}: active={session_active}, connected_to={connected_peer}")
        
        if not peer_id:
            return jsonify({'status': 'error', 'message': 'Peer ID required'}), 400
            
        if session_active and connected_peer:
            # Create or update session record
            session_id = f"{min(peer_id, connected_peer)}_{max(peer_id, connected_peer)}"
            controller_state['sessions'][session_id] = {
                'id': session_id,
                'peer_a': peer_id,
                'peer_b': connected_peer,
                'start_time': time.time(),
                'status': 'active',
                'last_update': time.time()
            }
            
            app.logger.info(f"Session created/updated: {session_id}")
        else:
            # Remove sessions involving this peer
            sessions_to_remove = []
            for session_id, session in controller_state['sessions'].items():
                if peer_id in [session['peer_a'], session['peer_b']]:
                    sessions_to_remove.append(session_id)
                    
            for session_id in sessions_to_remove:
                del controller_state['sessions'][session_id]
                app.logger.info(f"Session removed: {session_id}")
        
        app.logger.info(f"Total active sessions: {len(controller_state['sessions'])}")
        return jsonify({'status': 'success', 'sessions_active': len(controller_state['sessions'])})
        
    except Exception as e:
        app.logger.error(f"Error reporting session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/debug/state', methods=['GET'])
def get_debug_state():
    """Debug endpoint to check controller state"""
    return jsonify({
        'controller_active': controller_state['active'],
        'peers_count': len(controller_state['peers']),
        'sessions_count': len(controller_state['sessions']),
        'peers': list(controller_state['peers'].keys()),
        'sessions': controller_state['sessions'],
        'alerts_count': len(active_alerts),
        'events_count': len(security_events)
    })

@app.route('/api/peer/isolate', methods=['POST'])
def isolate_peer():
    """Isolate a peer from the network"""
    try:
        data = request.get_json()
        peer_id = data.get('peer_id')
        reason = data.get('reason', 'Security violation')
        
        if peer_id in controller_state['peers']:
            controller_state['peers'][peer_id]['status'] = 'isolated'
            controller_state['peers'][peer_id]['isolation_reason'] = reason
            controller_state['peers'][peer_id]['isolated_at'] = time.time()
            
            # Log isolation event
            security_events.append({
                'timestamp': time.time(),
                'event_type': 'PEER_ISOLATED',
                'details': {
                    'peer_id': peer_id,
                    'reason': reason
                }
            })
            
            app.logger.warning(f"Peer {peer_id} isolated: {reason}")
            return jsonify({'status': 'success', 'peer_isolated': True})
            
        return jsonify({'status': 'error', 'message': 'Peer not found'}), 404
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/controller/start', methods=['POST'])
def start_controller():
    """
    Start the SDN Progressive Self-Destruct Controller

    Activates the security monitoring and progressive response system
    """
    controller_state['active'] = True
    controller_state['start_time'] = time.time()

    security_events.append({
        'timestamp': time.time(),
        'event_type': 'CONTROLLER_START',
        'details': {
            'message': 'SDN Progressive Self-Destruct Controller activated',
            'version': '2.0',
            'features': [
                'Progressive attack response',
                'Real-time threat detection',
                'Automatic peer isolation',
                'Victim notification system'
            ]
        }
    })

    app.logger.info(
        "🚀 SDN Progressive Self-Destruct Controller STARTED | "
        "Monitoring: ACTIVE | Auto-escalation: ENABLED"
    )

    return jsonify({
        'status': 'success',
        'controller_active': True,
        'start_time': controller_state['start_time'],
        'message': 'Progressive Self-Destruct System Online'
    })

@app.route('/api/controller/stop', methods=['POST'])
def stop_controller():
    """
    Stop the SDN Progressive Self-Destruct Controller

    Deactivates the security monitoring system
    """
    uptime = time.time() - controller_state.get('start_time', time.time())
    controller_state['active'] = False

    # Get final statistics
    total_attacks = sum(
        m.total_replay_attempts + m.total_flood_events + m.total_auth_failures
        for m in attack_metrics.values()
    )
    isolated_peers = sum(1 for m in attack_metrics.values() if m.isolated)

    security_events.append({
        'timestamp': time.time(),
        'event_type': 'CONTROLLER_STOP',
        'details': {
            'message': 'SDN Progressive Self-Destruct Controller deactivated',
            'uptime': uptime,
            'total_attacks_detected': total_attacks,
            'peers_isolated': isolated_peers,
            'total_alerts': len(active_alerts)
        }
    })

    app.logger.warning(
        f"🛑 SDN Controller STOPPED | "
        f"Uptime: {uptime:.0f}s | "
        f"Attacks detected: {total_attacks} | "
        f"Peers isolated: {isolated_peers}"
    )

    return jsonify({
        'status': 'success',
        'controller_active': False,
        'uptime': uptime,
        'statistics': {
            'total_attacks': total_attacks,
            'peers_isolated': isolated_peers,
            'total_alerts': len(active_alerts)
        }
    })

def cleanup_old_data():
    """Background task to cleanup old alerts and events"""
    while True:
        try:
            current_time = time.time()
            
            # Remove alerts older than 1 hour
            global active_alerts
            active_alerts = [
                alert for alert in active_alerts 
                if current_time - alert['timestamp'] < 3600
            ]
            
            # Keep only last 1000 security events
            global security_events
            if len(security_events) > 1000:
                security_events = security_events[-1000:]
                
            time.sleep(300)  # Cleanup every 5 minutes
            
        except Exception as e:
            app.logger.error(f"Cleanup error: {e}")

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_data)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)