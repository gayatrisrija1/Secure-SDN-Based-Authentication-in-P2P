# 🔍 Localhost Development Environment - Complete Verification

## Your Setup (All on Same Machine - localhost)

```
┌─────────────────────────────────────────────────────────┐
│          ALL RUNNING ON 127.0.0.1 (localhost)          │
└─────────────────────────────────────────────────────────┘

Controller:
  - Backend (Ubuntu): http://localhost:5000 (api_server.py)
  - Dashboard (Browser Tab 1): http://localhost:3001

Peer 1 (Victim):
  - Backend: http://localhost:8080
  - Dashboard (Browser Tab 2): http://localhost:3000

Peer 2 (Victim):
  - Backend: http://localhost:8081
  - Dashboard (Browser Tab 3): http://localhost:3002

Peer 3 (Attacker):
  - Backend: http://localhost:8082
  - Dashboard (Browser Tab 4): http://localhost:3003
```

---

## ✅ Pre-Flight Checklist

### 1. Verify All Services Are Running

```bash
# Check if all ports are listening
netstat -an | findstr "5000 8080 8081 8082 3000 3001 3002 3003"

# OR use PowerShell
Test-NetConnection -ComputerName localhost -Port 5000
Test-NetConnection -ComputerName localhost -Port 8080
Test-NetConnection -ComputerName localhost -Port 8081
Test-NetConnection -ComputerName localhost -Port 8082
```

**Expected:** All ports should be LISTENING

### 2. Verify Controller is Accessible

```bash
curl http://localhost:5000/api/status
```

**Expected Response:**
```json
{
  "active": false,
  "timestamp": 1234567890,
  "active_peers": 0,
  "active_flows": 0,
  "recent_alerts": 0
}
```

### 3. Verify Peer Backends are Running

```bash
curl http://localhost:8080/api/peer/status
curl http://localhost:8081/api/peer/status
curl http://localhost:8082/api/peer/status
```

**Expected:** All return peer status successfully

---

## 🧪 Complete 4-Level Verification Test

### **Test Setup**

1. **Open 4 Browser Tabs:**
   - Tab 1: http://localhost:3001 (Controller Dashboard)
   - Tab 2: http://localhost:3000 (Peer 1 - Victim)
   - Tab 3: http://localhost:3002 (Peer 2 - Victim)
   - Tab 4: http://localhost:3003 (Peer 3 - Attacker)

2. **Arrange Tabs Side-by-Side** (Use Windows Snap):
   ```
   ┌─────────────┬─────────────┐
   │ Controller  │   Peer 1    │
   │   :3001     │   :3000     │
   ├─────────────┼─────────────┤
   │   Peer 2    │   Peer 3    │
   │   :3002     │   :3003     │
   └─────────────┴─────────────┘
   ```

3. **Start All Peers:**
   - In each Peer tab (3000, 3002, 3003): Click "Start Discovery"
   - Wait 5 seconds for peer discovery

4. **Optional - Create Session:**
   - Peer 1 (Tab 2): Click "Connect" to Peer 2
   - Peer 2 (Tab 3): Accept connection
   - Send a test message

---

## 📊 Level 1 - LOW (Monitoring & Warning)

### Execute Attack

**In Peer 3 Dashboard (Tab 4 - :3003):**
1. Go to "Launch Attack" tab
2. Select: **Replay Attack** 🔄
3. Select: **LOW** intensity
4. Click "Launch Attack"

### Verify in Controller (Tab 1 - :3001)

✅ **System Logs Tab:**
```
📊 [LEVEL 1 - MONITORING] REPLAY_ATTACK from abcd1234... |
Threat score: 15.0 |
Action: Increased monitoring, peer marked as SUSPICIOUS
```

✅ **Network Overview:**
- Active Peers: 3
- Active Sessions: 0-1 (unchanged)
- Threats: 1
- Isolated Peers: 0

### Verify in Victim Peers (Tabs 2 & 3 - :3000, :3002)

✅ **Security Alerts Tab (Both Peer 1 & 2):**
```
Alert appears:
- Type: REPLAY_ATTACK
- Severity: LOW
- Message: "[AUTO-DETECTED] Duplicate nonce detected..."
- Attacker ID: abcd1234...
- Threat Score: ~15.0
- Recommended Action: "Monitor network activity - stay alert"
```

✅ **Chat Tab:**
- Session STILL ACTIVE ✓
- Can still send messages ✓

### Verify in Attacker (Tab 4 - :3003)

✅ **Attack Status:**
- Shows "Attack launched successfully"
- "Check Controller Dashboard for progressive response"

---

## 🚨 Level 2 - MEDIUM (Session Termination)

