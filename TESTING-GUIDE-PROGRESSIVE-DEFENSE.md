# Complete Testing Guide: 4-Level Progressive Defense

## Prerequisites

### 1. Make sure all components are running:

**Controller (WSL/Ubuntu):**
```bash
cd ~/sdn-controller  # or /mnt/c/Users/charan27/OneDrive/Desktop/SDN/sdn-controller
export VICTIM_PEER_HOST=192.168.2.125  # Your Windows IP
python3 api_server.py
```

**Peer 1 - Victim (Windows Terminal 1):**
```bash
cd peer-backend
python peer_app.py
```

**Peer 2 - Victim (Windows Terminal 2):**
```bash
cd peer-backend-2
python peer-backend-2.py
```

**Peer 3 - Attacker (Windows Terminal 3):**
```bash
cd peer-backend-3
python peer-backend-3.py
```

**Dashboards (4 separate browser tabs):**
- Controller: http://localhost:3004
- Peer 1: http://localhost:3000
- Peer 2: http://localhost:3001
- Peer 3: http://localhost:3002

### 2. Clear previous test data:
```bash
# In Windows Command Prompt or PowerShell:
curl -X DELETE http://localhost:8080/api/peer/alerts
curl -X DELETE http://localhost:8081/api/peer/alerts
```

---

## SCENARIO 1: Victim Connected to Attacker

**Setup:** Victim peer establishes session with attacker, then attacker launches attacks.

### Setup Phase:

