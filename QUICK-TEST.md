# Quick Testing Checklist

## Before You Start Testing

### 1. Verify All Applications Are Running
Run the health check script:
```bash
cd "c:\Users\charan27\OneDrive\Desktop\Final Year Projects\SDN"
python health-check.py
```

Expected output: "🎉 ALL SYSTEMS OPERATIONAL (8/8)"

### 2. Open Required Browser Windows
- Controller Dashboard: http://localhost:3001
- Peer Dashboard: http://localhost:3000
- Keep both windows visible side by side

### 3. Prepare WSL2 Terminal
- Open WSL2 Ubuntu terminal
- Navigate to attack scripts directory:
```bash
cd /mnt/c/Users/charan27/OneDrive/Desktop/Final\ Year\ Projects/SDN/attack-scripts
```

## Quick 5-Minute Test

### Test 1: Normal Communication (2 minutes)
1. ✅ Open Peer Dashboard (http://localhost:3000)
2. ✅ Click "Discover Peers" 
3. ✅ Select a peer and click "Connect"
4. ✅ Send a test message: "Hello, this is a secure test message"
5. ✅ Verify message appears encrypted in Controller Dashboard

### Test 2: Attack Response (3 minutes)
1. ✅ Run Level 1 Attack (WSL2):
   ```bash
   python3 attack_simulator.py --attack-type replay --intensity low
   ```
   - Should see LOW severity alert in Controller Dashboard
   - Peer should receive warning but stay connected

2. ✅ Run Level 4 Attack (WSL2):
   ```bash
   python3 attack_simulator.py --attack-type flooding --intensity critical
   ```
   - Should see CRITICAL severity alert
   - Peer should be completely isolated

## Full Demo Test (15 minutes)

Run the automated demo script:
```bash
python demo-script.py
```

Choose option 1 for full demo, then follow the on-screen instructions.

## Success Indicators

✅ **System Health**: All 8 components responding
✅ **Peer Discovery**: Peers found automatically  
✅ **Authentication**: Connection established successfully
✅ **Encryption**: Messages encrypted in transit
✅ **Attack Detection**: All 4 severity levels trigger correctly
✅ **Progressive Response**: Each level executes appropriate action
✅ **UI Updates**: Dashboards show real-time status changes

## If Something Fails

1. **Check health-check.py output** - identifies which component failed
2. **Restart failed components** - refer to installation-guide.md
3. **Check browser console** - for UI-related errors
4. **Verify WSL2 connectivity** - ensure SDN controller is accessible

## Demo Presentation Tips

1. **Start with system overview** - explain the architecture
2. **Show normal operation first** - establish baseline
3. **Demonstrate progressive attacks** - show each severity level
4. **Highlight security features** - encryption, anonymity, no storage
5. **Emphasize real-world applicability** - enterprise security use cases

## Ready to Test?

If all checkboxes above are ✅, you're ready to demonstrate your SDN security system!

Start with: `python health-check.py`