"""
Terminal Controller Service Implementation
Implements ITerminalController interface using existing TerminalController
"""

from typing import Tuple
from core.interfaces.controller_service import ITerminalController
from assistance.controllers.terminal_controller import TerminalController


class TerminalControllerService(ITerminalController):
    """Terminal controller service implementation"""
    
    def __init__(self):
        self.terminal_controller = TerminalController()
    
    def execute_task_by_phrase(self, phrase: str) -> Tuple[bool, str]:
        """Execute terminal command by natural language phrase"""
        return self.terminal_controller.execute_task_by_phrase(phrase)
    
    def execute_command(self, command: str) -> Tuple[bool, str]:
        """Execute raw terminal command"""
        return self.terminal_controller.execute_command(command)