### Execute Attack

**In Peer 3 Dashboard (Tab 4 - :3003):**
1. Select: **Replay Attack** 🔄
2. Select: **MEDIUM** intensity
3. Click "Launch Attack"

### Verify in Controller (Tab 1 - :3001)

✅ **System Logs Tab:**
```
⚠️ [LEVEL 2 - SESSION TERMINATION] REPLAY_ATTACK from abcd1234... |
Terminated X session(s) |
Threat score: 30.0 |
Victim peers notified
```

✅ **Network Overview:**
- Active Sessions: **DECREASED** (should drop to 0)
- Threats: 1
- Recent Alerts: Increased

### Verify in Victim Peers (Tabs 2 & 3 - :3000, :3002)

✅ **Security Alerts Tab (NEW ALERT):**
```
⚠️ [LEVEL 2] Your session was terminated for security reasons.
Attack Type: REPLAY_ATTACK
Attacker: abcd1234...
Sessions affected: 1
Threat Score: 30.0/100

Recommended Action: Wait 30-60 seconds, then reconnect to establish new secure session
```

✅ **Chat Tab:**
- Session shows as **DISCONNECTED** ❌
- Chat input may be disabled
- Message: "No active session" or similar

### Verify in Attacker (Tab 4 - :3003)

✅ **Attack Status:**
- Shows attack success
- May show session terminated

### Manual Verification

```bash
# Check sessions are actually terminated
curl http://localhost:5000/api/flows
# Should return empty array [] or no sessions with attacker
```

---

## 🔥 Level 3 - HIGH (Key Destruction)

### Execute Attack

**In Peer 3 Dashboard (Tab 4 - :3003):**
1. Select: **Replay Attack** 🔄
2. Select: **HIGH** intensity
3. Click "Launch Attack"

### Verify in Controller (Tab 1 - :3001)

✅ **System Logs Tab:**
```
🔥 [LEVEL 3 - KEY DESTRUCTION] REPLAY_ATTACK from abcd1234... |
Keys destroyed, X session(s) terminated |
Threat score: 60.0 |
Re-authentication required
```

✅ **Peer Status:**
- Attacker peer should show "keys_destroyed": true

### Verify in Victim Peers (Tabs 2 & 3 - :3000, :3002)

✅ **Security Alerts Tab (NEW ALERT):**
```
🔐 [LEVEL 3] Encryption keys destroyed due to severe attack.
Attack Type: REPLAY_ATTACK
Attacker: abcd1234...
Sessions terminated: 1
Threat Score: 60.0/100
All compromised keys have been destroyed.

Recommended Action: Re-authenticate with trusted peers to establish new encrypted sessions
```

### Verify in Attacker (Tab 4 - :3003)

✅ **May notice:**
- Cannot establish new connections
- Keys invalidated

### Manual Verification

```bash
# Check keys are destroyed
curl http://localhost:5000/api/peers | jq '.[] | select(.id | contains("attacker_id"))'
# Should show: "keys_destroyed": true, "security_level": "compromised"
```

---

## 🚫 Level 4 - CRITICAL (Peer Isolation)

### Execute Attack

**In Peer 3 Dashboard (Tab 4 - :3003):**
1. Select: **Replay Attack** 🔄
2. Select: **CRITICAL** intensity
3. Click "Launch Attack"

### Verify in Controller (Tab 1 - :3001)

✅ **System Logs Tab:**
```
🚫 [LEVEL 4 - PEER ISOLATION] REPLAY_ATTACK from abcd1234... |
PEER ISOLATED FROM NETWORK |
X session(s) terminated, keys destroyed |
Threat score: 90.0 |
Network secured
```

✅ **Network Overview:**
- Isolated Peers: **1** ✓
- Threats: 1
- Health Score: Decreased

### Verify in Victim Peers (Tabs 2 & 3 - :3000, :3002)

✅ **Security Alerts Tab (CRITICAL ALERT):**
```
🚫 [LEVEL 4] CRITICAL: Malicious peer completely isolated.
Attack Type: REPLAY_ATTACK
Attacker: abcd1234...
Sessions terminated: 0-1
Threat Score: 90.0/100
Peer has been blocked from all network communications.
⚠️ THREAT NEUTRALIZED ⚠️

Recommended Action: Network is now secure. Safe to discover and connect to other peers
```

### Verify in Attacker (Tab 4 - :3003)

✅ **Expected Behavior:**
- Peer 3 is now ISOLATED
- Cannot connect to other peers
- Peer discovery may show no peers or errors

### Manual Verification

