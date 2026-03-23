# Progressive Self-Destruct System - Complete Testing Guide

## 🎯 System Overview

This SDN project implements a **real-world Progressive Self-Destruct mechanism** where attacks are detected based on actual network behavior, not reported data.

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   ATTACK EXECUTION FLOW                     │
└─────────────────────────────────────────────────────────────┘

User clicks "Launch Attack" in Peer 3 Dashboard
              ↓
Peer 3 Backend executes REAL attack behavior
  • Replay: Sends duplicate nonces
  • Flooding: Sends packet bursts
  • Auth Flooding: Rapid auth attempts
              ↓
Victim Peers (1 & 2) receive malicious packets
              ↓
Victims report to Controller via /api/network/monitor
  • event_type: AUTH_ATTEMPT (with nonce)
  • event_type: PACKET_FLOOD (with packet count)
              ↓
Controller AUTOMATICALLY DETECTS attack patterns
  • Global nonce duplicate detection
  • Packet rate analysis
  • Auth attempt frequency
              ↓
Controller calculates severity based on thresholds
  • LOW: 2 replays / 15 packets
  • MEDIUM: 3-4 replays / 30-50 packets
  • HIGH: 5-6 replays / 50-100 packets
  • CRITICAL: 7+ replays / 100+ packets
              ↓
Controller triggers PROGRESSIVE RESPONSE
  • Level 1: Monitoring & Warning
  • Level 2: Session Termination
  • Level 3: Key Destruction
  • Level 4: Peer Isolation
              ↓
Controller sends notifications to victim peers
  • POST to http://localhost:8080/api/security/notify
  • POST to http://localhost:8081/api/security/notify
              ↓
Victim Dashboards display alerts in Security Alerts tab
```

---

## 🚀 Starting the System

### 1. Start SDN Controller (Ubuntu)

```bash
cd /path/to/SDN/sdn-controller
python3 api_server.py
```

**Expected Output:**
```
🚀 SDN Progressive Self-Destruct Controller STARTED
Monitoring: ACTIVE | Auto-escalation: ENABLED
 * Running on http://0.0.0.0:5000
```

### 2. Start Controller Dashboard (Windows)

```cmd
cd c:\Users\charan27\OneDrive\Desktop\SDN
start-controller-dashboard.bat
```

**Opens:** http://localhost:3001

### 3. Start Peer Dashboards & Backends

```cmd
:: Peer 1 (Victim)
start-peer1-dashboard.bat
→ Dashboard: http://localhost:3000
→ Backend: Port 8080

:: Peer 2 (Victim)
start-peer2-dashboard.bat
→ Dashboard: http://localhost:3002
→ Backend: Port 8081

