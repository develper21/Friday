"""
Messaging Service Interface
Defines the contract for WhatsApp and Instagram messaging services
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Platform(Enum):
    """Messaging platforms"""
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"


class MessagePriority(Enum):
    """Message priority levels"""
    NORMAL = "normal"
    IMPORTANT = "important"
    URGENT = "urgent"


class Message:
    """Message data model"""
    def __init__(
        self,
        id: str,
        platform: Platform,
        sender: str,
        sender_name: Optional[str] = None,
        text: str = "",
        timestamp: Optional[datetime] = None,
        read: bool = False,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.platform = platform
        self.sender = sender
        self.sender_name = sender_name or sender
        self.text = text
        self.timestamp = timestamp or datetime.now()
        self.read = read
        self.priority = priority
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'platform': self.platform.value,
            'sender': self.sender,
            'sender_name': self.sender_name,
            'text': self.text,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'read': self.read,
            'priority': self.priority.value,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            id=data['id'],
            platform=Platform(data['platform']),
            sender=data['sender'],
            sender_name=data.get('sender_name'),
            text=data.get('text', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            read=data.get('read', False),
            priority=MessagePriority(data.get('priority', 'normal')),
            metadata=data.get('metadata', {})
        )


class Contact:
    """Contact data model"""
    def __init__(
        self,
        id: str,
        platform: Platform,
        name: str,
        phone: Optional[str] = None,
        username: Optional[str] = None,
        is_important: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.platform = platform
        self.name = name
        self.phone = phone
        self.username = username
        self.is_important = is_important
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary"""
        return {
            'id': self.id,
            'platform': self.platform.value,
            'name': self.name,
            'phone': self.phone,
            'username': self.username,
            'is_important': self.is_important,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contact':
        """Create contact from dictionary"""
        return cls(
            id=data['id'],
            platform=Platform(data['platform']),
            name=data['name'],
            phone=data.get('phone'),
            username=data.get('username'),
            is_important=data.get('is_important', False),
            metadata=data.get('metadata', {})
        )


class IMessagingService(ABC):
    """Interface for messaging services (WhatsApp/Instagram)"""
    
    @abstractmethod
    def get_platform(self) -> Platform:
        """Get the platform type"""
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if service is authenticated"""
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass
    
    @abstractmethod
    def get_unread_messages(self, limit: int = 20) -> List[Message]:
        """Get unread messages"""
        pass
    
    @abstractmethod
    def get_messages_from_contact(self, contact_id: str, limit: int = 20) -> List[Message]:
        """Get messages from specific contact"""
        pass
    
    @abstractmethod
    def send_message(self, recipient: str, text: str) -> bool:
        """Send message to recipient"""
        pass
    
    @abstractmethod
    def mark_as_read(self, message_ids: List[str]) -> bool:
        """Mark messages as read"""
        pass
    
    @abstractmethod
    def get_contacts(self) -> List[Contact]:
        """Get all contacts"""
        pass
    
    @abstractmethod
    def search_contact(self, query: str) -> Optional[Contact]:
        """Search contact by name or phone/username"""
        pass
    
    @abstractmethod
    def get_unread_count(self) -> int:
        """Get total unread message count"""
        pass
    
    @abstractmethod
    def get_message_count_since(self, days: int) -> int:
        """Get message count since specified days"""
        pass


class IMessageMonitor(ABC):
    """Interface for message monitoring service"""
    
    @abstractmethod
    def start_monitoring(self) -> bool:
        """Start background message monitoring"""
        pass
    
    @abstractmethod
    def stop_monitoring(self) -> bool:
        """Stop background message monitoring"""
        pass
    
    @abstractmethod
    def is_monitoring(self) -> bool:
        """Check if monitoring is active"""
        pass
    
    @abstractmethod
    def register_new_message_callback(self, callback):
        """Register callback for new messages"""
        pass
    
    @abstractmethod
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring status information"""
        pass