```bash
# Verify isolation
curl http://localhost:5000/api/status/comprehensive | jq '.threat_landscape.isolated_peers'
# Should return: 1

curl http://localhost:5000/api/peers | jq '.[] | select(.status == "isolated")'
# Should show the isolated peer with:
# "status": "isolated"
# "security_level": "isolated"
# "isolated_at": <timestamp>
```

---

## 🔍 Complete Verification Checklist

### Controller Dashboard (Tab 1 - :3001)

- [ ] System logs show all 4 levels with emojis (📊, ⚠️, 🔥, 🚫)
- [ ] Network Overview stats update correctly
- [ ] Active Sessions count decreases at Level 2+
- [ ] Isolated Peers increases to 1 at Level 4
- [ ] Threat count increases with attacks
- [ ] Health Score decreases with severity

### Peer 1 Dashboard (Tab 2 - :3000)

- [ ] Security Alerts tab shows ALL 4 alerts
- [ ] Alert severity increases: LOW → MEDIUM → HIGH → CRITICAL
- [ ] Each alert shows attacker ID (truncated)
- [ ] Threat scores increase: ~15 → ~30 → ~60 → ~90
- [ ] Recommended actions change per level
- [ ] Chat disconnects at Level 2 (MEDIUM)
- [ ] Reconnection possible after Level 2 (if attempted)

### Peer 2 Dashboard (Tab 3 - :3002)

- [ ] Same as Peer 1 (both victims receive identical alerts)
- [ ] Security Alerts tab shows ALL 4 alerts
- [ ] Alert details match Peer 1's alerts
- [ ] Chat behavior matches Peer 1

### Peer 3 Dashboard (Tab 4 - :3003)

- [ ] Attack launch succeeds at all 4 levels
- [ ] Attack status shows success messages
- [ ] Last attack status updates after each launch
- [ ] Can launch all 3 attack types (Replay, Flooding, Auth Flooding)

---

## 🔧 Quick Verification Commands

### Run All Verifications at Once

```bash
# Copy this entire block and run in PowerShell or CMD

# 1. Check system status
echo "=== System Status ==="
curl -s http://localhost:5000/api/status/comprehensive | jq '{health_score: .system.health_score, isolated_peers: .threat_landscape.isolated_peers, total_attacks: .attack_statistics.total_attacks}'

# 2. Check isolated peers
echo ""
echo "=== Isolated Peers ==="
curl -s http://localhost:5000/api/peers | jq '.[] | select(.status == "isolated") | {id, status, security_level, keys_destroyed}'

# 3. Check active sessions
echo ""
echo "=== Active Sessions ==="
curl -s http://localhost:5000/api/flows | jq 'length'

# 4. Check all peer metrics
echo ""
echo "=== Attack Metrics ==="
curl -s http://localhost:5000/api/metrics/all | jq '{total_monitored: .total_peers_monitored, isolated: .isolated_peers, suspicious: .suspicious_peers}'
```

---

## 🚨 Common Issues & Fixes

### Issue 1: Alerts Not Appearing in Peer Dashboards

**Cause:** Notification endpoints failing

**Fix:**
```bash
# Check if peer backends are responding
curl http://localhost:8080/api/peer/status
curl http://localhost:8081/api/peer/status

# Check controller logs for notification failures
# Look for "⚠️ Failed to notify port" messages
```

### Issue 2: Sessions Not Terminating

**Cause:** No active sessions to terminate

**Fix:**
1. Create a session first:
   - Peer 1: Click "Connect" to Peer 2
   - Peer 2: Accept connection
   - Send messages to establish session
2. Then launch MEDIUM+ attack

### Issue 3: Peer Not Showing as Isolated

**Cause:** Need to reach CRITICAL level

**Fix:**
- Ensure you launch **CRITICAL** intensity attack
- Check controller logs for "PEER ISOLATED FROM NETWORK"
- Verify with: `curl http://localhost:5000/api/peers | jq '.[] | select(.status == "isolated")'`

### Issue 4: Controller Not Detecting Attacks

**Cause:** Peers not reporting to controller

**Fix:**
1. Ensure all peers started discovery
2. Check peer backends are running
3. Verify controller is running: `curl http://localhost:5000/api/status`

---

## 🎯 Success Indicators

After running all 4 levels, you should see:

### In Controller Dashboard:
```
✅ System Health: 70-85% (decreased from 100%)
✅ Total Attacks: 4+ (one per level minimum)
✅ Isolated Peers: 1
✅ Sessions Terminated: 1+ (if session existed)
✅ Keys Destroyed: 1
```

### In Victim Dashboards (Peer 1 & 2):
```
✅ 4+ alerts in Security Alerts tab
✅ Alerts span all severity levels: LOW, MEDIUM, HIGH, CRITICAL
✅ Latest alert shows CRITICAL with "THREAT NEUTRALIZED"
✅ Chat disconnected (if was connected)
```