:: Peer 3 (Attacker)
start-peer3-dashboard.bat
→ Dashboard: http://localhost:3003
→ Backend: Port 8082
```

---

## 🧪 Test Scenario 1: Replay Attack (Progressive Escalation)

### Objective
Demonstrate all 4 levels of progressive response

### Steps

1. **Start All Peers**
   - Click "Start Discovery" in Peer 1, 2, and 3
   - Wait for peers to discover each other (~5 seconds)

2. **Create a Session (Optional but Recommended)**
   - In Peer 1: Click "Connect" to Peer 2
   - In Peer 2: Accept the connection request
   - Send a few messages to establish active session

3. **Launch LOW Intensity Replay Attack**
   - In Peer 3 Dashboard → "Launch Attack" tab
   - Select: Replay Attack
   - Intensity: LOW
   - Click "Launch Attack"

4. **Verify Level 1 Response (LOW)**

   **Controller Dashboard:**
   - Check "System Logs" tab
   - Should see: `📊 [LEVEL 1 - MONITORING] REPLAY_ATTACK`
   - Threat score calculated
   - Peer marked as SUSPICIOUS

   **Victim Dashboards (Peer 1 & 2):**
   - Check "Security Alerts" tab
   - Should see alert with LOW severity
   - Sessions should remain ACTIVE

5. **Launch MEDIUM Intensity Replay Attack**
   - Peer 3: Select MEDIUM intensity
   - Click "Launch Attack"

6. **Verify Level 2 Response (MEDIUM)**

   **Controller Dashboard:**
   - System Logs: `⚠️ [LEVEL 2 - SESSION TERMINATION]`
   - Active Sessions count decreases

   **Victim Dashboards:**
   - New alert appears: "Your session was terminated for security"
   - Chat connection shows as disconnected
   - Can reconnect after 30-60 seconds

7. **Launch HIGH Intensity Replay Attack**
   - Peer 3: Select HIGH intensity
   - Launch attack

8. **Verify Level 3 Response (HIGH)**

   **Controller Dashboard:**
   - System Logs: `🔥 [LEVEL 3 - KEY DESTRUCTION]`
   - Shows "Keys destroyed" in logs

   **Victim Dashboards:**
   - Alert: "Encryption keys destroyed due to severe attack"
   - Re-authentication required message

9. **Launch CRITICAL Intensity Replay Attack**
   - Peer 3: Select CRITICAL intensity
   - Launch attack

10. **Verify Level 4 Response (CRITICAL)**

    **Controller Dashboard:**
    - System Logs: `🚫 [LEVEL 4 - PEER ISOLATION]`
    - Isolated Peers count increases to 1
    - Peer 3 status shows "isolated"

    **Victim Dashboards:**
    - Alert: "CRITICAL: Malicious peer completely isolated"
    - Network secured message
    - Threat neutralized notification

---

## 🧪 Test Scenario 2: Network Flooding Attack

### Objective
Test packet-based attack detection

### Prerequisites
- Active session between Peer 1 and Peer 2

### Steps

1. **Establish Session**
   - Peer 1 connects to Peer 2
   - Send some messages

2. **Launch LOW Flooding Attack**
   - Peer 3: Select "Network Flooding"
   - Intensity: LOW (15 packets)
   - Launch

3. **Verify Detection**

   **Controller Dashboard:**
   - System Logs: `🚨 FLOODING ATTACK detected`
   - Shows packet count: "15 packets/10sec"
   - Progressive response triggered

4. **Escalate to MEDIUM**
   - Launch MEDIUM intensity (40 packets)
   - Session should be terminated

5. **Escalate to HIGH**
   - Launch HIGH intensity (80 packets)
   - Keys should be destroyed

6. **Escalate to CRITICAL**
   - Launch CRITICAL intensity (150 packets)
   - Peer should be isolated

---

## 🧪 Test Scenario 3: Authentication Flooding

### Objective
Test rapid authentication attempt detection

### Steps

1. **Launch LOW Auth Flooding**
   - Peer 3: Select "Auth Flooding"
   - Intensity: LOW (8 attempts/min)
   - Launch

2. **Verify Detection**

   **Controller Dashboard:**
   - System Logs: `🚨 AUTH FLOODING detected`
   - Shows: "8 attempts/60s"
   - Level 1 response triggered

3. **Escalate Progressively**
   - MEDIUM: 15 attempts → Session Termination
   - HIGH: 25 attempts → Key Destruction
   - CRITICAL: 35 attempts → Peer Isolation

---

## ✅ Verification Checklist

### Controller Dashboard (http://localhost:3001)

- [ ] **Network Overview Tab**
  - Shows active peers count
  - Shows active sessions count
  - Shows threat count
  - Shows isolated peers count

- [ ] **Traffic Monitor Tab**
  - Displays packet statistics
  - Shows bytes transferred
  - Updates in real-time

- [ ] **Attack Detection Tab**
  - Lists detected attacks
  - Shows attack types and severity
  - Displays response actions taken

- [ ] **System Logs Tab**
  - Progressive response levels visible
  - Threat scores calculated
  - State transitions logged
  - Timestamps accurate

### Victim Peer Dashboards (Ports 3000, 3002)

- [ ] **Security Alerts Tab**
  - Receives alerts when Peer 3 attacks
  - Shows alert severity (LOW/MEDIUM/HIGH/CRITICAL)
  - Displays attacker ID (truncated)
  - Shows recommended actions
  - Includes threat score

- [ ] **Secure Chat Tab**
  - Session disconnects on MEDIUM+ severity
  - Shows "Session terminated" message
  - Can reconnect after cooldown

- [ ] **Peer Discovery Tab**
  - Shows Peer 3 status as "isolated" (after CRITICAL attack)
  - Can't connect to isolated peer

### Attacker Peer Dashboard (Port 3003)

- [ ] **Launch Attack Tab**
  - All 3 attack types available:
    - 🔄 Replay Attack
    - 🌊 Network Flooding
    - 🔐 Auth Flooding
  - All 4 intensity levels work
  - Attack status shows success/failure
  - Progressive response levels explained

---

## 🔍 Real-Time Monitoring Commands

### Watch Controller Logs (Ubuntu)

```bash
tail -f /path/to/SDN/sdn-controller/api_server.log
```

### Check Comprehensive Status

```bash
curl http://localhost:5000/api/status/comprehensive | jq
```

**Expected Output:**
```json
{
  "status": "success",
  "system": {
    "controller_active": true,
    "health_score": 85.0,
    "uptime": 1234.5
  },
  "threat_landscape": {
    "total_monitored_peers": 3,
    "isolated_peers": 1,
    "suspicious_peers": 1
  },
  "attack_statistics": {
    "total_replay_attacks": 10,
    "total_flood_attacks": 4,
    "total_auth_failures": 8
  },
  "progressive_defense_levels": {
    "level_1_monitoring": 0,
    "level_2_session_termination": 0,
    "level_3_key_destruction": 0,
    "level_4_peer_isolation": 1
  }
}
```

### Check Peer Metrics

```bash
# Get metrics for specific peer
curl http://localhost:5000/api/metrics/peer/<peer_id> | jq

