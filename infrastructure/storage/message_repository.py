"""
Message Repository
Handles persistent storage for messages and contacts using SQLite
"""

import sqlite3
import json
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from core.interfaces.messaging_service import Message, Contact, Platform, MessagePriority
from core.interfaces.repository import IRepository
from assistance.utils.logger import logger


class MessageRepository(IRepository):
    """SQLite repository for message and contact storage"""
    
    def __init__(self, db_path: str = "data/messages.db"):
        """
        Initialize message repository
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local_lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        with self._local_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    sender_name TEXT,
                    text TEXT,
                    timestamp TEXT NOT NULL,
                    read BOOLEAN DEFAULT 0,
                    priority TEXT DEFAULT 'normal',
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Contacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    username TEXT,
                    is_important BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_platform 
                ON messages(platform)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_sender 
                ON messages(sender)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_read 
                ON messages(read)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_contacts_platform 
                ON contacts(platform)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_contacts_name 
                ON contacts(name)
            """)
            
            conn.commit()
            conn.close()
            
            logger.system(f"Message repository initialized at {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Message operations
    
    def save_message(self, message: Message) -> bool:
        """Save or update a message"""
        try:
            with self._local_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO messages 
                    (id, platform, sender, sender_name, text, timestamp, read, priority, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message.id,
                    message.platform.value,
                    message.sender,
                    message.sender_name,
                    message.text,
                    message.timestamp.isoformat() if message.timestamp else None,
                    message.read,
                    message.priority.value,
                    json.dumps(message.metadata)
                ))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_message(row)
            return None
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            return None
    
    def get_messages(
        self,
        platform: Optional[Platform] = None,
        sender: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """Get messages with optional filters"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM messages WHERE 1=1"
            params = []
            
            if platform:
                query += " AND platform = ?"
                params.append(platform.value)
            
            if sender:
                query += " AND sender = ?"
                params.append(sender)
            
            if unread_only:
                query += " AND read = 0"
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_message(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def get_unread_messages(self, platform: Optional[Platform] = None, limit: int = 20) -> List[Message]:
        """Get unread messages"""
        return self.get_messages(platform=platform, unread_only=True, limit=limit)
    
    def mark_messages_as_read(self, message_ids: List[str]) -> bool:
        """Mark messages as read"""
        try:
            with self._local_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE messages SET read = 1 WHERE id IN ({})".format(
                        ','.join(['?' for _ in message_ids])
                    ),
                    message_ids
                )
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            return False
    
    def mark_all_as_read(self, platform: Optional[Platform] = None) -> bool:
        """Mark all messages as read"""
        try:
            with self._local_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                if platform:
                    cursor.execute("UPDATE messages SET read = 1 WHERE platform = ?", (platform.value,))
                else:
                    cursor.execute("UPDATE messages SET read = 1")
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Error marking all messages as read: {e}")
            return False
    
    def get_message_count_since(self, days: int, platform: Optional[Platform] = None) -> int:
        """Get message count since specified days"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            if platform:
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE timestamp >= ? AND platform = ?",
                    (since_date, platform.value)
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE timestamp >= ?",
                    (since_date,)
                )
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    def get_unread_count(self, platform: Optional[Platform] = None) -> int:
        """Get unread message count"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if platform:
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE read = 0 AND platform = ?",
                    (platform.value,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM messages WHERE read = 0")
            
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def delete_old_messages(self, days: int = 30) -> bool:
        """Delete messages older than specified days"""
        try:
            with self._local_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                cursor.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff_date,))
                
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                logger.system(f"Deleted {deleted} old messages")
                return True
        except Exception as e:
            logger.error(f"Error deleting old messages: {e}")
            return False
    
    # Contact operations
    
    def save_contact(self, contact: Contact) -> bool:
        """Save or update a contact"""
        try:
            with self._local_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO contacts 
                    (id, platform, name, phone, username, is_important, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contact.id,
                    contact.platform.value,
                    contact.name,
                    contact.phone,
                    contact.username,
                    contact.is_important,
                    json.dumps(contact.metadata),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Error saving contact: {e}")
            return False
    
    def get_contact(self, contact_id: str) -> Optional[Contact]:
        """Get contact by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_contact(row)
            return None
        except Exception as e:
            logger.error(f"Error getting contact: {e}")
            return None
    
    def get_contacts(self, platform: Optional[Platform] = None) -> List[Contact]:
        """Get all contacts"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if platform:
                cursor.execute(
                    "SELECT * FROM contacts WHERE platform = ? ORDER BY name",
                    (platform.value,)
                )
            else:
                cursor.execute("SELECT * FROM contacts ORDER BY platform, name")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_contact(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []
    
    def search_contact(self, query: str, platform: Optional[Platform] = None) -> List[Contact]:
        """Search contacts by name, phone, or username"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query_pattern = f"%{query}%"
            
            if platform:
                cursor.execute("""
                    SELECT * FROM contacts 
                    WHERE platform = ? 
                    AND (name LIKE ? OR phone LIKE ? OR username LIKE ?)
                    ORDER BY 
                        CASE WHEN name LIKE ? THEN 0 ELSE 1 END,
                        name
                """, (platform.value, query_pattern, query_pattern, query_pattern, query_pattern))
            else:
                cursor.execute("""
                    SELECT * FROM contacts 
                    WHERE name LIKE ? OR phone LIKE ? OR username LIKE ?
                    ORDER BY platform, 
                        CASE WHEN name LIKE ? THEN 0 ELSE 1 END,
                        name
                """, (query_pattern, query_pattern, query_pattern, query_pattern))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_contact(row) for row in rows]
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            return []
    
    def mark_contact_important(self, contact_id: str, important: bool = True) -> bool:
        """Mark contact as important/unimportant"""
        try:
            with self._local_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute(
                    "UPDATE contacts SET is_important = ?, updated_at = ? WHERE id = ?",
                    (important, datetime.now().isoformat(), contact_id)
                )
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Error marking contact important: {e}")
            return False
    
    # Helper methods
    
    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """Convert database row to Message object"""
        return Message(
            id=row['id'],
            platform=Platform(row['platform']),
            sender=row['sender'],
            sender_name=row['sender_name'],
            text=row['text'] or '',
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None,
            read=bool(row['read']),
            priority=MessagePriority(row['priority'] or 'normal'),
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def _row_to_contact(self, row: sqlite3.Row) -> Contact:
        """Convert database row to Contact object"""
        return Contact(
            id=row['id'],
            platform=Platform(row['platform']),
            name=row['name'],
            phone=row['phone'],
            username=row['username'],
            is_important=bool(row['is_important']),
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def clear_all_data(self) -> bool:
        """Clear all messages and contacts (for testing)"""
        try:
            with self._local_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM messages")
                cursor.execute("DELETE FROM contacts")
                
                conn.commit()
                conn.close()
                logger.warning("All message data cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            return False
