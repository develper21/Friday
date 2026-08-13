"""
Browser Controller
Handles browser tab management
"""

import subprocess
import psutil
from typing import List
from assistance.utils.logger import logger


class BrowserController:
    def __init__(self):
        """Initialize browser controller"""
        self.browsers = {
            "chrome": ["google-chrome", "chrome"],
            "firefox": ["firefox", "mozilla"]
        }
        
    def close_all_tabs(self, browser: str = "all") -> bool:
        """
        Close all browser tabs (by killing browser process)
        
        Args:
            browser: Specific browser or 'all' for all browsers
            
        Returns:
            True if successful
        """
        logger.info(f"Closing all tabs for {browser}...", module="BrowserController")
        closed = False
        
        if browser == "all":
            # Close all browsers
            for browser_name, processes in self.browsers.items():
                if self._close_browser(processes):
                    logger.success(f"Closed {browser_name} tabs", module="BrowserController")
                    closed = True
        elif browser in self.browsers:
            if self._close_browser(self.browsers[browser]):
                logger.success(f"Closed {browser} tabs", module="BrowserController")
                closed = True
        else:
            logger.warning(f"Unknown browser: {browser}", module="BrowserController")
            return False
            
        if not closed:
            logger.warning("No browsers running", module="BrowserController")
            
        return closed
    
    def _close_browser(self, process_names: List[str]) -> bool:
        """
        Close browser by process name
        
        Args:
            process_names: List of process names to match
            
        Returns:
            True if process was found and closed
        """
        closed = False
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""
                    
                    for proc_name_match in process_names:
                        if proc_name_match.lower() in proc_name or proc_name_match.lower() in cmdline:
                            proc.terminate()
                            closed = True
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
            return closed
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}", module="BrowserController")
            return False
    
    def get_running_browsers(self) -> List[str]:
        """
        Get list of currently running browsers
        
        Returns:
            List of browser names
        """
        running = []
        
        try:
            for browser_name, processes in self.browsers.items():
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                        cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""
                        
                        for proc_name_match in processes:
                            if proc_name_match.lower() in proc_name or proc_name_match.lower() in cmdline:
                                running.append(browser_name)
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
        except Exception:
            pass
            
        return list(set(running))
