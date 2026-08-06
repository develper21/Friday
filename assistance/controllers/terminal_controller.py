"""
Terminal Controller for JeanMax
Provides autonomous Linux terminal interaction, command execution, and system updates.
"""

import subprocess
import shutil
import os
import re
from typing import Tuple, Optional


class TerminalController:
    """
    Executes Linux terminal commands and manages system maintenance tasks.
    """
    def __init__(self):
        self.sudo_cmd = self._detect_sudo_method()

    def _detect_sudo_method(self) -> str:
        """Detect graphical or non-interactive sudo command"""
        if shutil.which("pkexec"):
            return "pkexec"
        return "sudo"

    def run_command(self, cmd: str, timeout: int = 120) -> Tuple[bool, str]:
        """
        Execute an arbitrary shell command in bash
        
        Args:
            cmd: Command string to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Tuple of (success: bool, output_summary: str)
        """
        print(f"💻 [Terminal Execution]: {cmd}")
        try:
            process = subprocess.run(
                ["bash", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()
            output = stdout if stdout else stderr

            if process.returncode == 0:
                # Truncate summary for voice feedback if too long
                summary = stdout[:300] if stdout else "Command executed successfully with no output."
                return True, summary
            else:
                summary = stderr[:300] if stderr else f"Command failed with exit code {process.returncode}."
                return False, summary

        except subprocess.TimeoutExpired:
            return False, f"Command execution timed out after {timeout} seconds."
        except Exception as e:
            return False, f"Failed to execute command: {str(e)}"

    def update_system(self) -> Tuple[bool, str]:
        """
        Update and upgrade all Linux packages and system repositories
        """
        print("🔄 Initiating complete Linux system update and upgrade...")
        
        # Check if terminal emulator is available to run interactively with GUI password prompt if needed
        terminal_emulators = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm", "kitty", "alacritty"]
        gui_terminal = None
        for term in terminal_emulators:
            if shutil.which(term):
                gui_terminal = term
                break

        # Sudo update command
        update_cmd = "sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y"

        if gui_terminal:
            # Launch terminal window so user can view progress or enter sudo password
            cmd = f"{gui_terminal} -- bash -c '{update_cmd}; echo \"System update complete! Press Enter to close.\"; read'"
            try:
                subprocess.Popen(cmd, shell=True)
                return True, "Sir, I have opened the terminal to update and upgrade your Linux system packages."
            except Exception:
                pass

        # Fallback to direct subprocess run
        success, out = self.run_command(f"{self.sudo_cmd} apt update && {self.sudo_cmd} apt upgrade -y", timeout=300)
        if success:
            return True, "Sir, your system repositories and packages have been successfully updated."
        else:
            return False, f"Sir, system update encountered an error: {out[:150]}"

    def install_package(self, package_name: str) -> Tuple[bool, str]:
        """
        Install a package via apt or snap
        """
        if not package_name:
            return False, "Sir, please specify which package to install."

        package_name = package_name.lower().strip()
        print(f"📦 Installing package: {package_name}")

        terminal_emulators = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]
        for term in terminal_emulators:
            if shutil.which(term):
                cmd = f"{term} -- bash -c 'sudo apt install -y {package_name} || sudo snap install {package_name}; echo \"Press Enter to exit.\"; read'"
                subprocess.Popen(cmd, shell=True)
                return True, f"Sir, initiating installation of {package_name} in the terminal."

        success, out = self.run_command(f"sudo apt install -y {package_name}", timeout=300)
        if success:
            return True, f"Sir, {package_name} has been successfully installed."
        else:
            return False, f"Sir, failed to install {package_name}."

    def execute_task_by_phrase(self, task_phrase: str) -> Tuple[bool, str]:
        """
        Process natural language terminal task phrases
        """
        phrase_clean = task_phrase.lower().strip()

        if any(kw in phrase_clean for kw in ["update system", "upgrade system", "update linux", "system update", "update packages"]):
            return self.update_system()

        if any(kw in phrase_clean for kw in ["clean system", "clean apt", "autoremove", "free disk space"]):
            return self.run_command("sudo apt autoremove -y && sudo apt autoclean", timeout=120)

        if "disk space" in phrase_clean or "disk usage" in phrase_clean or "df -h" in phrase_clean:
            success, out = self.run_command("df -h / | tail -n 1", timeout=10)
            if success:
                parts = out.split()
                if len(parts) >= 5:
                    return True, f"Sir, disk usage is at {parts[4]} with {parts[3]} free space remaining."
            return success, out

        # Direct shell command parsing if phrase starts with run/execute command
        for prefix in ["run command", "execute command", "terminal command", "run in terminal", "execute"]:
            if phrase_clean.startswith(prefix):
                cmd_to_run = phrase_clean.replace(prefix, "").strip()
                if cmd_to_run:
                    return self.run_command(cmd_to_run)

        # Fallback run as command
        return self.run_command(phrase_clean)