### In Attacker Dashboard (Peer 3):
```
✅ All attack launches succeeded
✅ Attack status shows each result
✅ May show isolation effects (cannot connect to peers)
```

---

## 📝 Test Results Template

Use this to document your test results:

```
=== PROGRESSIVE SELF-DESTRUCT TEST RESULTS ===
Date: __________
Time: __________

LEVEL 1 (LOW):
  Controller Logs: [ ] Pass [ ] Fail
  Victim Alerts: [ ] Pass [ ] Fail
  Sessions Active: [ ] Pass [ ] Fail

LEVEL 2 (MEDIUM):
  Controller Logs: [ ] Pass [ ] Fail
  Victim Alerts: [ ] Pass [ ] Fail
  Sessions Terminated: [ ] Pass [ ] Fail

LEVEL 3 (HIGH):
  Controller Logs: [ ] Pass [ ] Fail
  Victim Alerts: [ ] Pass [ ] Fail
  Keys Destroyed: [ ] Pass [ ] Fail

LEVEL 4 (CRITICAL):
  Controller Logs: [ ] Pass [ ] Fail
  Victim Alerts: [ ] Pass [ ] Fail
  Peer Isolated: [ ] Pass [ ] Fail

OVERALL: [ ] All Pass [ ] Some Failures

Notes:
_________________________________________________
_________________________________________________
```

---

## 🎬 Demo Script

For a polished demonstration:

1. **Start (30 seconds):**
   - Show all 4 dashboards arranged
   - Explain: "All running on localhost, different tabs"
   - Start discovery on all peers

2. **Establish Baseline (30 seconds):**
   - Create Peer 1 ↔ Peer 2 session
   - Send test message: "Hello, testing secure chat"
   - Show controller: Everything normal, health 100%

3. **Level 1 Demo (1 minute):**
   - Launch LOW attack from Peer 3
   - Point to controller: "📊 Monitoring only"
   - Point to victims: "Alerts appear, but session still active"
   - Explain: "Warning only, no blocking yet"

4. **Level 2 Demo (1 minute):**
   - Launch MEDIUM attack
   - Point to controller: "⚠️ Session terminated"
   - Point to victims: "Connection dropped"
   - Point to session count: "Decreased to 0"
   - Explain: "Communication stopped, can reconnect later"

5. **Level 3 Demo (1 minute):**
   - Launch HIGH attack
   - Point to controller: "🔥 Keys destroyed"
   - Point to victims: "Must re-authenticate"
   - Show keys_destroyed: true
   - Explain: "Security credentials invalidated"

6. **Level 4 Demo (1 minute):**
   - Launch CRITICAL attack
   - Point to controller: "🚫 Peer isolated, threat neutralized"
   - Point to victims: "Network secured notification"
   - Show isolated peers: 1
   - Explain: "Complete ban, cannot reconnect"

7. **Wrap Up (30 seconds):**
   - Show comprehensive status
   - Highlight: Health score, isolated peers, total attacks
   - Emphasize: "Progressive response - punishment fits the crime"

---

## ✅ Final Verification

Run this comprehensive test:

```bash
# Save as verify-all.sh or run directly
echo "🔍 Starting Complete Verification..."
echo ""

echo "1. Controller Status:"
curl -s http://localhost:5000/api/status | jq '{active, active_peers, active_flows, recent_alerts}'
echo ""

echo "2. All Peer Backends:"
for port in 8080 8081 8082; do
  echo "  Port $port:"
  curl -s http://localhost:$port/api/peer/status | jq '{peer_name, running, discovered_peers}' 2>/dev/null || echo "  ❌ Not responding"
done
echo ""

echo "3. Attack Detection Readiness:"
curl -s http://localhost:5000/api/security/config | jq '.configuration.replay_thresholds'
echo ""

echo "4. System Health:"
curl -s http://localhost:5000/api/status/comprehensive | jq '{health_score: .system.health_score, isolated_peers: .threat_landscape.isolated_peers, suspicious_peers: .threat_landscape.suspicious_peers}'
echo ""

echo "✅ Verification Complete!"
```

---

**Your system is READY FOR TESTING!** 🚀

All 4 levels are properly implemented for localhost development with:
- ✅ Real attack detection
- ✅ Automatic progressive response
- ✅ Victim notifications to ports 8080 & 8081
- ✅ Session termination
- ✅ Key destruction
- ✅ Peer isolation
- ✅ Real-time dashboard updates

**Start testing now using the step-by-step guide above!**
