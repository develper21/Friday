"""
Application Manager Controller
Handles dynamic opening, searching, and closing of Linux applications using desktop entry indexing and fuzzy matching.
"""

import os
import re
import shlex
import subprocess
import psutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import difflib
from assistance.utils.logger import logger


class SecurityError(Exception):
    """Security-related error"""
    pass


class PathValidator:
    """Validates file paths to prevent path traversal attacks"""
    
    @staticmethod
    def validate_path(base_dir: str, user_path: str) -> str:
        """Validate path is within base directory"""
        base = Path(base_dir).resolve()
        target = (base / user_path).resolve()
        
        # Ensure target is within base directory
        try:
            target.relative_to(base)
        except ValueError:
            raise SecurityError("Path traversal attempt detected")
        
        # Ensure path exists and is file
        if not target.exists():
            raise FileNotFoundError(f"Path not found: {target}")
        if not target.is_file():
            raise SecurityError(f"Not a file: {target}")
        
        return str(target)


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
    CACHE_FILE = Path.home() / ".cache" / "jeanmax" / "apps_cache.json"
    CACHE_TTL = 86400  # 24 hours
    
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
        self._load_or_build_index()
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is valid"""
        if not self.CACHE_FILE.exists():
            return False
        
        # Check age
        cache_age = datetime.now().timestamp() - self.CACHE_FILE.stat().st_mtime
        return cache_age < self.CACHE_TTL
    
    def _load_from_cache(self):
        """Load app index from cache"""
        try:
            with open(self.CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                self.apps_index = [
                    AppEntry(
                        name=app['name'],
                        exec_cmd=app['exec_cmd'],
                        desktop_file=app['desktop_file'],
                        generic_name=app.get('generic_name', ''),
                        keywords=app.get('keywords', ''),
                        wm_class=app.get('wm_class', '')
                    )
                    for app in cache_data['apps']
                ]
            logger.success("Loaded app index from cache", module="AppManager")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}, rebuilding...", module="AppManager")
            self._build_index()
    
    def _save_to_cache(self):
        """Save app index to cache"""
        try:
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'apps': [
                    {
                        'name': app.name,
                        'exec_cmd': app.exec_cmd,
                        'desktop_file': app.desktop_file,
                        'generic_name': app.generic_name,
                        'keywords': app.keywords,
                        'wm_class': app.wm_class
                    }
                    for app in self.apps_index
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.success("Saved app index to cache", module="AppManager")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}", module="AppManager")
    
    def _load_or_build_index(self):
        """Load from cache or build new index"""
        if self._is_cache_valid():
            self._load_from_cache()
        else:
            self._build_index()
            self._save_to_cache()
    
    def invalidate_cache(self):
        """Force cache rebuild"""
        if self.CACHE_FILE.exists():
            self.CACHE_FILE.unlink()
        self._build_index()
        self._save_to_cache()
        logger.success("Cache invalidated and rebuilt", module="AppManager")

    def _clean_exec_command(self, exec_str: str) -> str:
        """Strip desktop field codes like %f, %F, %u, %U, %k, %i, etc."""
        # Remove field codes
        cleaned = re.sub(r'%[fFuUkKiIcCnNdDsS]', '', exec_str)
        cleaned = cleaned.strip()
        return cleaned

    def _build_index(self):
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

                        # Validate path to prevent traversal attacks
                        try:
                            safe_filepath = PathValidator.validate_path(root, filename)
                        except (SecurityError, FileNotFoundError):
                            continue

                        with open(safe_filepath, 'r', encoding='utf-8', errors='ignore') as f:
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

        logger.success(f"Indexed {len(self.apps_index)} system applications.", module="AppManager")

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
            logger.info(f"Found app entry: {app.name} ({desktop_id})", module="AppManager")

            # Try gtk-launch
            try:
                subprocess.Popen(["gtk-launch", desktop_id],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                logger.success(f"Launched {app.name} via gtk-launch", module="AppManager")
                return True
            except Exception:
                pass

            # Try gio launch
            try:
                subprocess.Popen(["gio", "launch", app.desktop_file],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                logger.success(f"Launched {app.name} via gio launch", module="AppManager")
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
                logger.success(f"Launched {app.name} via command line", module="AppManager")
                return True
            except Exception as e:
                logger.error(f"Failed launching {app.exec_cmd}: {e}", module="AppManager")

        # Fallback: check if raw command exists in system PATH
        fallback_cmd = app_name.lower().strip().replace(" ", "-")
        try:
            res = subprocess.run(["which", fallback_cmd], capture_output=True, text=True)
            if res.returncode == 0:
                subprocess.Popen([fallback_cmd],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                logger.success(f"Opened {fallback_cmd} from PATH", module="AppManager")
                return True
        except Exception:
            pass

        logger.error(f"Could not find or launch application: '{app_name}'", module="AppManager")
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
                logger.warning(f"No running process found for '{app_name}'", module="AppManager")
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

            logger.success(f"Closed '{app_name}' ({len(pids_killed)} processes stopped)", module="AppManager")
            return True

        except Exception as e:
            logger.error(f"Error closing {app_name}: {e}", module="AppManager")
            return False

    def close_all_apps(self) -> bool:
        """Close all user applications"""
        logger.info("Closing user applications...", module="AppManager")
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

        logger.success(f"Closed {closed_count} user application process(es)", module="AppManager")
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

