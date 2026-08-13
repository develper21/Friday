"""
Message Monitor Service
Background service for monitoring new messages from WhatsApp and Instagram
"""

import threading
import time
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime, timedelta

from core.interfaces.messaging_service import (
    IMessageMonitor, IMessagingService, Platform, Message
)
from infrastructure.storage.message_repository import MessageRepository
from assistance.utils.logger import logger


class MessageMonitor(IMessageMonitor):
    """Background message monitoring service"""
    
    def __init__(
        self,
        messaging_services: List[IMessagingService],
        repository: Optional[MessageRepository] = None,
        polling_interval: int = 30,
        enable_alerts: bool = True
    ):
        """
        Initialize message monitor
        
        Args:
            messaging_services: List of messaging services to monitor
            repository: Message repository for storage
            polling_interval: Polling interval in seconds
            enable_alerts: Enable new message alerts
        """
        self.messaging_services = messaging_services
        self.repository = repository or MessageRepository()
        self.polling_interval = polling_interval
        self.enable_alerts = enable_alerts
        
        self._monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        
        self._new_message_callbacks = []
        self._last_check_time = None
        self._last_message_counts = {}
        
        # Statistics
        self._total_messages_checked = 0
        self._new_messages_found = 0
        self._monitor_start_time = None
    
    def start_monitoring(self) -> bool:
        """Start background message monitoring"""
        try:
            if self._monitoring:
                logger.warning("Message monitoring is already running")
                return True
            
            logger.system("Starting message monitoring service...")
            
            self._monitoring = True
            self._stop_event.clear()
            self._monitor_start_time = datetime.now()
            
            # Initialize last message counts
            for service in self.messaging_services:
                platform = service.get_platform()
                self._last_message_counts[platform.value] = service.get_unread_count()
            
            # Start monitoring thread
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="MessageMonitor"
            )
            self._monitor_thread.start()
            
            logger.success(f"Message monitoring started (interval: {self.polling_interval}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error starting message monitoring: {e}")
            self._monitoring = False
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop background message monitoring"""
        try:
            if not self._monitoring:
                logger.warning("Message monitoring is not running")
                return True
            
            logger.system("Stopping message monitoring service...")
            
            self._stop_event.set()
            self._monitoring = False
            
            if self._monitor_thread:
                self._monitor_thread.join(timeout=5)
            
            logger.success("Message monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping message monitoring: {e}")
            return False
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active"""
        return self._monitoring
    
    def register_new_message_callback(self, callback: Callable[[List[Message]], None]):
        """Register callback for new messages"""
        self._new_message_callbacks.append(callback)
        logger.system(f"Registered new message callback (total: {len(self._new_message_callbacks)})")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring status information"""
        uptime = None
        if self._monitor_start_time:
            uptime = (datetime.now() - self._monitor_start_time).total_seconds()
        
        platform_stats = {}
        for service in self.messaging_services:
            platform = service.get_platform()
            platform_stats[platform.value] = {
                'authenticated': service.is_authenticated(),
                'unread_count': service.get_unread_count(),
                'last_count': self._last_message_counts.get(platform.value, 0)
            }
        
        return {
            'monitoring': self._monitoring,
            'polling_interval': self.polling_interval,
            'uptime_seconds': uptime,
            'total_messages_checked': self._total_messages_checked,
            'new_messages_found': self._new_messages_found,
            'callbacks_registered': len(self._new_message_callbacks),
            'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
            'platform_stats': platform_stats
        }
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.system("Message monitor loop started")
        
        while not self._stop_event.is_set():
            try:
                self._check_messages()
                
                # Wait for polling interval or stop event
                self._stop_event.wait(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                # Continue monitoring despite errors
                time.sleep(5)
        
        logger.system("Message monitor loop stopped")
    
    def _check_messages(self):
        """Check for new messages from all services"""
        self._last_check_time = datetime.now()
        
        all_new_messages = []
        
        for service in self.messaging_services:
            try:
                platform = service.get_platform()
                
                # Check if service is authenticated
                if not service.is_authenticated():
                    logger.warning(f"{platform.value} service not authenticated, skipping")
                    continue
                
                # Get current unread count
                current_count = service.get_unread_count()
                last_count = self._last_message_counts.get(platform.value, 0)
                
                # If count increased, fetch new messages
                if current_count > last_count:
                    logger.info(f"New messages detected on {platform.value}: {current_count - last_count}")
                    
                    # Fetch unread messages
                    new_messages = service.get_unread_messages(limit=20)
                    all_new_messages.extend(new_messages)
                    
                    # Update last count
                    self._last_message_counts[platform.value] = current_count
                    self._new_messages_found += len(new_messages)
                
                # Also periodically fetch messages even if count hasn't changed
                # (to catch messages that might have been marked as read elsewhere)
                elif self._total_messages_checked % 10 == 0:  # Every 10th check
                    service.get_unread_messages(limit=10)
                
                self._total_messages_checked += 1
                
            except Exception as e:
                logger.error(f"Error checking messages for {service.get_platform().value}: {e}")
        
        # Trigger callbacks if new messages found
        if all_new_messages and self.enable_alerts:
            self._trigger_callbacks(all_new_messages)
    
    def _trigger_callbacks(self, messages: List[Message]):
        """Trigger all registered callbacks with new messages"""
        for callback in self._new_message_callbacks:
            try:
                callback(messages)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
    
    def force_check(self) -> List[Message]:
        """Force immediate message check (synchronous)"""
        logger.system("Forcing immediate message check...")
        
        all_new_messages = []
        
        for service in self.messaging_services:
            try:
                messages = service.get_unread_messages(limit=20)
                all_new_messages.extend(messages)
                
                # Update last count
                platform = service.get_platform()
                self._last_message_counts[platform.value] = service.get_unread_count()
                
            except Exception as e:
                logger.error(f"Error in force check for {service.get_platform().value}: {e}")
        
        self._total_messages_checked += 1
        logger.system(f"Force check complete: {len(all_new_messages)} messages")
        
        return all_new_messages
    
    def get_unread_summary(self) -> Dict[str, Any]:
        """Get summary of unread messages across all platforms"""
        summary = {
            'total_unread': 0,
            'platforms': {},
            'important_messages': [],
            'urgent_messages': []
        }
        
        for service in self.messaging_services:
            platform = service.get_platform()
            unread_count = service.get_unread_count()
            
            summary['platforms'][platform.value] = unread_count
            summary['total_unread'] += unread_count
            
            # Get unread messages for priority classification
            unread_messages = service.get_unread_messages(limit=50)
            
            for msg in unread_messages:
                if msg.priority.value == 'urgent':
                    summary['urgent_messages'].append(msg.to_dict())
                elif msg.priority.value == 'important':
                    summary['important_messages'].append(msg.to_dict())
        
        return summary
    
    def get_message_activity(self, days: int = 7) -> Dict[str, Any]:
        """Get message activity statistics for specified days"""
        activity = {
            'total_messages': 0,
            'platforms': {},
            'daily_breakdown': {}
        }
        
        for service in self.messaging_services:
            platform = service.get_platform()
            count = service.get_message_count_since(days)
            
            activity['platforms'][platform.value] = count
            activity['total_messages'] += count
        
        return activity
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_monitoring()
            self._new_message_callbacks.clear()
            logger.system("Message monitor cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
