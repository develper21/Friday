"""
Terminal Controller for JeanMax
Provides autonomous Linux terminal interaction, command execution, and system updates.
"""

import subprocess
import shutil
import os
import re
import shlex
from typing import Tuple, Optional, List
from assistance.utils.logger import logger
from assistance.utils.errors import ValidationError


class SecurityError(Exception):
    """Security-related error"""
    pass


class TerminalController:
    """
    Executes Linux terminal commands and manages system maintenance tasks.
    """
    # Whitelist of allowed commands
    ALLOWED_COMMANDS = {
        'ls', 'pwd', 'cd', 'cat', 'grep', 'find',
        'df', 'du', 'free', 'top', 'htop',
        'ps', 'kill', 'systemctl', 'apt', 'snap',
        'echo', 'date', 'whoami', 'hostname', 'uname',
        'which', 'whereis', 'type', 'file', 'head', 'tail',
        'wc', 'sort', 'uniq', 'cut', 'tr', 'sed',
        'mkdir', 'rmdir', 'touch', 'cp', 'mv', 'ln',
        'chmod', 'chown', 'tar', 'zip', 'unzip',
        'ping', 'curl', 'wget', 'ssh', 'scp',
        'git', 'python', 'python3', 'pip', 'pip3',
        'npm', 'node', 'yarn', 'docker', 'docker-compose',
        'sudo', 'pkexec'  # Privilege escalation commands (allowed with validation)
    }
    
    # Blacklist of dangerous patterns
    DANGEROUS_PATTERNS = [
        r';', r'&&', r'\|\|', r'\|',  # Command chaining (basic)
        r'\$.*\(', r'`', r'\$\{',     # Command substitution
        r'>\s*/dev/sd',                 # Disk destruction
        r'rm\s+-rf\s+/',                # Dangerous commands
        r':\(\)\{:\|:&\};:',            # Fork bomb
        r'chmod\s+777',                 # Permission changes
        r'su',                          # su command (but allow sudo with validation)
        r'mkfs', r'format',             # Filesystem operations
        r'dd\s+if=',                    # Disk operations
    ]
    
    def __init__(self):
        self.sudo_cmd = self._detect_sudo_method()
        self._allow_command_chaining = False  # Security: disable command chaining by default

    def _detect_sudo_method(self) -> str:
        """Detect graphical or non-interactive sudo command"""
        if shutil.which("pkexec"):
            return "pkexec"
        return "sudo"
    
    def _validate_command(self, cmd: str) -> List[str]:
        """Validate and parse command safely"""
        cmd = cmd.strip()
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, cmd):
                raise SecurityError(f"Dangerous pattern detected: {pattern}")
        
        # Parse command safely
        try:
            args = shlex.split(cmd)
        except ValueError as e:
            raise SecurityError(f"Invalid command syntax: {e}")
        
        # Check if command is allowed
        if not args:
            raise SecurityError("Empty command")
        
        if args[0] not in self.ALLOWED_COMMANDS:
            raise SecurityError(f"Command not allowed: {args[0]}")
        
        # Validate arguments
        for arg in args[1:]:
            if not self._is_safe_argument(arg):
                raise SecurityError(f"Unsafe argument: {arg}")
        
        return args
    
    def _is_safe_argument(self, arg: str) -> bool:
        """Check if argument is safe"""
        # Allow alphanumeric, hyphens, underscores, dots, slashes, @, :
        return bool(re.match(r'^[\w\-./@:]+$', arg))

    def run_command(self, cmd: str, timeout: int = 120) -> Tuple[bool, str]:
        """
        Execute a validated shell command
        
        Args:
            cmd: Command string to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Tuple of (success: bool, output_summary: str)
        """
        # Validate input
        if not cmd or not cmd.strip():
            raise ValueError("Command cannot be empty")
        
        args = self._validate_command(cmd)
        
        logger.command(f"Terminal Execution: {' '.join(args)}", module="TerminalController")
        try:
            # Execute without shell for security
            process = subprocess.run(
                args,  # Use parsed args, not shell
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
        except SecurityError as e:
            return False, f"Security error: {(str(e))}"
        except Exception as e:
            return False, f"Failed to execute command: {str(e)}"

    def update_system(self) -> Tuple[bool, str]:
        """
        Update and upgrade all Linux packages and system repositories
        """
        logger.info("Initiating complete Linux system update and upgrade...", module="TerminalController")
        
        # Check if terminal emulator is available to run interactively with GUI password prompt if needed
        terminal_emulators = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm", "kitty", "alacritty"]
        gui_terminal = None
        for term in terminal_emulators:
            if shutil.which(term):
                gui_terminal = term
                break

        if gui_terminal:
            # Launch terminal window safely using argument list
            try:
                cmd_args = [
                    gui_terminal,
                    "--",
                    "bash",
                    "-c",
                    "sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y; echo 'System update complete! Press Enter to close.'; read"
                ]
                subprocess.Popen(cmd_args, start_new_session=True)
                return True, "Sir, I have opened the terminal to update and upgrade your Linux system packages."
            except (subprocess.SubprocessError, OSError) as e:
                logger.error(f"Failed to launch terminal: {e}", module="TerminalController")

        # Fallback to direct subprocess run (without command chaining for security)
        try:
            success1, out1 = self.run_command(f"{self.sudo_cmd} apt update", timeout=120)
            success2, out2 = self.run_command(f"{self.sudo_cmd} apt upgrade -y", timeout=300)
            success3, out3 = self.run_command(f"{self.sudo_cmd} apt autoremove -y", timeout=120)
            
            if success1 and success2 and success3:
                return True, "Sir, your system repositories and packages have been successfully updated."
            else:
                errors = []
                if not success1: errors.append(f"update: {out1[:50]}")
                if not success2: errors.append(f"upgrade: {out2[:50]}")
                if not success3: errors.append(f"autoremove: {out3[:50]}")
                return False, f"Sir, system update encountered errors: {', '.join(errors)}"
        except Exception as e:
            return False, f"Sir, system update encountered an error: {str(e)}"

    def install_package(self, package_name: str) -> Tuple[bool, str]:
        """
        Install a package via apt or snap
        """
        if not package_name:
            return False, "Sir, please specify which package to install."

        package_name = package_name.lower().strip()
        logger.command(f"Installing package: {package_name}", module="TerminalController")

        # Validate package name for security
        if not self._is_safe_argument(package_name):
            return False, f"Sir, invalid package name: {package_name}"

        terminal_emulators = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]
        for term in terminal_emulators:
            if shutil.which(term):
                # Launch terminal safely using argument list
                try:
                    cmd_args = [
                        term,
                        "--",
                        "bash",
                        "-c",
                        f"sudo apt install -y {package_name} || sudo snap install {package_name}; echo 'Press Enter to exit.'; read"
                    ]
                    subprocess.Popen(cmd_args, start_new_session=True)
                    return True, f"Sir, initiating installation of {package_name} in the terminal."
                except (subprocess.SubprocessError, OSError) as e:
                    logger.error(f"Failed to launch terminal: {e}", module="TerminalController")
                    continue

        # Fallback to direct command execution
        success, out = self.run_command(f"{self.sudo_cmd} apt install -y {package_name}", timeout=300)
        if success:
            return True, f"Sir, {package_name} has been successfully installed."
        else:
            # Try snap as fallback
            success_snap, out_snap = self.run_command(f"{self.sudo_cmd} snap install {package_name}", timeout=300)
            if success_snap:
                return True, f"Sir, {package_name} has been successfully installed via snap."
            else:
                return False, f"Sir, failed to install {package_name} via apt or snap."

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