1. **Start Peer 1** (http://localhost:3000)
   - Click "Start Peer"
   - Go to "Peer Discovery" tab
   - Wait for peers to appear

2. **Connect Peer 1 to Attacker (Peer 3)**
   - Look for Peer 3 in discovered peers
   - Click "Connect" on Peer 3
   - Peer 3 should see connection request
   - Peer 3 accepts the request
   - Both should now show "Active Session"

3. **Verify Connection**
   - Go to "Secure Chat" tab on both peers
   - Send a test message
   - Confirm chat works

---

### LEVEL 1 (LOW) - Monitoring Only

**Trigger:** Launch 1-2 replay attacks (LOW intensity)

**From Peer 3 Dashboard:**
1. Click "Attack Panel" tab
2. Select: Attack Type = "Replay Attack"
3. Select: Intensity = "LOW"
4. Click "Launch Attack"
5. Wait 2-3 seconds, launch again

**Expected Controller Logs:**
```
INFO:api_server:🔐 Peer [attacker_id]... security state: normal → suspicious
WARNING:api_server:🚨 REPLAY ATTACK detected from [attacker_id]... | Total replays: 1 | Severity: LOW | Threat score: 15.0
DEBUG:api_server:  → Sending alert to port 8080
INFO:api_server:  ✅ Alert sent to peer on port 8080
DEBUG:api_server:  → Sending alert to port 8081
INFO:api_server:  ✅ Alert sent to peer on port 8081
INFO:api_server:📊 [LEVEL 1 - MONITORING] REPLAY_ATTACK from [attacker_id]... | Threat score: 15.0 | Action: Increased monitoring, peer marked as SUSPICIOUS
```

**Expected Peer 1 Logs:**
```
WARNING:peer_app: SECURITY ALERT RECEIVED: REPLAY_ATTACK - LOW - [AUTO-DETECTED] Duplicate nonce detected...
```

**Expected Behavior:**
- ✅ **Security Alerts tab** shows alert with LOW severity
- ✅ **Chat still works** - no session termination
- ✅ **Attacker can still send messages**
- ✅ **No progressive action taken** (just monitoring)

**Verification in Dashboards:**
- Peer 1 Security Alerts: Shows "1 alert" (or more if multiple attacks)
- Peer 2 Security Alerts: Shows same alerts (both victims notified)
- Controller Dashboard: Shows attack in "Recent Attack Attempts"

---

### LEVEL 2 (MEDIUM) - Session Termination

**Trigger:** Launch 1 more replay attack (total 3)

**From Peer 3 Dashboard:**
1. Launch another "Replay Attack" with "LOW" intensity
2. Wait for detection

**Expected Controller Logs:**
```
INFO:api_server:🔐 Peer [attacker_id]... security state: suspicious → threat_detected
WARNING:api_server:🚨 REPLAY ATTACK detected from [attacker_id]... | Total replays: 3 | Severity: MEDIUM | Threat score: 45.0
DEBUG:api_server:  → Sending alert to port 8080
INFO:api_server:  ✅ Alert sent to peer on port 8080
DEBUG:api_server:  → Sending alert to port 8081
INFO:api_server:  ✅ Alert sent to peer on port 8081
WARNING:api_server:⚠️  [LEVEL 2 - SESSION TERMINATION] REPLAY_ATTACK from [attacker_id]... | Terminated 1 session(s)
INFO:api_server:  ✅ Notified victim on port 8080
INFO:api_server:  ✅ Notified victim on port 8081
```

**Expected Peer 1 Logs:**
```
WARNING:peer_app: SECURITY ALERT RECEIVED: REPLAY_ATTACK - MEDIUM - [AUTO-DETECTED] Duplicate nonce detected...
INFO:peer_app: Processing progressive action notification: SESSION_TERMINATED for attacker [attacker_id]...
WARNING:peer_app: 🔒 SESSION TERMINATED by controller (attacker: [attacker_id]...)
INFO:peer_app: Removed pending connection request from blocked attacker [attacker_id]...
INFO:peer_app: Blocked future connections from [attacker_id]...
```

**Expected Behavior:**
- ✅ **Session with attacker TERMINATES**
- ✅ **Secure Chat tab shows "No active session"**
- ✅ **Cannot send messages anymore**
- ✅ **Attacker BLOCKED from reconnecting**
- ✅ **If attacker tries to connect again, request is REJECTED** (won't appear in UI)

**Verification:**
1. **Check Peer 1 Secure Chat:** Should show "Start a new session to chat"
2. **Try to reconnect from Peer 3:** Should fail (check Peer 1 logs for "🚫 BLOCKED")
3. **Security Alerts:** Shows MEDIUM severity alert

---

### LEVEL 3 (HIGH) - Key Destruction

**Trigger:** Launch 2 more replay attacks (total 5)

**From Peer 3 Dashboard:**
1. Launch 2 more "Replay Attack" with "MEDIUM" intensity
2. Wait for detection

**Expected Controller Logs:**
```
INFO:api_server:🔐 Peer [attacker_id]... security state: threat_detected → compromised
WARNING:api_server:🚨 REPLAY ATTACK detected from [attacker_id]... | Total replays: 5 | Severity: HIGH | Threat score: 75.0
INFO:api_server:  ↳ Destroyed encryption keys for peer: [attacker_id]...
ERROR:api_server:🔥 [LEVEL 3 - KEY DESTRUCTION] REPLAY_ATTACK from [attacker_id]... | Keys destroyed, 0 session(s) terminated
INFO:api_server:  ✅ Notified victim on port 8080
INFO:api_server:  ✅ Notified victim on port 8081
```

**Expected Peer 1 Logs:**
```
WARNING:peer_app: SECURITY ALERT RECEIVED: REPLAY_ATTACK - HIGH - [AUTO-DETECTED] Duplicate nonce detected...
INFO:peer_app: Processing progressive action notification: KEYS_DESTROYED for attacker [attacker_id]...
INFO:peer_app: KEYS_DESTROYED notification received but not connected to attacker
INFO:peer_app: Removed pending connection request from blocked attacker [attacker_id]...
INFO:peer_app: Blocked future connections from [attacker_id]...
```

**Expected Behavior:**
- ✅ **Attacker's encryption keys DESTROYED** (controller-side)
- ✅ **Session already terminated** (from Level 2)
- ✅ **Attacker remains BLOCKED**
- ✅ **Security state escalated to COMPROMISED**

**Verification:**
1. **Security Alerts:** Shows HIGH severity alert
2. **Attacker cannot reconnect** (still blocked)
3. **Controller shows "Keys destroyed"**

---

### LEVEL 4 (CRITICAL) - Peer Isolation

**Trigger:** Launch 2-3 more replay attacks (total 7+)

**From Peer 3 Dashboard:**
1. Launch 2-3 more "Replay Attack" with "CRITICAL" intensity
2. Wait for detection

**Expected Controller Logs:**
```
INFO:api_server:🔐 Peer [attacker_id]... security state: compromised → compromised
WARNING:api_server:🚨 REPLAY ATTACK detected from [attacker_id]... | Total replays: 7 | Severity: CRITICAL | Threat score: 100.0
INFO:api_server:  ↳ Destroyed encryption keys for peer: [attacker_id]...
INFO:api_server:  ↳ Isolated peer from network: [attacker_id]...
CRITICAL:api_server:🚫 [LEVEL 4 - PEER ISOLATION] REPLAY_ATTACK from [attacker_id]... | PEER ISOLATED FROM NETWORK
INFO:api_server:  ✅ Notified victim on port 8080
INFO:api_server:  ✅ Notified victim on port 8081
```

**Expected Peer 1 Logs:**
```
WARNING:peer_app: SECURITY ALERT RECEIVED: REPLAY_ATTACK - CRITICAL - [AUTO-DETECTED] Duplicate nonce detected...
INFO:peer_app: Processing progressive action notification: PEER_ISOLATED for attacker [attacker_id]...
INFO:peer_app: PEER_ISOLATED notification received but not connected to attacker
INFO:peer_app: Removed attacker from discovered peers list
INFO:peer_app: Removed pending connection request from isolated attacker [attacker_id]...
CRITICAL:peer_app: 🚫 ATTACKER ISOLATED AND BLOCKED (attacker: [attacker_id]...)
```

**Expected Behavior:**
- ✅ **Attacker COMPLETELY ISOLATED from network**
- ✅ **Attacker removed from discovered peers list**
- ✅ **All connection attempts BLOCKED**
- ✅ **Network is now secure**

**Verification:**
1. **Peer Discovery tab:** Attacker NO LONGER appears in peer list
2. **Security Alerts:** Shows CRITICAL severity alert
3. **Connection Requests:** Attacker CANNOT send new requests
4. **Controller:** Shows "PEER ISOLATED FROM NETWORK"

---

## SCENARIO 2: Victim Connected to Another Victim (NOT Attacker)

**Setup:** Two victims chatting with each other, attacker sends attacks without established session.

### Setup Phase:

1. **Connect Peer 1 to Peer 2** (NOT Peer 3)
   - Peer 1: Discover and connect to Peer 2
   - Peer 2: Accept connection from Peer 1
   - Verify chat works between Peer 1 and Peer 2

2. **Do NOT accept any connection from Peer 3** (attacker)
   - If Peer 3 sends requests, just leave them pending
   - Do NOT click Accept

3. **Verify State:**
   - Peer 1 ↔ Peer 2: Active session, can chat ✓
   - Peer 3 (attacker): NO session with victims ✓

---

### LEVEL 1 (LOW) - Monitoring Only

**Trigger:** Launch 1-2 replay attacks from Peer 3

**From Peer 3 Dashboard:**
1. Attack Panel → Replay Attack → LOW intensity
2. Launch 1-2 attacks

**Expected Controller Logs:**
```
WARNING:api_server:🚨 REPLAY ATTACK detected from [attacker_id]... | Total replays: 1 | Severity: LOW | Threat score: 15.0
INFO:api_server:  ✅ Alert sent to peer on port 8080
INFO:api_server:  ✅ Alert sent to peer on port 8081
INFO:api_server:📊 [LEVEL 1 - MONITORING] REPLAY_ATTACK from [attacker_id]...
```

**Expected Peer 1 Logs:**
```
WARNING:peer_app: SECURITY ALERT RECEIVED: REPLAY_ATTACK - LOW - [AUTO-DETECTED] Duplicate nonce detected...
```

**Expected Behavior:**
- ✅ **Peer 1 ↔ Peer 2 chat CONTINUES normally** (not affected)
- ✅ **Security alerts appear in both Peer 1 and Peer 2**
- ✅ **Attacker detected but no action yet**
- ✅ **No session to terminate** (victims not connected to attacker)

**Verification:**
- Peer 1 ↔ Peer 2: Can still chat normally ✓
- Security Alerts: Show LOW severity in both victims ✓
- Attacker connection requests: Still pending (not accepted) ✓

---

### LEVEL 2 (MEDIUM) - Session Termination

**Trigger:** Launch 1 more replay attack (total 3)

**Expected Controller Logs:**
```
WARNING:api_server:🚨 REPLAY ATTACK detected from [attacker_id]... | Total replays: 3 | Severity: MEDIUM | Threat score: 45.0
WARNING:api_server:⚠️  [LEVEL 2 - SESSION TERMINATION] REPLAY_ATTACK from [attacker_id]... | Terminated 0 session(s)
                                                                                            ↑ No session with attacker!
INFO:api_server:  ✅ Notified victim on port 8080
INFO:api_server:  ✅ Notified victim on port 8081
```

**Expected Peer 1 Logs:**
```
WARNING:peer_app: SECURITY ALERT RECEIVED: REPLAY_ATTACK - MEDIUM - [AUTO-DETECTED] Duplicate nonce detected...
INFO:peer_app: Processing progressive action notification: SESSION_TERMINATED for attacker [attacker_id]...
INFO:peer_app: SESSION_TERMINATED notification received but not connected to attacker (connected to [peer2_id]...)
                                                                                        ↑ Connected to Peer 2, not attacker!
INFO:peer_app: Removed pending connection request from blocked attacker [attacker_id]...
INFO:peer_app: Blocked future connections from [attacker_id]...
```

**Expected Behavior:**
- ✅ **Peer 1 ↔ Peer 2 session CONTINUES** (not terminated)
- ✅ **Victims are chatting with EACH OTHER, not attacker**
- ✅ **Attacker BLOCKED from connecting**
- ✅ **Any pending requests from attacker REMOVED**
- ✅ **Security alerts show MEDIUM severity**

**Key Point:** Session termination only affects sessions WITH THE ATTACKER. Since victims are connected to each other, their legitimate session continues!

**Verification:**
1. **Chat between Peer 1 ↔ Peer 2:** Still works ✓
2. **Try to connect Peer 3 to Peer 1:** BLOCKED (won't appear in UI) ✓
3. **Existing pending requests from Peer 3:** REMOVED from Connection Requests ✓
4. **Peer 1 logs:** Shows "not connected to attacker (connected to [peer2_id]...)" ✓

---

### LEVEL 3 (HIGH) - Key Destruction

**Trigger:** Launch 2 more replay attacks (total 5)

**Expected Controller Logs:**
```
WARNING:api_server:🚨 REPLAY ATTACK detected from [attacker_id]... | Total replays: 5 | Severity: HIGH | Threat score: 75.0
INFO:api_server:  ↳ Destroyed encryption keys for peer: [attacker_id]...
ERROR:api_server:🔥 [LEVEL 3 - KEY DESTRUCTION] REPLAY_ATTACK from [attacker_id]... | Keys destroyed, 0 session(s) terminated
                                                                                       ↑ No sessions to terminate
INFO:api_server:  ✅ Notified victim on port 8080
INFO:api_server:  ✅ Notified victim on port 8081
```

**Expected Peer 1 Logs:**
```
WARNING:peer_app: SECURITY ALERT RECEIVED: REPLAY_ATTACK - HIGH - [AUTO-DETECTED] Duplicate nonce detected...
INFO:peer_app: Processing progressive action notification: KEYS_DESTROYED for attacker [attacker_id]...
INFO:peer_app: KEYS_DESTROYED notification received but not connected to attacker (connected to [peer2_id]...)
INFO:peer_app: Removed pending connection request from blocked attacker [attacker_id]...
INFO:peer_app: Blocked future connections from [attacker_id]...
```

**Expected Behavior:**
- ✅ **Peer 1 ↔ Peer 2 session CONTINUES** (their keys NOT destroyed)
- ✅ **Attacker's keys destroyed** (controller-side)
- ✅ **Attacker remains BLOCKED**
- ✅ **Legitimate chat UNAFFECTED**

**Verification:**
1. **Chat between Peer 1 ↔ Peer 2:** Still works perfectly ✓
2. **Security Alerts:** Shows HIGH severity ✓
3. **Attacker:** Cannot reconnect (blocked) ✓

---

### LEVEL 4 (CRITICAL) - Peer Isolation

**Trigger:** Launch 2-3 more replay attacks (total 7+)

**Expected Controller Logs:**
```
WARNING:api_server:🚨 REPLAY ATTACK detected from [attacker_id]... | Total replays: 7 | Severity: CRITICAL | Threat score: 100.0
INFO:api_server:  ↳ Isolated peer from network: [attacker_id]...
CRITICAL:api_server:🚫 [LEVEL 4 - PEER ISOLATION] REPLAY_ATTACK from [attacker_id]... | PEER ISOLATED FROM NETWORK
INFO:api_server:  ✅ Notified victim on port 8080
INFO:api_server:  ✅ Notified victim on port 8081
```

**Expected Peer 1 Logs:**
```
WARNING:peer_app: SECURITY ALERT RECEIVED: REPLAY_ATTACK - CRITICAL - [AUTO-DETECTED] Duplicate nonce detected...
INFO:peer_app: Processing progressive action notification: PEER_ISOLATED for attacker [attacker_id]...
INFO:peer_app: PEER_ISOLATED notification received but not connected to attacker (connected to [peer2_id]...)
INFO:peer_app: Removed attacker from discovered peers list
INFO:peer_app: Removed pending connection request from isolated attacker [attacker_id]...
CRITICAL:peer_app: 🚫 ATTACKER ISOLATED AND BLOCKED (attacker: [attacker_id]...)
```

**Expected Behavior:**
- ✅ **Peer 1 ↔ Peer 2 session CONTINUES** (legitimate communication preserved)
- ✅ **Attacker COMPLETELY ISOLATED**
- ✅ **Attacker removed from Peer Discovery**
- ✅ **Network is SECURE**
- ✅ **Victims can continue chatting safely**

**Verification:**
1. **Chat between Peer 1 ↔ Peer 2:** Still works ✓
2. **Peer Discovery:** Attacker NO LONGER in peer list ✓
3. **Connection Requests:** Attacker CANNOT send requests ✓
4. **Security Alerts:** Shows CRITICAL severity ✓
5. **Both victims notified:** Peer 1 and Peer 2 see alerts ✓

---

## Summary Comparison

### Scenario 1: Victim Connected to Attacker

| Level | Session Status | Chat Works | Attacker Blocked | Reconnect |
|-------|---------------|------------|------------------|-----------|
| LOW | Active | ✓ Yes | ✗ No | ✓ Can reconnect |
| MEDIUM | **TERMINATED** | ✗ No | ✓ Yes | ✗ BLOCKED |
| HIGH | Terminated | ✗ No | ✓ Yes | ✗ BLOCKED |
| CRITICAL | Terminated | ✗ No | ✓ Yes + Isolated | ✗ BLOCKED |

### Scenario 2: Victim Connected to Another Victim

| Level | Victim-Victim Chat | Attacker Status | Attacker Can Connect | Key Difference |
|-------|-------------------|-----------------|----------------------|----------------|
| LOW | ✓ Continues | Detected | ✓ Yes | Just monitoring |
| MEDIUM | ✓ **Continues** | Blocked | ✗ **BLOCKED** | Legitimate session preserved |
| HIGH | ✓ **Continues** | Blocked + Keys destroyed | ✗ **BLOCKED** | Only attacker affected |
| CRITICAL | ✓ **Continues** | Isolated from network | ✗ **BLOCKED** | Attacker removed from network |

---

## Quick Test Commands

### Check Alert Count:
```bash
# Peer 1
curl http://localhost:8080/api/peer/alerts

# Peer 2
curl http://localhost:8081/api/peer/alerts

# Controller stats
curl http://localhost:5000/api/status/comprehensive
```

### Check Active Sessions:
```bash
# Peer 1 status
curl http://localhost:8080/api/peer/status

# Peer 2 status
curl http://localhost:8081/api/peer/status
```

### Clear Alerts (between tests):
```bash
curl -X DELETE http://localhost:8080/api/peer/alerts
curl -X DELETE http://localhost:8081/api/peer/alerts
```

---

## Expected Attack Thresholds

### Replay Attack:
- LOW: 2-3 attacks (Threat: 15-30)
- MEDIUM: 3-4 attacks (Threat: 45-60)
- HIGH: 5-6 attacks (Threat: 75-90)
- CRITICAL: 7+ attacks (Threat: 100+)

### Network Flooding:
- LOW: 15-30 packets/10sec
- MEDIUM: 30-50 packets/10sec
- HIGH: 50-100 packets/10sec
- CRITICAL: 100+ packets/10sec

### Auth Flooding:
- LOW: 5-10 attempts/60sec
- MEDIUM: 10-15 attempts/60sec
- HIGH: 15-20 attempts/60sec
- CRITICAL: 20+ attempts/60sec

---

## Troubleshooting

### If alerts don't appear:
1. Check controller is running with: `export VICTIM_PEER_HOST=192.168.2.125`
2. Verify peer backends are running on Windows
3. Check controller logs for "✅ Alert sent to peer on port"

### If blocking doesn't work:
1. Make sure you restarted peer backends after the fix
2. Check peer logs for "🚫 BLOCKED connection request"
3. Verify `blocked_peers` set is being populated

### If sessions don't terminate:
1. This is CORRECT if victim is connected to another victim, not attacker
2. Sessions only terminate if connected to the attacker
3. Check peer logs to see which peer it's connected to

---

**Test both scenarios to fully understand how progressive defense protects legitimate communications while blocking attackers!**
