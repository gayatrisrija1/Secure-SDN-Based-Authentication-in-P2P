# WSL2 Setup Guide for SDN Development

## Why WSL2 is Required
- Ryu SDN Controller needs Linux kernel features
- Open vSwitch requires native Linux networking
- Better isolation for SDN experiments
- Seamless integration with Windows development

## Step-by-Step Installation

### 1. Enable WSL Feature
Open PowerShell as Administrator and run:
```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

### 2. Restart Windows
**IMPORTANT**: Restart your computer now.

### 3. Set WSL2 as Default
After restart, open PowerShell as Administrator:
```powershell
wsl --set-default-version 2
```

### 4. Install Ubuntu 22.04
```powershell
wsl --install -d Ubuntu-22.04
```

### 5. Initial Ubuntu Setup
When Ubuntu starts:
1. Create username (e.g., `sdn-user`)
2. Create password
3. Update system:
```bash
sudo apt update && sudo apt upgrade -y
```

### 6. Install Required Packages
```bash
# Python and development tools
sudo apt install -y python3.10 python3-pip python3-venv git curl

# SDN components
sudo apt install -y openvswitch-switch openvswitch-common

# Network tools
sudo apt install -y net-tools iproute2 tcpdump
```

### 7. Install Ryu Controller
```bash
pip3 install ryu==4.34
```

### 8. Verify Installation
```bash
# Check Python version
python3 --version

# Check Ryu installation
ryu-manager --version

# Check OVS installation
sudo ovs-vsctl show
```

## Network Configuration

### WSL2 IP Discovery
```bash
# Find WSL2 IP address
ip addr show eth0
```

### Windows-WSL Communication
- WSL2 can access Windows via `localhost`
- Windows accesses WSL2 via WSL2's IP address
- Ports are automatically forwarded

## Troubleshooting

### Common Issues
1. **WSL2 not starting**: Check Windows version (requires Windows 10 version 2004+)
2. **Network issues**: Restart WSL with `wsl --shutdown` then `wsl`
3. **Permission errors**: Use `sudo` for system operations

### Verification Commands
```bash
# Test network connectivity
ping google.com

# Test Python
python3 -c "print('Python working')"

# Test Ryu
python3 -c "import ryu; print('Ryu installed')"
```

## Next Steps
After WSL2 setup is complete:
1. Clone project to WSL2 filesystem
2. Set up SDN controller
3. Configure network bridges
4. Test basic connectivity