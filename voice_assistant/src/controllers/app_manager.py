"""
Application Manager Controller
Handles dynamic opening, searching, and closing of Linux applications using desktop entry indexing and fuzzy matching.
"""

import os
import re
import shlex
import subprocess
import psutil
from typing import Dict, List, Optional, Tuple
import difflib


class AppEntry:
    def __init__(self, name: str, exec_cmd: str, desktop_file: str, 
                 generic_name: str = "", keywords: str = "", wm_class: str = ""):
        self.name = name
        self.exec_cmd = exec_cmd
        self.desktop_file = desktop_file
        self.desktop_id = os.path.basename(desktop_file).replace('.desktop', '')
        self.generic_name = generic_name
        self.keywords = keywords
        self.wm_class = wm_class

    def __repr__(self):
        return f"<AppEntry name='{self.name}' id='{self.desktop_id}' exec='{self.exec_cmd}'>"


class AppManager:
    def __init__(self):
        """Initialize app manager and index desktop applications"""
        # Common aliases dictionary to map conversational phrases to standard app names/keywords
        self.aliases = {
            "chrome": ["google-chrome", "google chrome", "chrome", "browser"],
            "google chrome": ["google-chrome", "chrome"],
            "vs code": ["code", "vscode", "visual studio code"],
            "vscode": ["code", "vs code", "visual studio code"],
            "visual studio code": ["code", "vscode"],
            "terminal": ["gnome-terminal", "terminal", "alacritty", "kitty", "konsole", "xfce4-terminal"],
            "command prompt": ["gnome-terminal", "terminal"],
            "cmd": ["gnome-terminal", "terminal"],
            "calculator": ["gnome-calculator", "calculator", "kcalc"],
            "files": ["nautilus", "files", "file manager", "thunar", "dolphin"],
            "file manager": ["nautilus", "files", "thunar", "dolphin"],
            "explorer": ["nautilus", "files"],
            "settings": ["gnome-control-center", "settings", "system settings"],
            "system settings": ["gnome-control-center", "settings"],
            "text editor": ["gedit", "gnome-text-editor", "kate", "notepad"],
            "notepad": ["gedit", "gnome-text-editor", "kate"],
            "browser": ["google-chrome", "firefox", "brave", "microsoft-edge"],
            "web browser": ["google-chrome", "firefox", "brave"],
            "obs": ["obs studio", "com.obsproject.Studio", "obs"],
            "spotify": ["spotify", "com.spotify.Client"],
            "discord": ["discord", "com.discordapp.Discord"],
            "vlc": ["vlc", "vlc media player"],
            "media player": ["vlc", "totem", "celluloid"],
            "system monitor": ["gnome-system-monitor", "system monitor", "htop"],
            "task manager": ["gnome-system-monitor", "system monitor"],
            "postman": ["postman"],
            "pycharm": ["pycharm", "pycharm-community", "pycharm-professional"],
            "sublime": ["sublime-text", "sublime_text", "sublime"],
            "sublime text": ["sublime-text", "sublime_text"],
            "telegram": ["telegram-desktop", "telegram"],
            "gimp": ["gimp"],
            "trash": ["nautilus trash:///", "files"]
        }

        # Excluded processes when closing all user apps
        self.system_processes = [
            'systemd', 'gnome-shell', 'xorg', 'wayland', 'pulseaudio', 'pipewire',
            'networkmanager', 'kernel', 'kthreadd', 'ksoftirqd', 'dbus-daemon',
            'dock', 'panel', 'ibus-daemon', 'gdm', 'lightdm', 'sddm', 'python'
        ]

        self.apps_index: List[AppEntry] = []
        self._index_desktop_files()

    def _clean_exec_command(self, exec_str: str) -> str:
        """Strip desktop field codes like %f, %F, %u, %U, %k, %i, etc."""
        # Remove field codes
        cleaned = re.sub(r'%[fFuUkKiIcCnNdDsS]', '', exec_str)
        cleaned = cleaned.strip()
        return cleaned

    def _index_desktop_files(self):
        """Build an index of all installed applications from .desktop files"""
        desktop_dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
            "/var/lib/snapd/desktop/applications"
        ]

        indexed_ids = set()

        for dir_path in desktop_dirs:
            if not os.path.exists(dir_path):
                continue

            for root, _, files in os.walk(dir_path):
                for filename in files:
                    if not filename.endswith(".desktop"):
                        continue

                    filepath = os.path.join(root, filename)
                    desktop_id = filename.replace(".desktop", "")

                    if desktop_id in indexed_ids:
                        continue

                    try:
                        name = ""
                        exec_cmd = ""
                        generic_name = ""
                        keywords = ""
                        wm_class = ""
                        no_display = False
                        in_main_section = False

                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in f:
                                line = line.strip()
                                if line == "[Desktop Entry]":
                                    in_main_section = True
                                    continue
                                elif line.startswith("[") and line.endswith("]"):
                                    in_main_section = False

                                if in_main_section:
                                    if line.startswith("Name=") and not name:
                                        name = line[5:].strip()
                                    elif line.startswith("Exec=") and not exec_cmd:
                                        exec_cmd = line[5:].strip()
                                    elif line.startswith("GenericName=") and not generic_name:
                                        generic_name = line[12:].strip()
                                    elif line.startswith("Keywords=") and not keywords:
                                        keywords = line[9:].strip()
                                    elif line.startswith("StartupWMClass=") and not wm_class:
                                        wm_class = line[15:].strip()
                                    elif line.startswith("NoDisplay=true"):
                                        no_display = True

                        if no_display or not name or not exec_cmd:
                            continue

                        clean_exec = self._clean_exec_command(exec_cmd)
                        app_entry = AppEntry(
                            name=name,
                            exec_cmd=clean_exec,
                            desktop_file=filepath,
                            generic_name=generic_name,
                            keywords=keywords,
                            wm_class=wm_class
                        )
                        self.apps_index.append(app_entry)
                        indexed_ids.add(desktop_id)

                    except Exception:
                        continue

        print(f"✓ Indexed {len(self.apps_index)} system applications.")

    def find_app(self, query: str) -> Optional[AppEntry]:
        """
        Find application entry matching query using exact, alias, and fuzzy matching.
        """
        if not query:
            return None

        q_clean = query.lower().strip()

        # Check aliases first
        for alias, mapped_targets in self.aliases.items():
            if q_clean == alias or q_clean in alias or alias in q_clean:
                for target in mapped_targets:
                    # Look for target in apps index
                    for app in self.apps_index:
                        if (target.lower() == app.desktop_id.lower() or 
                            target.lower() == app.name.lower() or 
                            target.lower() in app.exec_cmd.lower()):
                            return app

        # 1. Exact match on desktop ID or Name
        for app in self.apps_index:
            if q_clean == app.desktop_id.lower() or q_clean == app.name.lower():
                return app

        # 2. Substring match on Name or Desktop ID
        for app in self.apps_index:
            if q_clean in app.name.lower() or q_clean in app.desktop_id.lower():
                return app

        # 3. Substring match in Exec command
        for app in self.apps_index:
            if q_clean in app.exec_cmd.lower():
                return app

        # 4. Match in GenericName or Keywords
        for app in self.apps_index:
            if (app.generic_name and q_clean in app.generic_name.lower()) or \
               (app.keywords and q_clean in app.keywords.lower()):
                return app

        # 5. Fuzzy match on names
        app_names = [app.name for app in self.apps_index]
        matches = difflib.get_close_matches(query, app_names, n=1, cutoff=0.5)
        if matches:
            matched_name = matches[0]
            for app in self.apps_index:
                if app.name == matched_name:
                    return app

        return None

    def open_app(self, app_name: str) -> bool:
        """
        Open application dynamically
        """
        app = self.find_app(app_name)

        # 1. Try launching using desktop entry via gtk-launch or gio
        if app:
            desktop_id = app.desktop_id
            print(f"Found app entry: {app.name} ({desktop_id})")

            # Try gtk-launch
            try:
                subprocess.Popen(["gtk-launch", desktop_id],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                print(f"✓ Launched {app.name} via gtk-launch")
                return True
            except Exception:
                pass

            # Try gio launch
            try:
                subprocess.Popen(["gio", "launch", app.desktop_file],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                print(f"✓ Launched {app.name} via gio launch")
                return True
            except Exception:
                pass

            # Try executing cleaned Exec command directly
            try:
                cmd_args = shlex.split(app.exec_cmd)
                subprocess.Popen(cmd_args,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                print(f"✓ Launched {app.name} via command line")
                return True
            except Exception as e:
                print(f"✗ Failed launching {app.exec_cmd}: {e}")

        # Fallback: check if raw command exists in system PATH
        fallback_cmd = app_name.lower().strip().replace(" ", "-")
        try:
            res = subprocess.run(["which", fallback_cmd], capture_output=True, text=True)
            if res.returncode == 0:
                subprocess.Popen([fallback_cmd],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                print(f"✓ Opened {fallback_cmd} from PATH")
                return True
        except Exception:
            pass

        print(f"✗ Could not find or launch application: '{app_name}'")
        return False

    def close_app(self, app_name: str) -> bool:
        """
        Close application by matching running process names, cmdlines, or WM classes
        """
        app = self.find_app(app_name)

        search_targets = [app_name.lower().strip()]
        if app:
            search_targets.append(app.desktop_id.lower())
            search_targets.append(app.name.lower())
            search_targets.append(app.wm_class.lower())
            exec_binary = app.exec_cmd.split()[0].split('/')[-1].lower()
            search_targets.append(exec_binary)

        # Check aliases
        for alias, targets in self.aliases.items():
            if app_name.lower().strip() == alias:
                search_targets.extend(targets)

        pids_killed = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    cmdline_str = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""

                    for target in search_targets:
                        if not target:
                            continue
                        if target in proc_name or target in cmdline_str:
                            pids_killed.append(proc.info['pid'])
                            break

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if not pids_killed:
                print(f"✗ No running process found for '{app_name}'")
                return False

            # Kill processes
            for pid in set(pids_killed):
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Wait briefly and force kill if still running
            gone, alive = psutil.wait_procs([psutil.Process(p) for p in set(pids_killed) if psutil.pid_exists(p)], timeout=2)
            for p in alive:
                try:
                    p.kill()
                except Exception:
                    pass

            print(f"✓ Closed '{app_name}' ({len(pids_killed)} processes stopped)")
            return True

        except Exception as e:
            print(f"✗ Error closing {app_name}: {e}")
            return False

    def close_all_apps(self) -> bool:
        """Close all user applications"""
        print("Closing user applications...")
        closed_count = 0

        current_pid = os.getpid()

        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                pid = proc.info['pid']
                if pid <= 1000 or pid == current_pid:
                    continue

                proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                if any(sys_p in proc_name for sys_p in self.system_processes):
                    continue

                proc.terminate()
                closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        print(f"✓ Closed {closed_count} user application process(es)")
        return True

    def is_running(self, app_name: str) -> bool:
        """Check if application is running"""
        app = self.find_app(app_name)
        search_target = app.name.lower() if app else app_name.lower()

        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""
                if search_target in proc_name or search_target in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return False

