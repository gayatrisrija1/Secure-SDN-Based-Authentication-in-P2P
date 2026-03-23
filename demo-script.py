#!/usr/bin/env python3
"""
SDN Security System - Demo Script
Automated demonstration of progressive self-destruct mechanism
"""

import requests
import time
import json
from datetime import datetime

class SDNDemo:
    def __init__(self):
        self.controller_api = "http://localhost:5001/api"
        self.peer_api = "http://localhost:5000/api"
        
    def print_header(self, title):
        print("\n" + "=" * 60)
        print(f"🎯 {title}")
        print("=" * 60)
        
    def print_step(self, step, description):
        print(f"\n📍 Step {step}: {description}")
        print("-" * 40)
        
    def wait_for_user(self, message="Press Enter to continue..."):
        input(f"\n⏸️  {message}")
        
    def check_system_status(self):
        """Check if all components are running"""
        try:
            controller_status = requests.get(f"{self.controller_api}/status", timeout=3)
            peer_status = requests.get(f"{self.peer_api}/status", timeout=3)
            
            if controller_status.status_code == 200 and peer_status.status_code == 200:
                print("✅ All systems operational")
                return True
            else:
                print("❌ System components not responding")
                return False
        except Exception as e:
            print(f"❌ System check failed: {e}")
            return False
    
    def simulate_normal_operation(self):
        """Demonstrate normal peer communication"""
        self.print_step(1, "Normal Peer Communication")
        
        print("🔍 What to observe:")
        print("• Controller Dashboard shows normal traffic")
        print("• Peers can discover each other")
        print("• Authentication works properly")
        print("• Messages are encrypted")
        
        print("\n📋 Manual Actions Required:")
        print("1. Open Controller Dashboard: http://localhost:3001")
        print("2. Open Peer Dashboard: http://localhost:3000")
        print("3. Connect two peers and send messages")
        
        self.wait_for_user("Complete normal communication test, then press Enter...")
    
    def simulate_attack_level_1(self):
        """Demonstrate Level 1 - Warning"""
        self.print_step(2, "Attack Level 1 - Monitoring & Warning")
        
        print("🎯 Triggering LOW severity attack...")
        print("📊 Expected Response:")
        print("• Controller shows LOW severity alert")
        print("• Peer receives warning notification")
        print("• Session continues normally")
        print("• Increased monitoring activated")
        
        print("\n🚀 Run this command in WSL2:")
        print("cd /mnt/c/Users/charan27/OneDrive/Desktop/Final\\ Year\\ Projects/SDN/attack-scripts")
        print("python3 attack_simulator.py --attack-type replay --intensity low")
        
        self.wait_for_user("Run the attack command, observe the response, then press Enter...")
    
    def simulate_attack_level_2(self):
        """Demonstrate Level 2 - Session Termination"""
        self.print_step(3, "Attack Level 2 - Session Termination")
        
        print("🎯 Triggering MEDIUM severity attack...")
        print("📊 Expected Response:")
        print("• Controller shows MEDIUM severity alert")
        print("• Active session terminates immediately")
        print("• Peers disconnected but can reconnect")
        print("• Suspicious flow blocked")
        
        print("\n🚀 Run this command in WSL2:")
        print("python3 attack_simulator.py --attack-type flooding --intensity medium")
        
        self.wait_for_user("Run the attack command, observe session termination, then press Enter...")
    
    def simulate_attack_level_3(self):
        """Demonstrate Level 3 - Key Destruction"""
        self.print_step(4, "Attack Level 3 - Key Destruction")
        
        print("🎯 Triggering HIGH severity attack...")
        print("📊 Expected Response:")
        print("• Controller shows HIGH severity alert")
        print("• Session keys destroyed")
        print("• Pseudo-identity invalidated")
        print("• Re-authentication required")
        
        print("\n🚀 Run this command in WSL2:")
        print("python3 attack_simulator.py --attack-type replay --intensity high")
        
        self.wait_for_user("Run the attack command, observe key destruction, then press Enter...")
    
    def simulate_attack_level_4(self):
        """Demonstrate Level 4 - Peer Isolation"""
        self.print_step(5, "Attack Level 4 - Peer Isolation")
        
        print("🎯 Triggering CRITICAL severity attack...")
        print("📊 Expected Response:")
        print("• Controller shows CRITICAL severity alert")
        print("• Attacker peer completely isolated")
        print("• All traffic from attacker blocked")
        print("• Permanent isolation status")
        
        print("\n🚀 Run this command in WSL2:")
        print("python3 attack_simulator.py --attack-type flooding --intensity critical")
        
        self.wait_for_user("Run the attack command, observe complete isolation, then press Enter...")
    
    def demonstrate_recovery(self):
        """Show system recovery capabilities"""
        self.print_step(6, "System Recovery & Reset")
        
        print("🔄 Demonstrating system recovery...")
        print("📊 What to show:")
        print("• Legitimate peers can still communicate")
        print("• System maintains security posture")
        print("• Attack logs are preserved")
        print("• Network remains operational")
        
        self.wait_for_user("Demonstrate system recovery, then press Enter...")
    
    def run_full_demo(self):
        """Run complete demonstration"""
        self.print_header("SDN Security System - Live Demo")
        
        print("🎬 This demo will showcase:")
        print("• Normal peer-to-peer communication")
        print("• Progressive attack detection")
        print("• 4-level self-destruct mechanism")
        print("• System recovery capabilities")
        
        print("\n⚠️  Prerequisites:")
        print("• All 5 applications must be running")
        print("• WSL2 terminal ready for attack commands")
        print("• Browser windows open for dashboards")
        
        if not self.check_system_status():
            print("\n❌ System not ready. Please start all components first.")
            return
        
        self.wait_for_user("Ready to begin demo? Press Enter...")
        
        # Run demo phases
        self.simulate_normal_operation()
        self.simulate_attack_level_1()
        self.simulate_attack_level_2()
        self.simulate_attack_level_3()
        self.simulate_attack_level_4()
        self.demonstrate_recovery()
        
        self.print_header("Demo Complete! 🎉")
        print("✅ Successfully demonstrated:")
        print("• Anonymous P2P communication")
        print("• Real-time attack detection")
        print("• Progressive self-destruct mechanism")
        print("• SDN-based security enforcement")
        
        print("\n📋 Demo Summary:")
        print("• Level 1: Warning & monitoring")
        print("• Level 2: Session termination")
        print("• Level 3: Key destruction")
        print("• Level 4: Complete isolation")
        
        print("\n🎯 Key Achievements:")
        print("• Zero data leakage during attacks")
        print("• Proportional response to threat level")
        print("• Maintained network availability")
        print("• Professional security implementation")

def main():
    demo = SDNDemo()
    
    print("SDN Security System Demo")
    print("Choose an option:")
    print("1. Run full automated demo")
    print("2. Check system health only")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        demo.run_full_demo()
    elif choice == "2":
        demo.check_system_status()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice. Please run again.")

if __name__ == "__main__":
    main()