# SDN-Based Progressive Self-Destruct - Complete Implementation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SDN Controller                            │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  api_server.py   │◄───────►│ security_ctrl.py │         │
│  │  (Flask REST)    │  calls  │  (Ryu OpenFlow)  │         │
│  └──────────────────┘         └──────────────────┘         │
│          │                              │                    │
│          │ HTTP/REST                    │ OpenFlow          │
│          ▼                              ▼                    │
│   ┌────────────┐                ┌─────────────┐            │
│   │   Peers    │                │   Switch    │            │
│   └────────────┘                └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Components

### 1. MAC Address Tracking
**Purpose**: Map pseudo_id → MAC address for flow rules

**File**: `sdn-controller/api_server.py`
```python
# Global peer registry
peer_registry = {
    'pseudo_id': {
        'mac_address': 'aa:bb:cc:dd:ee:ff',
        'ip_address': '192.168.1.99',
        'port': 8080,
        'last_seen': timestamp
    }
}
```

### 2. Progressive Defense with Flow Rules

#### Level 1 - LOW (Monitoring)
**Actions:**
- ✅ Log traffic
- ✅ Calculate threat score
- ❌ No flow rules (monitoring only)

#### Level 2 - MEDIUM (Session Termination)
**Actions:**
- ✅ Terminate session (notify victims)
- ✅ **Install flow rules**: Block packets from attacker to victims
- ✅ Application-level blocking

**OpenFlow Rule:**
```python
# Block traffic: attacker → victim
match = parser.OFPMatch(
    eth_src=attacker_mac,
    eth_dst=victim_mac
)
actions = []  # DROP
priority = 50
```

#### Level 3 - HIGH (Key Destruction)
**Actions:**
- ✅ Delete session keys (notify victims)
- ✅ **Invalidate pseudo-identity** (force re-registration)
- ✅ **Install flow rules**: Block ALL new connections from attacker
- ✅ Application-level blocking

**OpenFlow Rule:**
```python
# Block all outgoing traffic from attacker
match = parser.OFPMatch(eth_src=attacker_mac)
actions = []  # DROP all
priority = 75
```

**Pseudo-ID Invalidation:**
```python
# Notify attacker to regenerate identity
{
    'action': 'INVALIDATE_IDENTITY',
    'reason': 'Security violation - HIGH level',
    'must_regenerate': True
}
```

#### Level 4 - CRITICAL (Complete Isolation)
**Actions:**
- ✅ Peer isolation (notify ALL peers)
- ✅ **Install flow rules**: Block ALL traffic (in/out)
- ✅ **Permanent ban** from network
- ✅ Remove from peer discovery globally

**OpenFlow Rules:**
```python
# Block all incoming traffic
match_in = parser.OFPMatch(eth_dst=attacker_mac)
actions = []
priority = 100

# Block all outgoing traffic
match_out = parser.OFPMatch(eth_src=attacker_mac)
actions = []
priority = 100
```

### 3. Integration Points

#### A. API Server → Security Controller
**Method 1: Direct Function Call** (if same process)
```python
from security_controller import SDNSecurityController
security_ctrl = SDNSecurityController()

# Call from api_server:
security_ctrl.block_flow(attacker_mac, victim_mac, priority=50)
```

**Method 2: REST API** (if separate processes)
```python
# Security controller exposes REST API:
@app.route('/api/sdn/block_flow', methods=['POST'])
def block_flow():
    data = request.json
    install_blocking_rule(
        attacker_mac=data['attacker_mac'],
        victim_mac=data.get('victim_mac'),
        priority=data['priority']
    )
```

#### B. Peer Registration with MAC Address
```python
@app.route('/api/peer/register', methods=['POST'])
def register_peer():
    data = request.json
    peer_registry[data['pseudo_id']] = {
        'mac_address': data['mac_address'],  # Required!
        'ip_address': data['ip_address'],
        'port': data['port']
    }
```

### 4. Flow Rule Management

#### Installation
```python
def install_blocking_rule(datapath, attacker_mac, victim_mac=None, priority=50):
    """Install OpenFlow rule to drop packets"""
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto

    if victim_mac:
        # Block specific flow: attacker → victim
        match = parser.OFPMatch(
            eth_src=attacker_mac,
            eth_dst=victim_mac
        )
    else:
        # Block all traffic from attacker
        match = parser.OFPMatch(eth_src=attacker_mac)

    # Empty actions = DROP
    actions = []

    # Install flow
    inst = [parser.OFPInstructionActions(
        ofproto.OFPIT_APPLY_ACTIONS, actions)]

    mod = parser.OFPFlowMod(
        datapath=datapath,
        priority=priority,
        match=match,
        instructions=inst,
        idle_timeout=0,     # Permanent
        hard_timeout=0,     # Permanent
        flags=ofproto.OFPFF_SEND_FLOW_REM
    )

    datapath.send_msg(mod)
```

