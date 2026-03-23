# SDN Security System - Complete Testing Guide

## Testing Overview
This guide will help you test all components of your SDN-based anonymous P2P communication system, including the progressive attack-triggered self-destruct mechanism.

## Prerequisites
- All 5 applications running:
  1. SDN Controller (WSL2)
  2. Controller Backend API (WSL2)
  3. Controller Dashboard (Windows)
  4. Peer Backend (Windows)
  5. Peer Dashboard (Windows)

## Testing Phases

### Phase 1: System Health Check
**Objective**: Verify all components are communicating properly

1. **Check Controller Dashboard** (http://localhost:3001)
   - Should show "Network Status: Active"
   - Traffic monitor should show baseline activity
   - No attacks detected initially

2. **Check Peer Dashboard** (http://localhost:3000)
   - Should show "Scanning for peers..."
   - Network status should be "Connected"

### Phase 2: Normal Peer Communication Test
**Objective**: Test legitimate peer-to-peer communication

1. **Peer Discovery**:
   - Open Peer Dashboard
   - Should automatically discover available peers
   - Select a peer to connect

2. **Anonymous Authentication**:
   - Click "Connect" to a peer
   - Watch authentication process (pseudo-ID, nonce, timestamp)
   - Session should establish successfully

3. **Secure Chat**:
   - Send test messages between peers
   - Verify messages are encrypted in transit
   - Check Controller Dashboard shows normal traffic

### Phase 3: Attack Simulation & Progressive Response
**Objective**: Test the 4-level progressive self-destruct mechanism

#### Level 1 - Monitoring & Warning
1. **Run Low-Severity Attack**:
   ```bash
   # In WSL2 terminal
   cd /mnt/c/Users/charan27/OneDrive/Desktop/Final\ Year\ Projects/SDN/attack-scripts
   python3 attack_simulator.py --attack-type replay --intensity low
   ```

2. **Expected Behavior**:
   - Controller Dashboard shows "LOW" severity alert
   - Peer receives warning notification
   - Session continues normally
   - Increased logging visible

#### Level 2 - Session Termination
1. **Run Medium-Severity Attack**:
   ```bash
   python3 attack_simulator.py --attack-type flooding --intensity medium
   ```

2. **Expected Behavior**:
   - Controller Dashboard shows "MEDIUM" severity
   - Active session terminates immediately
   - Peers disconnected but can reconnect
   - Suspicious flow blocked

#### Level 3 - Key Destruction
1. **Run High-Severity Attack**:
   ```bash
   python3 attack_simulator.py --attack-type replay --intensity high
   ```

2. **Expected Behavior**:
   - Controller Dashboard shows "HIGH" severity
   - Session keys destroyed
   - Pseudo-identity invalidated
   - Re-authentication required

#### Level 4 - Peer Isolation
1. **Run Critical Attack**:
   ```bash
   python3 attack_simulator.py --attack-type flooding --intensity critical
   ```

2. **Expected Behavior**:
   - Controller Dashboard shows "CRITICAL" severity
   - Attacker peer completely isolated
   - All traffic from attacker blocked
   - Permanent isolation status

### Phase 4: Security Verification
**Objective**: Verify security features work correctly

1. **Encryption Verification**:
   - Monitor network traffic during chat
   - Verify messages are encrypted
   - Confirm no plaintext leakage

2. **Session Management**:
   - Verify keys exist only in memory
   - Confirm no chat history stored
   - Test session cleanup on disconnect

3. **Anonymous Authentication**:
   - Verify no real identity exposure
   - Check pseudo-ID generation
   - Confirm nonce uniqueness

## Demo Scenarios

### Scenario 1: Business Demo
**"Secure Communication Under Attack"**

1. Start with normal peer communication
2. Show encrypted message exchange
3. Simulate progressive attacks
4. Demonstrate system's defensive response
5. Show complete isolation of attacker

### Scenario 2: Technical Demo
**"SDN Security Architecture"**

1. Explain SDN controller monitoring
2. Show real-time traffic analysis
3. Demonstrate attack detection algorithms
4. Walk through progressive response levels
5. Show security policy enforcement

## Troubleshooting Common Issues

### Issue 1: Peers Not Discovering
- Check if peer backend is running on correct port
- Verify network connectivity
- Restart peer discovery service

### Issue 2: Authentication Failing
- Check timestamp synchronization
- Verify nonce generation
- Restart peer backend

### Issue 3: Attacks Not Detected
- Verify SDN controller is monitoring
- Check attack script parameters
- Ensure controller API is responding

### Issue 4: UI Not Updating
- Check WebSocket connections
- Verify API endpoints
- Refresh browser cache

## Performance Metrics to Monitor

1. **Response Time**: Attack detection to action
2. **Accuracy**: False positive/negative rates
3. **Throughput**: Messages per second during normal operation
4. **Recovery Time**: System restoration after attack

## Success Criteria

✅ **Normal Operation**:
- Peers discover each other automatically
- Authentication completes successfully
- Messages encrypt/decrypt properly
- No false attack alerts

✅ **Attack Response**:
- All 4 severity levels trigger correctly
- Progressive actions execute in order
- System isolates attackers effectively
- Legitimate peers remain unaffected

✅ **Security**:
- No plaintext message leakage
- Keys destroyed on high-severity attacks
- No persistent storage of sensitive data
- Anonymous authentication works

## Next Steps After Testing

1. **Document Results**: Record all test outcomes
2. **Performance Tuning**: Optimize based on test results
3. **Demo Preparation**: Prepare presentation materials
4. **Client Presentation**: Schedule final demonstration

## Emergency Reset Commands

If system gets stuck during testing:

```bash
# Reset SDN Controller (WSL2)
sudo pkill -f ryu-manager
sudo ovs-vsctl del-br br0
# Restart from installation guide step 4

# Reset Peer Applications (Windows)
# Stop all Node.js and Python processes
# Restart from installation guide step 6
```