# Get all peer metrics
curl http://localhost:5000/api/metrics/all | jq
```

### Check Security Configuration

```bash
curl http://localhost:5000/api/security/config | jq
```

---

## 🎛️ Dynamic Configuration Adjustment

### Adjust Detection Thresholds

```bash
curl -X PUT http://localhost:5000/api/security/config \
  -H "Content-Type: application/json" \
  -d '{
    "replay_thresholds": {
      "low": 1,
      "medium": 2,
      "high": 3,
      "critical": 4
    }
  }'
```

### Enable/Disable Features

```bash
curl -X PUT http://localhost:5000/api/security/config \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "auto_escalation": true,
      "victim_notification": true,
      "auto_recovery": false
    }
  }'
```

---

## 🔧 Troubleshooting

### Problem: Alerts not showing in victim dashboards

**Solution:**
1. Check controller is running: `curl http://localhost:5000/api/status`
2. Verify peer backends are running on correct ports (8080, 8081, 8082)
3. Check browser console for errors (F12)
4. Verify CORS is enabled in api_server.py

### Problem: Attacks not detected

**Solution:**
1. Ensure all peers started discovery
2. Check controller logs for monitoring events
3. Verify peer backends are reporting to `/api/network/monitor`
4. Test with higher intensity attacks

### Problem: Sessions not terminating

**Solution:**
1. Create an active session first (Peer 1 ↔ Peer 2)
2. Launch MEDIUM+ intensity attacks
3. Check controller logs for session termination messages
4. Verify sessions exist: `curl http://localhost:5000/api/flows`

### Problem: Peer not isolated after CRITICAL attack

**Solution:**
1. Check controller logs for isolation messages
2. Verify peer status: `curl http://localhost:5000/api/peers | jq`
3. Look for `"status": "isolated"` in peer data

---

## 📊 Expected Metrics After Full Test

After running all test scenarios, your system should show:

**Controller Dashboard:**
- Total Attacks Detected: 20-30
- Isolated Peers: 1 (Peer 3)
- Sessions Terminated: 5-10
- Keys Destroyed: 1 (Peer 3)
- Health Score: 70-85

**Victim Peer Dashboards:**
- Security Alerts: 15-20 alerts
- Recent Alerts (5 min): 5-10
- Alert Severities: Mix of LOW, MEDIUM, HIGH, CRITICAL

**Attacker Peer Dashboard:**
- Successful Attacks Launched: 15-20
- All 4 severity levels triggered

---

## 🎓 Understanding the Detection Mechanisms

### 1. Replay Attack Detection
**How it works:**
- Controller maintains global nonce history across ALL peers
- When victim receives auth request, reports nonce to controller
- Controller checks if nonce already exists (duplicate = replay)
- Severity increases with each replay attempt

**Key Code:** `api_server.py` lines 375-427

### 2. Flooding Attack Detection
**How it works:**
- Victims count packets received within 10-second windows
- Report packet counts to controller
- Controller analyzes packet rate
- Exceeding thresholds triggers progressive response

**Key Code:** `api_server.py` lines 462-503

### 3. Auth Flooding Detection
**How it works:**
- Controller tracks auth attempts per peer per minute
- Counts attempts in 60-second sliding window
- Rapid attempts trigger escalation
- Even with valid nonces (not replays)