#### Removal (if needed)
```python
def remove_blocking_rule(datapath, attacker_mac, victim_mac=None):
    """Remove OpenFlow blocking rule"""
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto

    if victim_mac:
        match = parser.OFPMatch(
            eth_src=attacker_mac,
            eth_dst=victim_mac
        )
    else:
        match = parser.OFPMatch(eth_src=attacker_mac)

    mod = parser.OFPFlowMod(
        datapath=datapath,
        command=ofproto.OFPFC_DELETE,
        out_port=ofproto.OFPP_ANY,
        out_group=ofproto.OFPG_ANY,
        match=match
    )

    datapath.send_msg(mod)
```

## Implementation Files

### Files to Modify:
1. **api_server.py** - Add MAC tracking, flow rule triggers
2. **security_controller.py** - Add flow installation methods
3. **peer_app.py** - Send MAC address during registration, handle identity invalidation
4. **peer-backend-2.py** - Same as peer_app.py
5. **peer-backend-3.py** - Same as peer_app.py

### New Files to Create:
1. **sdn_flow_manager.py** - Flow rule management utilities
2. **peer_registry.py** - Centralized peer tracking

## Testing Strategy

### Test 1: MEDIUM Level Flow Rules
```bash
# 1. Start all components
# 2. Connect Peer 1 to Peer 3
# 3. Launch MEDIUM attack (3 attacks)
# 4. Verify:
#    - Flow rule installed (check switch)
#    - Peer 1 can't receive packets from Peer 3
#    - Peer 1 CAN still talk to Peer 2
```

### Test 2: HIGH Level Identity Invalidation
```bash
# 1. Launch HIGH attack (5 attacks)
# 2. Verify:
#    - Peer 3 receives INVALIDATE_IDENTITY notification
#    - Pseudo-ID forced to regenerate
#    - Must re-register with controller
#    - Flow rules block all traffic from old MAC
```

### Test 3: CRITICAL Level Complete Isolation
```bash
# 1. Launch CRITICAL attack (8 attacks)
# 2. Verify:
#    - Flow rules block all traffic (in AND out)
#    - Peer 3 cannot ping any peer
#    - Peer 3 removed from discovery
#    - Permanent ban persists across restarts
```

## Verification Commands

### Check Flow Rules:
```bash
# OpenFlow switch:
sudo ovs-ofctl dump-flows <bridge_name>

# Should see:
# priority=100,dl_src=<attacker_mac> actions=drop
# priority=100,dl_dst=<attacker_mac> actions=drop
```

### Check Peer Registry:
```bash
curl http://localhost:5000/api/peers/registry
```

### Simulate Traffic:
```bash
# Try to ping from attacker:
ping <victim_ip>  # Should fail if flow rules work
```

## Implementation Phases

### Phase 1: Foundation (Day 1)
- [ ] Add MAC address tracking in api_server
- [ ] Peer registration includes MAC
- [ ] Create flow rule utility functions

### Phase 2: Flow Rules (Day 2)
- [ ] MEDIUM: Block specific flows
- [ ] HIGH: Block all from attacker
- [ ] CRITICAL: Complete isolation

### Phase 3: Identity Management (Day 3)
- [ ] Pseudo-ID invalidation at HIGH level
- [ ] Force re-registration mechanism
- [ ] Identity regeneration logic

### Phase 4: Testing & Validation (Day 4)
- [ ] Test each level independently
- [ ] Verify flow rules in switch
- [ ] Network-level packet capture
- [ ] End-to-end integration testing

## Success Criteria

| Level | Criterion | Verification |
|-------|-----------|--------------|
| MEDIUM | Flow rule blocks attacker→victim | Packet capture shows drops |
| HIGH | Pseudo-ID invalidated | Attacker must re-register |
| CRITICAL | Complete isolation | No packets in/out from attacker |

## Documentation

All implementation will include:
- ✅ Inline code comments
- ✅ API documentation
- ✅ Testing procedures
- ✅ Troubleshooting guide

---

**Next Steps**: Implement Phase 1 - Foundation

