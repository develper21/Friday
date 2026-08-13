"""
Instagram Service
Implements Instagram messaging using instagrapi
"""

import time
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

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


class InstagramService(IMessagingService):
    """Instagram service implementation using instagrapi"""
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_file: Optional[str] = None,
        repository: Optional[MessageRepository] = None
    ):
        """
        Initialize Instagram service
        
        Args:
            username: Instagram username
            password: Instagram password
            session_file: Path to session file for persistent login
            repository: Message repository for storage
        """
        self.platform = Platform.INSTAGRAM
        self.username = username
        self.password = password
        self.session_file = session_file or "data/instagram_session.json"
        self.repository = repository or MessageRepository()
        self._instagrapi_client = None
        self._authenticated = False
        self._auth_lock = threading.Lock()
        self._last_message_fetch = None
        self._cached_messages = []
        
        # Secret manager for secure password storage
        self._secret_manager = None
        if SECRETS_AVAILABLE:
            try:
                self._secret_manager = SecretManager()
            except Exception as e:
                logger.warning(f"Could not initialize SecretManager: {e}")
        
        # Priority keywords for message classification
        self._urgent_keywords = ['urgent', 'emergency', 'asap', 'immediately', 'help']
        self._important_keywords = ['important', 'priority', 'meeting', 'deadline', 'work']
        
        # Ensure session directory exists
        Path(self.session_file).parent.mkdir(parents=True, exist_ok=True)
    
    def get_platform(self) -> Platform:
        """Get the platform type"""
        return self.platform
    
    def _get_instagrapi_client(self):
        """Get or create instagrapi client"""
        if self._instagrapi_client is None:
            try:
                from instagrapi import Client
                self._instagrapi_client = Client()
                logger.system("Instagrapi client created")
            except ImportError:
                logger.error("instagrapi not installed. Install with: pip install instagrapi")
                raise
            except Exception as e:
                logger.error(f"Error creating instagrapi client: {e}")
                raise
        return self._instagrapi_client
    
    def is_authenticated(self) -> bool:
        """Check if service is authenticated"""
        return self._authenticated
    
    def authenticate(self) -> bool:
        """Authenticate with Instagram"""
        try:
            with self._auth_lock:
                if self._authenticated:
                    return True
                
                logger.system("Authenticating with Instagram...")
                client = self._get_instagrapi_client()
                
                # Try to load session from file
                session_path = Path(self.session_file)
                if session_path.exists():
                    try:
                        client.load_settings(str(session_path))
                        self._authenticated = True
                        logger.success("Instagram authentication successful (session loaded)")
                        return True
                    except Exception as e:
                        logger.warning(f"Session load failed: {e}, trying fresh login")
                
                # Fresh login
                password = self.password
                
                # Try to get password from secure storage if not provided
                if not password and self._secret_manager:
                    password = self._secret_manager.get_secret('instagram_password')
                    if password:
                        logger.info("Retrieved Instagram password from secure storage")
                
                if self.username and password:
                    client.login(self.username, password)
                    client.dump_settings(str(session_file))
                    # Set restrictive permissions on session file
                    session_path.chmod(0o600)
                    self._authenticated = True
                    logger.success("Instagram authentication successful (fresh login)")
                    return True
                else:
                    logger.error("Instagram username and password required for authentication")
                    return False
                    
        except Exception as e:
            logger.error(f"Instagram authentication failed: {e}")
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
    
    def _parse_contact_name(self, user_id: str, username: Optional[str] = None) -> str:
        """Parse contact name from user ID or username"""
        # Try to find contact in repository
        contacts = self.repository.search_contact(user_id, self.platform)
        if contacts:
            return contacts[0].name
        
        # Use username if available
        if username:
            return f"@{username}"
        
        return user_id
    
    def get_unread_messages(self, limit: int = 20) -> List[Message]:
        """Get unread messages from Instagram"""
        try:
            if not self.authenticate():
                logger.error("Cannot fetch messages: not authenticated")
                return []
            
            logger.system("Fetching unread Instagram messages...")
            
            client = self._get_instagrapi_client()
            
            # Get direct threads (inbox)
            threads = client.direct_threads(amount=limit)
            
            messages = []
            for thread in threads:
                # Get messages from thread
                thread_messages = client.direct_messages(thread.id, amount=10)
                
                for msg in thread_messages:
                    # Check if message is unread
                    if not msg.seen and msg.user_id != client.user_id:
                        # Get sender info
                        sender_id = str(msg.user_id)
                        sender_name = None
                        
                        # Try to get user info from thread users
                        for user in thread.users:
                            if str(user.pk) == sender_id:
                                sender_name = user.full_name or user.username
                                break
                        
                        message = Message(
                            id=str(msg.id),
                            platform=self.platform,
                            sender=sender_id,
                            sender_name=sender_name,
                            text=msg.text or '',
                            timestamp=msg.timestamp,
                            read=False,
                            priority=self._classify_priority(msg.text or ''),
                            metadata={
                                'thread_id': str(thread.id),
                                'item_type': msg.item_type,
                                'media': bool(msg.media)
                            }
                        )
                        
                        # Save to repository
                        self.repository.save_message(message)
                        messages.append(message)
            
            # Update cache
            self._cached_messages = messages
            self._last_message_fetch = datetime.now()
            
            logger.system(f"Fetched {len(messages)} unread Instagram messages")
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
        """Send message to recipient via Instagram"""
        try:
            if not self.authenticate():
                logger.error("Cannot send message: not authenticated")
                return False
            
            logger.system(f"Sending Instagram message to {recipient}...")
            
            client = self._get_instagrapi_client()
            
            # Check if recipient is username or user ID
            if recipient.startswith('@'):
                username = recipient[1:]
                # Get user ID from username
                user_info = client.user_info_by_username(username)
                user_ids = [user_info.pk]
            else:
                # Assume it's a user ID
                user_ids = [int(recipient)]
            
            # Send message
            client.direct_send(text, user_ids=user_ids)
            
            logger.success(f"Instagram message sent to {recipient}")
            
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
            logger.error(f"Error sending Instagram message: {e}")
            return False
    
    def mark_as_read(self, message_ids: List[str]) -> bool:
        """Mark messages as read"""
        try:
            # Mark in repository
            repo_success = self.repository.mark_messages_as_read(message_ids)
            
            # Also mark as seen in Instagram
            if self._authenticated and self._instagrapi_client:
                try:
                    # Get unique thread IDs from messages
                    messages = [self.repository.get_message(mid) for mid in message_ids]
                    thread_ids = set()
                    for msg in messages:
                        if msg and msg.metadata.get('thread_id'):
                            thread_ids.add(msg.metadata['thread_id'])
                    
                    # Mark threads as seen
                    for thread_id in thread_ids:
                        self._instagrapi_client.direct_thread_mark_seen(thread_id)
                    
                    logger.system(f"Marked {len(message_ids)} messages as read in Instagram")
                except Exception as e:
                    logger.warning(f"Could not mark as seen in Instagram: {e}")
            
            return repo_success
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            return False
    
    def get_contacts(self) -> List[Contact]:
        """Get all Instagram contacts"""
        try:
            if not self.authenticate():
                logger.error("Cannot fetch contacts: not authenticated")
                return []
            
            client = self._get_instagrapi_client()
            
            # Get direct threads to extract contacts
            threads = client.direct_threads(amount=50)
            
            contacts = []
            seen_users = set()
            
            for thread in threads:
                for user in thread.users:
                    user_id = str(user.pk)
                    
                    if user_id not in seen_users:
                        contact = Contact(
                            id=user_id,
                            platform=self.platform,
                            name=user.full_name or user.username,
                            username=user.username,
                            is_important=False,
                            metadata={
                                'profile_pic': user.profile_pic_url,
                                'is_private': user.is_private,
                                'is_verified': user.is_verified
                            }
                        )
                        
                        self.repository.save_contact(contact)
                        contacts.append(contact)
                        seen_users.add(user_id)
            
            logger.system(f"Fetched {len(contacts)} Instagram contacts")
            return contacts
            
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []
    
    def search_contact(self, query: str) -> Optional[Contact]:
        """Search contact by username or name"""
        try:
            # First search in repository
            contacts = self.repository.search_contact(query, self.platform)
            if contacts:
                return contacts[0]
            
            # If not found in repository and authenticated, search Instagram
            if self._authenticated and self._instagrapi_client:
                try:
                    # Clean query (remove @ if present)
                    clean_query = query.lstrip('@')
                    
                    user_info = self._instagrapi_client.user_info_by_username(clean_query)
                    
                    contact = Contact(
                        id=str(user_info.pk),
                        platform=self.platform,
                        name=user_info.full_name or user_info.username,
                        username=user_info.username,
                        is_important=False,
                        metadata={
                            'profile_pic': user_info.profile_pic_url,
                            'is_private': user_info.is_private,
                            'is_verified': user_info.is_verified
                        }
                    )
                    
                    self.repository.save_contact(contact)
                    return contact
                    
                except Exception as e:
                    logger.warning(f"Could not find user on Instagram: {e}")
            
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
    
    def sync_threads(self) -> bool:
        """Sync all Instagram threads to repository"""
        try:
            if not self.authenticate():
                logger.error("Cannot sync threads: not authenticated")
                return False
            
            logger.system("Syncing Instagram threads...")
            
            client = self._get_instagrapi_client()
            threads = client.direct_threads(amount=50)
            
            for thread in threads:
                # Get messages from thread
                thread_messages = client.direct_messages(thread.id, amount=20)
                
                for msg in thread_messages:
                    sender_id = str(msg.user_id)
                    sender_name = None
                    
                    # Get sender info
                    for user in thread.users:
                        if str(user.pk) == sender_id:
                            sender_name = user.full_name or user.username
                            break
                    
                    message = Message(
                        id=str(msg.id),
                        platform=self.platform,
                        sender=sender_id,
                        sender_name=sender_name,
                        text=msg.text or '',
                        timestamp=msg.timestamp,
                        read=msg.seen,
                        priority=self._classify_priority(msg.text or ''),
                        metadata={
                            'thread_id': str(thread.id),
                            'item_type': msg.item_type,
                            'media': bool(msg.media)
                        }
                    )
                    
                    self.repository.save_message(message)
            
            logger.success(f"Synced {len(threads)} Instagram threads")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing threads: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self._instagrapi_client:
                # Save session before cleanup
                try:
                    self._instagrapi_client.dump_settings(self.session_file)
                    # Ensure restrictive permissions
                    Path(self.session_file).chmod(0o600)
                except Exception as e:
                    logger.warning(f"Could not save session: {e}")
            
            logger.system("Instagram service cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def store_credentials_securely(self, username: str, password: str) -> bool:
        """
        Store Instagram credentials securely using SecretManager
        
        Args:
            username: Instagram username
            password: Instagram password
            
        Returns:
            True if stored successfully
        """
        if not self._secret_manager:
            logger.warning("SecretManager not available, cannot store credentials securely")
            return False
        
        try:
            # Store username and password
            self._secret_manager.store_secret('instagram_username', username)
            self._secret_manager.store_secret('instagram_password', password)
            
            self.username = username
            self.password = None  # Clear from memory
            
            logger.success("Instagram credentials stored securely")
            return True
        except Exception as e:
            logger.error(f"Failed to store credentials securely: {e}")
            return False
