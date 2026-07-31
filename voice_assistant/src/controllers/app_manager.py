"""
Application Manager Controller
Handles opening and closing applications
"""

import subprocess
import psutil
import os
from typing import Dict, Optional


class AppManager:
    def __init__(self):
        """Initialize app manager"""
        # System processes to exclude when closing all apps
        self.system_processes = [
            'systemd', 'gnome-shell', 'Xorg', 'wayland', 
            'pulseaudio', 'pipewire', 'NetworkManager',
            'kernel', 'kthreadd', 'ksoftirqd'
        ]
        
    def _find_app_command(self, app_name: str) -> Optional[str]:
        """
        Find the command to run an app by searching system dynamically
        
        Args:
            app_name: Name of the application
            
        Returns:
            Command string if found, None otherwise
        """
        # Try the app name directly
        if self._command_exists(app_name):
            return app_name
        
        # Try with common prefixes
        prefixes = ["", "gnome-", "kde-", "xfce4-", "gtk-"]
        for prefix in prefixes:
            cmd = f"{prefix}{app_name}"
            if self._command_exists(cmd):
                return cmd
        
        # Try searching in /usr/share/applications
        cmd = self._find_from_desktop_files(app_name)
        if cmd:
            return cmd
        
        # Try fuzzy matching with hyphens
        app_name_hyphen = app_name.replace(" ", "-")
        if self._command_exists(app_name_hyphen):
            return app_name_hyphen
        
        return None
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _find_from_desktop_files(self, app_name: str) -> Optional[str]:
        """Find app command from desktop files"""
        desktop_dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications")
        ]
        
        app_name_lower = app_name.lower().replace(" ", "-")
        
        for dir_path in desktop_dirs:
            if not os.path.exists(dir_path):
                continue
            
            for filename in os.listdir(dir_path):
                if not filename.endswith(".desktop"):
                    continue
                
                filepath = os.path.join(dir_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Check if app_name is in filename or content
                    if app_name_lower in filename.lower() or app_name_lower in content.lower():
                        # Extract Exec line
                        for line in content.split('\n'):
                            if line.startswith('Exec='):
                                cmd = line[5:].split()[0]  # Get first word after Exec=
                                if self._command_exists(cmd):
                                    return cmd
                                return cmd  # Return anyway, might work
                except:
                    continue
        
        return None
        
    def open_app(self, app_name: str) -> bool:
        """
        Open an application
        
        Args:
            app_name: Name of the application
            
        Returns:
            True if successful
        """
        # Find the command
        cmd = self._find_app_command(app_name)
        
        if not cmd:
            print(f"✗ Could not find app: {app_name}")
            return False
            
        try:
            subprocess.Popen([cmd], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL,
                          start_new_session=True)
            print(f"✓ Opened {app_name}")
            return True
        except FileNotFoundError:
            print(f"✗ {app_name} not installed")
            return False
        except Exception as e:
            print(f"✗ Failed to open {app_name}: {e}")
            return False
    
    def close_app(self, app_name: str) -> bool:
        """
        Close an application by searching for it dynamically
        
        Args:
            app_name: Name of the application
            
        Returns:
            True if successful
        """
        # Find the command for this app
        cmd = self._find_app_command(app_name)
        
        # If command not found, try to search by app name directly in processes
        if not cmd:
            cmd = app_name
        
        closed = False
        pids_to_close = []
        
        # First pass: collect PIDs
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check by process name or command line
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""
                    
                    # Check if command matches (with various variations)
                    app_variations = [
                        cmd.lower(),
                        cmd.replace("-", "").lower(),
                        cmd.replace("_", "").lower(),
                        cmd.split("/")[-1].lower() if "/" in cmd else cmd.lower()
                    ]
                    
                    for variation in app_variations:
                        if variation in proc_name or variation in cmdline:
                            pids_to_close.append(proc.info['pid'])
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
            if not pids_to_close:
                print(f"✗ {app_name} not running")
                return False
                
            # Close main process only (first PID)
            main_pid = pids_to_close[0]
            try:
                proc = psutil.Process(main_pid)
                proc.terminate()
                
                # Wait for process to terminate
                try:
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    proc.kill()
                    proc.wait(timeout=2)
                
                closed = True
                print(f"✓ Closed {app_name}")
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                closed = False
                
            return closed
            
        except Exception as e:
            print(f"✗ Failed to close {app_name}: {e}")
            return False
    
    def close_all_apps(self) -> bool:
        """
        Close all user applications (excluding system processes)
        
        Returns:
            True if successful
        """
        print("Closing all applications...")
        closed_count = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    # Skip system processes
                    if not proc.info['name']:
                        continue
                        
                    proc_name = proc.info['name'].lower()
                    
                    # Skip system processes
                    if any(sys_proc in proc_name for sys_proc in self.system_processes):
                        continue
                        
                    # Only close user processes (PID > 1000 typically)
                    if proc.info['pid'] <= 1000:
                        continue
                        
                    # Skip kernel threads
                    if not proc.info['username']:
                        continue
                        
                    proc.terminate()
                    closed_count += 1
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
            print(f"✓ Closed {closed_count} applications")
            return True
            
        except Exception as e:
            print(f"✗ Failed to close all apps: {e}")
            return False
    
    def is_running(self, app_name: str) -> bool:
        """
        Check if an application is running by searching dynamically
        
        Args:
            app_name: Name of the application
            
        Returns:
            True if running
        """
        # Find the command for this app
        cmd = self._find_app_command(app_name)
        
        # If command not found, try to search by app name directly in processes
        if not cmd:
            cmd = app_name
        
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""
                    
                    # Check if command matches (with various variations)
                    app_variations = [
                        cmd.lower(),
                        cmd.replace("-", "").lower(),
                        cmd.replace("_", "").lower(),
                        cmd.split("/")[-1].lower() if "/" in cmd else cmd.lower()
                    ]
                    
                    for variation in app_variations:
                        if variation in proc_name or variation in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
            return False
            
        except Exception:
            return False
    
    def list_supported_apps(self) -> Dict[str, str]:
        """
        Get list of supported applications (dynamic - returns empty since no hardcoded apps)
        
        Returns:
            Empty dictionary (apps are discovered dynamically)
        """
        return {}