**Key Code:** `api_server.py` lines 433-457

---

## 🏆 Success Criteria

Your implementation is working correctly if:

✅ **Attack Execution is Real**
- Peer 3 sends actual duplicate nonces (not just reports "replay")
- Flooding sends real packets to victim peers
- Auth flooding sends rapid auth attempts

✅ **Detection is Automatic**
- Controller detects patterns WITHOUT peer reporting attack type
- Uses actual network behavior (nonce duplicates, packet rates)
- Calculates severity based on configured thresholds

✅ **Progressive Response Works**
- Each severity level triggers correct action
- Sessions terminate at MEDIUM
- Keys destroyed at HIGH
- Peer isolated at CRITICAL

✅ **Victim Notification Works**
- Victim dashboards receive real-time alerts
- Alerts show correct severity and threat score
- Recommended actions displayed

✅ **State Machine Functions**
- Peer states transition: NORMAL → SUSPICIOUS → THREAT_DETECTED → COMPROMISED → ISOLATED
- Threat scores calculate correctly with time decay
- Metrics track all attack attempts

---

## 📝 Demo Script

For a polished demonstration:

1. **Introduction (2 min)**
   - Show all 4 dashboards side-by-side
   - Explain the architecture
   - Start all peers

2. **Baseline (1 min)**
   - Show normal P2P communication
   - Peer 1 ↔ Peer 2 chat exchange
   - Controller shows "Normal" status

3. **Progressive Escalation (5 min)**
   - Launch LOW → Show monitoring only
   - Launch MEDIUM → Session terminated
   - Launch HIGH → Keys destroyed
   - Launch CRITICAL → Peer isolated

4. **Demonstrate Detection (2 min)**
   - Show controller logs detecting duplicate nonces
   - Show automatic severity calculation
   - Show threat score increasing

5. **Show Victim Experience (2 min)**
   - Victim alerts appearing in real-time
   - Progressive severity levels
   - Recommended actions

6. **Recovery (1 min)**
   - Show peer recovery endpoint
   - Restore isolated peer (optional)

---

## 🔐 Security Configuration Reference

| Threshold | LOW | MEDIUM | HIGH | CRITICAL |
|-----------|-----|--------|------|----------|
| **Replay Attacks** | 2 | 3-4 | 5-6 | 7+ |
| **Flooding (packets/10s)** | 15-29 | 30-49 | 50-99 | 100+ |
| **Auth Flooding (attempts/min)** | 5-9 | 10-14 | 15-19 | 20+ |

**Progressive Actions:**
- **Level 1 (LOW):** Monitoring, logging, peer marked suspicious
- **Level 2 (MEDIUM):** Session termination, victims notified
- **Level 3 (HIGH):** Key destruction, re-auth required
- **Level 4 (CRITICAL):** Complete network isolation, threat neutralized

---

## 🎯 Project Completion Checklist

- [x] Progressive Self-Destruct mechanism implemented
- [x] Real attack execution (not simulated reporting)
- [x] Automatic pattern detection by controller
- [x] All 4 severity levels functional
- [x] Victim notification system operational
- [x] 3 attack types: Replay, Flooding, Auth Flooding
- [x] Professional logging with structured output
- [x] Configurable thresholds
- [x] Comprehensive API endpoints
- [x] Recovery mechanism
- [x] Threat scoring with time decay
- [x] State machine implementation
- [x] Real-time dashboards
- [x] Complete testing guide

---

## 📚 Additional Resources

**API Documentation:**
- [api_server.py](sdn-controller/api_server.py) - Main controller with all endpoints
- Comprehensive status: `GET /api/status/comprehensive`
- Peer metrics: `GET /api/metrics/all`
- Security config: `GET /api/security/config`

**Attack Scripts:**
- [attack_simulator.py](attack-scripts/attack_simulator.py) - CLI attack tool
- [progressive-demo.py](attack-scripts/progressive-demo.py) - Demo script

**Documentation:**
- [README.md](README.md) - Project overview
- [PROJECT-SUMMARY.md](PROJECT-SUMMARY.md) - Architecture details
- [INSTALLATION-GUIDE.md](docs/installation-guide.md) - Setup instructions

---

**System Status: PRODUCTION READY ✅**

Your Progressive Self-Destruct SDN project is now complete and functional with real-world attack detection and automated progressive response mechanisms!
