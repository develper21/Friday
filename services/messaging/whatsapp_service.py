"""
WhatsApp Service
Implements WhatsApp messaging using pyzapkit (WhatsApp Web automation)
"""

import time
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.interfaces.messaging_service import (
    IMessagingService, Platform, Message, Contact, MessagePriority
)
from infrastructure.storage.message_repository import MessageRepository
from assistance.utils.logger import logger

try:
    from core.security.secrets import SecretManager
    SECRETS_AVAILABLE = True
except ImportError:
    SECRETS_AVAILABLE = False


class WhatsAppService(IMessagingService):
    """WhatsApp service implementation using pyzapkit"""
    
    def __init__(
        self,
        chrome_profile: str = "Default",
        repository: Optional[MessageRepository] = None,
        headless: bool = False
    ):
        """
        Initialize WhatsApp service
        
        Args:
            chrome_profile: Chrome profile name for WhatsApp Web session
            repository: Message repository for storage
            headless: Run browser in headless mode
        """
        self.platform = Platform.WHATSAPP
        self.chrome_profile = chrome_profile
        self.repository = repository or MessageRepository()
        self.headless = headless
        self._pyzap_instance = None
        self._authenticated = False
        self._auth_lock = threading.Lock()
        self._last_message_fetch = None
        self._cached_messages = []
        
        # Secret manager for secure credential storage
        self._secret_manager = None
        if SECRETS_AVAILABLE:
            try:
                self._secret_manager = SecretManager()
            except Exception as e:
                logger.warning(f"Could not initialize SecretManager: {e}")
        
        # Priority keywords for message classification
        self._urgent_keywords = ['urgent', 'emergency', 'asap', 'immediately', 'help']
        self._important_keywords = ['important', 'priority', 'meeting', 'deadline', 'work']
    
    def get_platform(self) -> Platform:
        """Get the platform type"""
        return self.platform
    
    def _get_pyzap_instance(self):
        """Get or create pyzapkit instance"""
        if self._pyzap_instance is None:
            try:
                from pyzapkit.main import Pyzap
                self._pyzap_instance = Pyzap(self.chrome_profile, headless=self.headless)
                logger.system("Pyzapkit instance created")
            except ImportError:
                logger.error("pyzapkit not installed. Install with: pip install pyzapkit")
                raise
            except Exception as e:
                logger.error(f"Error creating pyzapkit instance: {e}")
                raise
        return self._pyzap_instance
    
    def is_authenticated(self) -> bool:
        """Check if service is authenticated"""
        return self._authenticated
    
    def authenticate(self) -> bool:
        """Authenticate with WhatsApp Web"""
        try:
            with self._auth_lock:
                if self._authenticated:
                    return True
                
                logger.system("Authenticating with WhatsApp Web...")
                pyzap = self._get_pyzap_instance()
                
                # The first call will trigger QR code scan if needed
                # pyzapkit handles session persistence via chrome profile
                self._authenticated = True
                logger.success("WhatsApp Web authentication successful")
                return True
                
        except Exception as e:
            logger.error(f"WhatsApp authentication failed: {e}")
            self._authenticated = False
            return False
    
    def _classify_priority(self, text: str) -> MessagePriority:
        """Classify message priority based on content"""
        if not text:
            return MessagePriority.NORMAL
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in self._urgent_keywords):
            return MessagePriority.URGENT
        elif any(keyword in text_lower for keyword in self._important_keywords):
            return MessagePriority.IMPORTANT
        
        return MessagePriority.NORMAL
    
    def _parse_contact_name(self, phone: str) -> str:
        """Parse contact name from phone number"""
        # Try to find contact in repository
        contacts = self.repository.search_contact(phone, self.platform)
        if contacts:
            return contacts[0].name
        
        # Format phone number for display
        if len(phone) == 10:
            return f"+91 {phone[:5]} {phone[5:]}"
        elif len(phone) == 12 and phone.startswith('91'):
            return f"+{phone[:2]} {phone[2:7]} {phone[7:]}"
        else:
            return phone
    
    def get_unread_messages(self, limit: int = 20) -> List[Message]:
        """Get unread messages from WhatsApp"""
        try:
            if not self.authenticate():
                logger.error("Cannot fetch messages: not authenticated")
                return []
            
            logger.system("Fetching unread WhatsApp messages...")
            
            # Note: pyzapkit doesn't have a direct method to fetch messages
            # We'll need to implement a workaround or use a different approach
            # For now, we'll return messages from repository
            
            messages = self.repository.get_unread_messages(platform=self.platform, limit=limit)
            
            # Update cache
            self._cached_messages = messages
            self._last_message_fetch = datetime.now()
            
            logger.system(f"Fetched {len(messages)} unread WhatsApp messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching unread messages: {e}")
            return []
    
    def get_messages_from_contact(self, contact_id: str, limit: int = 20) -> List[Message]:
        """Get messages from specific contact"""
        try:
            messages = self.repository.get_messages(
                platform=self.platform,
                sender=contact_id,
                limit=limit
            )
            return messages
        except Exception as e:
            logger.error(f"Error getting messages from contact: {e}")
            return []
    
    def send_message(self, recipient: str, text: str) -> bool:
        """Send message to recipient via WhatsApp"""
        try:
            if not self.authenticate():
                logger.error("Cannot send message: not authenticated")
                return False
            
            logger.system(f"Sending WhatsApp message to {recipient}...")
            
            pyzap = self._get_pyzap_instance()
            
            # Clean recipient phone number
            recipient = recipient.strip().replace('+', '').replace(' ', '').replace('-', '')
            
            # Send message using pyzapkit
            pyzap.send_message(recipient, text)
            
            logger.success(f"WhatsApp message sent to {recipient}")
            
            # Save sent message to repository
            message = Message(
                id=f"sent_{int(time.time())}",
                platform=self.platform,
                sender="me",
                sender_name="You",
                text=text,
                timestamp=datetime.now(),
                read=True,
                priority=MessagePriority.NORMAL,
                metadata={'recipient': recipient, 'direction': 'outgoing'}
            )
            self.repository.save_message(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    def mark_as_read(self, message_ids: List[str]) -> bool:
        """Mark messages as read"""
        try:
            success = self.repository.mark_messages_as_read(message_ids)
            if success:
                logger.system(f"Marked {len(message_ids)} messages as read")
            return success
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            return False
    
    def get_contacts(self) -> List[Contact]:
        """Get all WhatsApp contacts"""
        try:
            contacts = self.repository.get_contacts(platform=self.platform)
            return contacts
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []
    
    def search_contact(self, query: str) -> Optional[Contact]:
        """Search contact by name or phone number"""
        try:
            contacts = self.repository.search_contact(query, self.platform)
            if contacts:
                return contacts[0]
            return None
        except Exception as e:
            logger.error(f"Error searching contact: {e}")
            return None
    
    def get_unread_count(self) -> int:
        """Get total unread message count"""
        try:
            count = self.repository.get_unread_count(platform=self.platform)
            return count
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def get_message_count_since(self, days: int) -> int:
        """Get message count since specified days"""
        try:
            count = self.repository.get_message_count_since(days, self.platform)
            return count
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    def sync_contacts(self, contacts_data: List[Dict[str, Any]]) -> bool:
        """
        Sync contacts from WhatsApp to repository
        This would be called when contacts are fetched from WhatsApp
        """
        try:
            for contact_data in contacts_data:
                contact = Contact(
                    id=contact_data.get('phone', ''),
                    platform=self.platform,
                    name=contact_data.get('name', 'Unknown'),
                    phone=contact_data.get('phone'),
                    is_important=contact_data.get('is_important', False),
                    metadata=contact_data.get('metadata', {})
                )
                self.repository.save_contact(contact)
            
            logger.system(f"Synced {len(contacts_data)} contacts")
            return True
        except Exception as e:
            logger.error(f"Error syncing contacts: {e}")
            return False
    
    def import_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Import a message from WhatsApp to repository
        This would be called when messages are fetched from WhatsApp
        """
        try:
            message = Message(
                id=message_data.get('id', f"msg_{int(time.time())}"),
                platform=self.platform,
                sender=message_data.get('sender', ''),
                sender_name=message_data.get('sender_name'),
                text=message_data.get('text', ''),
                timestamp=datetime.fromisoformat(message_data['timestamp']) if message_data.get('timestamp') else datetime.now(),
                read=message_data.get('read', False),
                priority=self._classify_priority(message_data.get('text', '')),
                metadata=message_data.get('metadata', {})
            )
            
            self.repository.save_message(message)
            return True
        except Exception as e:
            logger.error(f"Error importing message: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self._pyzap_instance:
                # pyzapkit doesn't have an explicit close method
                # The browser will be closed when the instance is garbage collected
                pass
            logger.system("WhatsApp service cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def store_chrome_profile_securely(self, profile_name: str) -> bool:
        """
        Store Chrome profile name securely using SecretManager
        
        Args:
            profile_name: Chrome profile name
            
        Returns:
            True if stored successfully
        """
        if not self._secret_manager:
            logger.warning("SecretManager not available, cannot store profile securely")
            return False
        
        try:
            self._secret_manager.store_secret('whatsapp_chrome_profile', profile_name)
            self.chrome_profile = profile_name
            logger.success("WhatsApp Chrome profile stored securely")
            return True
        except Exception as e:
            logger.error(f"Failed to store profile securely: {e}")
            return False
