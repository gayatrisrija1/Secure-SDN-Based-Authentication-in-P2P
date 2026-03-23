#!/usr/bin/env python3
"""
SDN Controller with Progressive Attack-Triggered Self-Destruct
Monitors traffic patterns and implements graduated security responses
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp
import time
import json
from collections import defaultdict, deque
from enum import Enum
import threading
import logging

class AttackSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class SecurityAction(Enum):
    MONITOR = "monitoring"
    WARN = "warning"
    TERMINATE_SESSION = "session_termination"
    DESTROY_KEYS = "key_destruction"
    ISOLATE_PEER = "peer_isolation"

class SDNSecurityController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(SDNSecurityController, self).__init__(*args, **kwargs)
        
        # Traffic monitoring data structures
        self.mac_to_port = {}
        self.flow_stats = defaultdict(lambda: {
            'packet_count': 0,
            'byte_count': 0,
            'first_seen': time.time(),
            'last_seen': time.time(),
            'packet_times': deque(maxlen=100)  # Track timing patterns
        })
        
        # Attack detection state
        self.peer_security_state = defaultdict(lambda: {
            'severity': AttackSeverity.LOW,
            'suspicious_flows': 0,
            'replay_attempts': 0,
            'flood_score': 0,
            'last_action': None,
            'isolated': False
        })
        
        # Security thresholds
        self.thresholds = {
            'replay_detection_window': 5.0,  # seconds
            'flood_rate_limit': 50,  # packets per second
            'suspicious_flow_limit': 10,
            'replay_attempt_limit': 3
        }
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._continuous_monitoring)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info("SDN Security Controller initialized with progressive self-destruct")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection and install default flow"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Install default flow to send packets to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                        ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        self.logger.info(f"Switch {datapath.id} connected - security monitoring active")

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Add flow entry to switch"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                  priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                  match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle incoming packets and perform security analysis"""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocols(ethernet.ethernet)[0]
        
        # Skip LLDP and other control packets
        if eth_pkt.ethertype == 0x88cc:
            return
            
        dst = eth_pkt.dst
        src = eth_pkt.src
        
        # Learn MAC addresses
        self.mac_to_port.setdefault(datapath.id, {})
        self.mac_to_port[datapath.id][src] = in_port
        
        # Security analysis
        current_time = time.time()
        flow_key = f"{src}->{dst}"
        
        # Update flow statistics
        flow_stat = self.flow_stats[flow_key]
        flow_stat['packet_count'] += 1
        flow_stat['byte_count'] += len(msg.data)
        flow_stat['last_seen'] = current_time
        flow_stat['packet_times'].append(current_time)
        
        # Perform attack detection
        attack_detected, severity = self._analyze_traffic_patterns(src, flow_key, current_time)
        
        if attack_detected:
            self._handle_security_event(src, severity, datapath)
            
        # Check if peer is isolated
        if self.peer_security_state[src]['isolated']:
            self.logger.warning(f"Dropping packet from isolated peer {src}")
            return
            
        # Normal forwarding logic
        if dst in self.mac_to_port[datapath.id]:
            out_port = self.mac_to_port[datapath.id][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
            
        actions = [parser.OFPActionOutput(out_port)]
        
        # Install flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions, msg.buffer_id)
            
        # Send packet out
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
            
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def _analyze_traffic_patterns(self, src_mac, flow_key, current_time):
        """Analyze traffic for attack patterns"""
        flow_stat = self.flow_stats[flow_key]
        peer_state = self.peer_security_state[src_mac]
        
        # Replay attack detection
        replay_detected = self._detect_replay_attack(flow_stat, current_time)
        
        # Flood attack detection  
        flood_detected = self._detect_flood_attack(flow_stat, current_time)
        
        # Calculate overall severity
        severity = AttackSeverity.LOW
        
        if replay_detected:
            peer_state['replay_attempts'] += 1
            severity = AttackSeverity.MEDIUM
            
        if flood_detected:
            peer_state['flood_score'] += 1
            severity = max(severity, AttackSeverity.HIGH)
            
        # Escalate severity based on repeated violations
        if peer_state['replay_attempts'] > self.thresholds['replay_attempt_limit']:
            severity = AttackSeverity.CRITICAL
            
        if peer_state['flood_score'] > 5:
            severity = AttackSeverity.CRITICAL
            
        peer_state['severity'] = severity
        
        return (replay_detected or flood_detected), severity

    def _detect_replay_attack(self, flow_stat, current_time):
        """Detect replay attacks based on timing patterns"""
        if len(flow_stat['packet_times']) < 3:
            return False
            
        # Check for suspicious timing patterns
        recent_times = list(flow_stat['packet_times'])[-10:]
        intervals = [recent_times[i+1] - recent_times[i] for i in range(len(recent_times)-1)]
        
        # Detect identical intervals (potential replay)
        if len(set(f"{interval:.3f}" for interval in intervals)) == 1 and len(intervals) > 2:
            return True
            
        return False

    def _detect_flood_attack(self, flow_stat, current_time):
        """Detect flood attacks based on packet rate"""
        if len(flow_stat['packet_times']) < 10:
            return False
            
        # Calculate packets per second in last window
        window_start = current_time - 1.0  # 1 second window
        recent_packets = [t for t in flow_stat['packet_times'] if t > window_start]
        
        if len(recent_packets) > self.thresholds['flood_rate_limit']:
            return True
            
        return False

    def _handle_security_event(self, src_mac, severity, datapath):
        """Implement progressive self-destruct response"""
        peer_state = self.peer_security_state[src_mac]
        current_time = time.time()
        
        action_taken = None
        
        if severity == AttackSeverity.LOW:
            # Level 1: Monitoring & Warning
            action_taken = SecurityAction.MONITOR
            self.logger.info(f"Level 1 Response: Monitoring peer {src_mac}")
            
        elif severity == AttackSeverity.MEDIUM:
            # Level 2: Session Termination
            action_taken = SecurityAction.TERMINATE_SESSION
            self._terminate_peer_sessions(src_mac)
            self.logger.warning(f"Level 2 Response: Terminating sessions for {src_mac}")
            
        elif severity == AttackSeverity.HIGH:
            # Level 3: Key Destruction
            action_taken = SecurityAction.DESTROY_KEYS
            self._destroy_peer_keys(src_mac)
            self.logger.error(f"Level 3 Response: Destroying keys for {src_mac}")
            
        elif severity == AttackSeverity.CRITICAL:
            # Level 4: Peer Isolation
            action_taken = SecurityAction.ISOLATE_PEER
            self._isolate_peer(src_mac, datapath)
            self.logger.critical(f"Level 4 Response: Isolating peer {src_mac}")
            
        peer_state['last_action'] = {
            'action': action_taken,
            'timestamp': current_time,
            'severity': severity
        }

    def _terminate_peer_sessions(self, src_mac):
        """Terminate active sessions for a peer"""
        # Signal to peer applications to terminate sessions
        self._send_security_alert(src_mac, "SESSION_TERMINATION", 
                                "Suspicious activity detected - terminating session")

    def _destroy_peer_keys(self, src_mac):
        """Destroy encryption keys for a peer"""
        # Signal to peer applications to destroy keys
        self._send_security_alert(src_mac, "KEY_DESTRUCTION", 
                                "Security breach detected - destroying encryption keys")

    def _isolate_peer(self, src_mac, datapath):
        """Completely isolate a peer from the network"""
        peer_state = self.peer_security_state[src_mac]
        peer_state['isolated'] = True
        
        # Install flow rules to drop all traffic from this peer
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_src=src_mac)
        actions = []  # Empty actions = drop
        self.add_flow(datapath, 100, match, actions)  # High priority
        
        self._send_security_alert(src_mac, "PEER_ISOLATION", 
                                "Critical security violation - peer isolated")

    def _send_security_alert(self, peer_mac, alert_type, message):
        """Send security alerts to peer applications"""
        alert = {
            'timestamp': time.time(),
            'peer_mac': peer_mac,
            'alert_type': alert_type,
            'message': message,
            'severity': self.peer_security_state[peer_mac]['severity'].name
        }
        
        # In a real implementation, this would use a message queue or API
        self.logger.info(f"Security Alert: {json.dumps(alert, indent=2)}")

    def _continuous_monitoring(self):
        """Background thread for continuous security monitoring"""
        while self.monitoring_active:
            try:
                current_time = time.time()
                
                # Clean up old flow statistics
                expired_flows = []
                for flow_key, stats in self.flow_stats.items():
                    if current_time - stats['last_seen'] > 300:  # 5 minutes
                        expired_flows.append(flow_key)
                        
                for flow_key in expired_flows:
                    del self.flow_stats[flow_key]
                    
                # Reset flood scores periodically
                for peer_state in self.peer_security_state.values():
                    if peer_state['flood_score'] > 0:
                        peer_state['flood_score'] = max(0, peer_state['flood_score'] - 1)
                        
                time.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")

    def get_security_status(self):
        """Get current security status for API"""
        return {
            'active_flows': len(self.flow_stats),
            'monitored_peers': len(self.peer_security_state),
            'isolated_peers': sum(1 for state in self.peer_security_state.values() 
                                if state['isolated']),
            'high_risk_peers': sum(1 for state in self.peer_security_state.values() 
                                 if state['severity'] in [AttackSeverity.HIGH, AttackSeverity.CRITICAL])
        }

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Start the controller
    from ryu.cmd import manager
    manager.main()