"""
System Controller
Handles system power controls (power off, restart)
"""

import subprocess
import time


class SystemController:
    def __init__(self):
        """Initialize system controller"""
        self.shutdown_delay = 10  # seconds
        
    def power_off(self, delay: int = None) -> bool:
        """
        Power off the system
        
        Args:
            delay: Delay in seconds before shutdown (default from config)
            
        Returns:
            True if command initiated
        """
        if delay is None:
            delay = self.shutdown_delay
            
        print(f"⚠️  Powering off system in {delay} seconds...")
        print("Press Ctrl+C to cancel")
        
        try:
            time.sleep(delay)
            subprocess.run(["poweroff"], check=False)
            return True
        except KeyboardInterrupt:
            print("✓ Shutdown cancelled")
            return False
        except Exception as e:
            print(f"✗ Failed to power off: {e}")
            return False
    
    def restart(self, delay: int = None) -> bool:
        """
        Restart the system
        
        Args:
            delay: Delay in seconds before restart (default from config)
            
        Returns:
            True if command initiated
        """
        if delay is None:
            delay = self.shutdown_delay
            
        print(f"⚠️  Restarting system in {delay} seconds...")
        print("Press Ctrl+C to cancel")
        
        try:
            time.sleep(delay)
            subprocess.run(["reboot"], check=False)
            return True
        except KeyboardInterrupt:
            print("✓ Restart cancelled")
            return False
        except Exception as e:
            print(f"✗ Failed to restart: {e}")
            return False
    
    def lock_screen(self) -> bool:
        """
        Lock the screen
        
        Returns:
            True if successful
        """
        try:
            # Try different commands based on desktop environment
            commands = [
                ["gnome-screensaver-command", "--lock"],
                ["xdg-screensaver", "lock"],
                ["loginctl", "lock-session"]
            ]
            
            for cmd in commands:
                try:
                    subprocess.run(cmd, check=True, 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
                    print("✓ Screen locked")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
                    
            print("✗ Failed to lock screen")
            return False
            
        except Exception as e:
            print(f"✗ Error locking screen: {e}")
            return False
    
    def suspend(self) -> bool:
        """
        Suspend the system
        
        Returns:
            True if successful
        """
        try:
            subprocess.run(["systemctl", "suspend"], check=False)
            print("✓ System suspending")
            return True
        except Exception as e:
            print(f"✗ Failed to suspend: {e}")
            return False
