# What Are "Keys" in This System?

## Simple Explanation

**Key** = Secret code that locks and unlocks messages

Think of it like a physical key:
- 🔑 **With key**: You can unlock (decrypt) messages
- 🚫 **Without key**: Messages stay locked, can't read them

---

## Technical Explanation

### Session Key = AES-256 Encryption Key

**Type**: Symmetric encryption key
**Size**: 256 bits (32 bytes)
**Algorithm**: AES-256 (Advanced Encryption Standard)
**Format**: Random bytes, example: `b'\xa8\xf3....\x2b\x9c'`

### Where It's Stored

```python
# In peer_app.py:
peer_instance.session_key = b'32_random_bytes_here'  # ← THIS is the key
```

### What It Does

**Encrypts messages before sending:**
```python
plaintext = "Hello, this is secret"
encrypted = AES.encrypt(plaintext, session_key)
# Result: b'\x9a\x4f\x8e\x2b\x7c...'  ← Unreadable without key
```

**Decrypts received messages:**
```python
encrypted = b'\x9a\x4f\x8e\x2b\x7c...'
plaintext = AES.decrypt(encrypted, session_key)
# Result: "Hello, this is secret"  ← Readable again
```

---

## Key Lifecycle

### 1. Session Start (Key Generation)

```
Peer 1 connects to Peer 3
    ↓
Key exchange (Diffie-Hellman or similar)
    ↓
Both peers derive the same session_key
    ↓
✅ Session active, encrypted communication possible
```

**Code:**
```python
peer_instance.session_key = generate_session_key()
peer_instance.active_session = {
    'peer_id': '877b6c8c...',
    'authenticated': True
}
```

---

### 2. Active Session (Key in Use)

```
Peer 1 → Encrypt("Attack at dawn") with session_key → Peer 3
Peer 3 → Encrypt("Roger that") with session_key → Peer 1
```

**Dashboard shows:**
```
🔒 Encryption: AES-256 Active
✅ Session Key: Present
📝 Messages: 5
```

---

### 3. Key Destruction (HIGH Level Attack)

```
Controller detects HIGH level attack (5 attacks)
    ↓
Controller sends KEYS_DESTROYED notification
    ↓
Victim peer receives notification
    ↓
✅ IF connected to attacker:
   peer_instance.session_key = None  ← KEY DESTROYED!
   peer_instance.active_session = None
   peer_instance.message_history = []
```

**What gets destroyed:**
```python
# Before:
session_key = b'\xa8\xf3...\x2b\x9c'  # 32 random bytes
active_session = {'peer_id': 'attacker', ...}
message_history = [{msg1}, {msg2}, {msg3}]

# After:
session_key = None  # ← KEY DELETED FROM MEMORY
active_session = None  # ← SESSION TERMINATED
message_history = []  # ← MESSAGES CLEARED
```

**Terminal log:**
```
ERROR: 🔐 KEYS DESTROYED by controller (attacker: 877b6c8c...)
```

---

### 4. Post-Destruction (No Key)

```
Try to send message: "New plan"
    ↓
ERROR: No session key available
    ↓
❌ Cannot encrypt message
❌ Cannot send
```

**Dashboard shows:**
```
❌ No active session
🚫 Session Key: None
📭 Messages: 0 (cleared)
```

---

## How to Verify Key Destruction

### Method 1: Use Diagnostic Script

```bash
python check-session-key.py
```

**Before attack:**
```
Peer 1 (Victim)
  Active Session: True
  Session Key: [PRESENT]  ← Has encryption key
  Messages: 3
```

**After HIGH attack:**
```
Peer 1 (Victim)
  Active Session: False
  Session Key: [NONE]  ← Key destroyed!
  Messages: 0
```

---

### Method 2: Check API Directly

**Before attack:**
```bash
curl http://localhost:8080/api/peer/status
```
```json
{
  "active_session": true,
  "message_count": 3
}
```

**After HIGH attack:**
```bash
curl http://localhost:8080/api/peer/status
```
```json
{
  "active_session": false,
  "message_count": 0
}
```

---

### Method 3: Test Sending Messages

**Before attack:**
- ✅ Can type and send messages
- ✅ Messages are encrypted with session_key
- ✅ Recipient can decrypt and read

**After key destruction:**
- ❌ "No active session" message appears
- ❌ Message input disabled
- ❌ Can't send messages (no key to encrypt with)

---

## Security Properties

### Why Destroy Keys?

**1. Forward Secrecy**
- Old messages can't be decrypted (key is gone)
- Even if attacker had encrypted messages saved, they're useless

**2. Immediate Protection**
- Attacker can't send more encrypted messages
- Victim is protected from further communication with attacker

**3. Clean Slate**
- Message history cleared
- No record of conversation
- Fresh start required

---

## Key vs Other Data

| Data Type | What It Is | Destroyed? |
|-----------|------------|------------|
| **Session Key** | 32-byte AES-256 encryption key | ✅ YES (set to None) |
| **Active Session** | Connection info (peer_id, timestamp) | ✅ YES (set to None) |
| **Message History** | Array of sent/received messages | ✅ YES (cleared to []) |
| **Pseudo ID** | Peer's identity (hash) | ❌ NO (permanent) |
| **Discovered Peers** | List of known peers | ❌ NO (kept) |
| **Security Alerts** | Attack warnings | ❌ NO (kept for evidence) |

---

## Real-World Analogy

### Before Key Destruction:
```
You and your friend have matching secret decoder rings 🔑🔑
You: "ATTACK AT DAWN" → Encode → "NGGNPX NG QNJA"
Friend: "NGGNPX NG QNJA" → Decode → "ATTACK AT DAWN" ✅
```

### After Key Destruction:
```
Controller smashes your decoder ring 💥
You: "NEW PLAN" → Need to encode → ❌ No decoder ring!
Friend: Can't send encrypted messages anymore
```

Your decoder ring = session_key
Smashing it = Setting session_key to None

---

## Summary

**What is a key?**
- 32-byte random encryption key for AES-256

**Where is it?**
- `peer_instance.session_key` in memory

**What does destruction do?**
- Sets key to `None`
- Terminates session
- Clears message history
- Prevents encrypted communication

**How to verify?**
- Check `active_session: false` in API
- Try to send message (should fail)
- Look for `🔐 KEYS DESTROYED` in terminal

**Why it matters?**
- Protects victim from further attacks
- Ensures past encrypted messages stay encrypted
- Forces clean break from malicious peer

---

## Test It Yourself

```bash
# 1. Check current status
python check-session-key.py

# 2. Connect Peer 1 to Peer 3 and chat

# 3. Check status again (should show key present)
python check-session-key.py

# 4. Launch HIGH attack from Peer 3

# 5. Check status one more time (key should be NONE)
python check-session-key.py

# 6. Try to send a message on Peer 1 (should fail!)
```

The key is what makes encrypted communication possible. Destroying it makes communication impossible! 🔐💥
