"""
System Controller
Handles system power controls, volume, battery status, system stats, time/date, and web search.
"""

import os
import subprocess
import time
import datetime
import webbrowser
import psutil


class SystemController:
    def __init__(self):
        """Initialize system controller"""
        self.shutdown_delay = 10  # seconds

    def get_battery_info(self) -> str:
        """Get battery percentage and status"""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return "Sir, I could not find a battery on this system."
            
            percent = int(battery.percent)
            plugged = battery.power_plugged
            status_str = "plugged in and charging" if plugged else "running on battery power"
            return f"Sir, your battery is at {percent} percent, and the system is {status_str}."
        except Exception as e:
            return "Sorry sir, I failed to retrieve battery information."

    def get_system_status(self) -> str:
        """Get CPU and RAM usage"""
        try:
            cpu_usage = psutil.cpu_percent(interval=0.5)
            ram_usage = psutil.virtual_memory().percent
            return f"Sir, current CPU usage is {cpu_usage} percent, and RAM usage is at {ram_usage} percent."
        except Exception as e:
            return "Sorry sir, I could not get system statistics."

    def get_time_date(self) -> str:
        """Get current time and date"""
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%B %d, %Y")
        return f"Sir, the current time is {time_str}, and today is {date_str}."

    def set_volume(self, action: str) -> str:
        """Change system volume using amixer, wpctl, or pactl"""
        try:
            if action == "up":
                commands = [
                    ["amixer", "-D", "pulse", "sset", "Master", "10%+"],
                    ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "10%+"],
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"]
                ]
                msg = "Sir, increasing volume."
            elif action == "down":
                commands = [
                    ["amixer", "-D", "pulse", "sset", "Master", "10%-"],
                    ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "10%-"],
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"]
                ]
                msg = "Sir, decreasing volume."
            else:  # mute/unmute
                commands = [
                    ["amixer", "-D", "pulse", "sset", "Master", "toggle"],
                    ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"],
                    ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"]
                ]
                msg = "Sir, toggling mute."

            for cmd in commands:
                try:
                    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if res.returncode == 0:
                        return msg
                except Exception:
                    continue

            return msg
        except Exception:
            return "Sir, I could not adjust system volume."

    def search_web(self, query: str) -> str:
        """Search Google or YouTube based on query"""
        if not query:
            return "Sir, please specify what you want to search for."

        q_lower = query.lower()
        if "youtube" in q_lower:
            search_term = q_lower.replace("search youtube for", "").replace("youtube search", "").replace("youtube", "").strip()
            url = f"https://www.youtube.com/results?search_query={search_term}"
            webbrowser.open(url)
            return f"Sir, searching YouTube for {search_term}"
        else:
            search_term = q_lower.replace("search google for", "").replace("google search", "").replace("search web for", "").replace("search for", "").strip()
            url = f"https://www.google.com/search?q={search_term}"
            webbrowser.open(url)
            return f"Sir, searching Google for {search_term}"

    def power_off(self, delay: int = None) -> bool:
        """Power off the system"""
        if delay is None:
            delay = self.shutdown_delay
            
        print(f"⚠️  Powering off system in {delay} seconds...")
        try:
            subprocess.run(["poweroff"], check=False)
            return True
        except Exception as e:
            print(f"✗ Failed to power off: {e}")
            return False
    
    def restart(self, delay: int = None) -> bool:
        """Restart the system"""
        if delay is None:
            delay = self.shutdown_delay
            
        print(f"⚠️  Restarting system in {delay} seconds...")
        try:
            subprocess.run(["reboot"], check=False)
            return True
        except Exception as e:
            print(f"✗ Failed to restart: {e}")
            return False
    
    def lock_screen(self) -> bool:
        """Lock the screen"""
        try:
            commands = [
                ["gnome-screensaver-command", "--lock"],
                ["xdg-screensaver", "lock"],
                ["loginctl", "lock-session"]
            ]
            for cmd in commands:
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("✓ Screen locked")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            return False
        except Exception as e:
            print(f"✗ Error locking screen: {e}")
            return False
    
    def suspend(self) -> bool:
        """Suspend the system"""
        try:
            subprocess.run(["systemctl", "suspend"], check=False)
            print("✓ System suspending")
            return True
        except Exception as e:
            print(f"✗ Failed to suspend: {e}")
            return False

