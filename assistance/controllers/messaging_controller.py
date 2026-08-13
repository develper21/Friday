"""
Messaging Controller
Handles voice commands for WhatsApp and Instagram messaging
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from core.interfaces.messaging_service import (
    IMessagingService, IMessageMonitor, Platform, Message, Contact
)
from assistance.utils.logger import logger


class MessagingController:
    """Controller for messaging voice commands"""
    
    def __init__(
        self,
        whatsapp_service: Optional[IMessagingService] = None,
        instagram_service: Optional[IMessagingService] = None,
        message_monitor: Optional[IMessageMonitor] = None,
        tts_service = None
    ):
        """
        Initialize messaging controller
        
        Args:
            whatsapp_service: WhatsApp messaging service
            instagram_service: Instagram messaging service
            message_monitor: Message monitoring service
            tts_service: Text-to-speech service for responses
        """
        self.whatsapp_service = whatsapp_service
        self.instagram_service = instagram_service
        self.message_monitor = message_monitor
        self.tts_service = tts_service
        
        self._last_check_time = None
        self._unread_alert_threshold_days = 3
        
        # Track conversation context for replies
        self._last_contact = None
        self._last_platform = None
    
    def _get_service(self, platform: Platform) -> Optional[IMessagingService]:
        """Get messaging service for platform"""
        if platform == Platform.WHATSAPP:
            return self.whatsapp_service
        elif platform == Platform.INSTAGRAM:
            return self.instagram_service
        return None
    
    def _speak(self, text: str):
        """Speak text using TTS service"""
        if self.tts_service:
            self.tts_service.speak(text)
        else:
            logger.speech(f"[TTS]: {text}")
    
    def read_whatsapp_messages(self, limit: int = 10) -> Tuple[bool, str]:
        """Read unread WhatsApp messages"""
        try:
            if not self.whatsapp_service:
                return False, "Sorry sir, WhatsApp service is not enabled"
            
            if not self.whatsapp_service.is_authenticated():
                auth_success = self.whatsapp_service.authenticate()
                if not auth_success:
                    return False, "Sorry sir, I could not authenticate with WhatsApp"
            
            messages = self.whatsapp_service.get_unread_messages(limit=limit)
            
            if not messages:
                self._speak("You have no unread WhatsApp messages")
                return True, "No unread WhatsApp messages"
            
            response = f"You have {len(messages)} unread WhatsApp messages. "
            
            # Group messages by sender
            messages_by_sender = {}
            for msg in messages:
                if msg.sender not in messages_by_sender:
                    messages_by_sender[msg.sender] = []
                messages_by_sender[msg.sender].append(msg)
            
            # Read messages grouped by sender
            for sender, sender_messages in messages_by_sender.items():
                sender_name = sender_messages[0].sender_name
                response += f"Message from {sender_name}. "
                
                for msg in sender_messages[:3]:  # Max 3 messages per sender
                    if msg.text:
                        response += f"{msg.text}. "
                
                if len(sender_messages) > 3:
                    response += f"And {len(sender_messages) - 3} more messages. "
            
            self._speak(response)
            logger.system(f"Read {len(messages)} WhatsApp messages")
            
            # Update context for potential reply
            if messages_by_sender:
                self._last_contact = list(messages_by_sender.keys())[0]
                self._last_platform = Platform.WHATSAPP
            
            return True, response
            
        except Exception as e:
            logger.error(f"Error reading WhatsApp messages: {e}")
            return False, f"Sorry sir, I could not read WhatsApp messages: {str(e)}"
    
    def read_instagram_messages(self, limit: int = 10) -> Tuple[bool, str]:
        """Read unread Instagram messages"""
        try:
            if not self.instagram_service:
                return False, "Sorry sir, Instagram service is not enabled"
            
            if not self.instagram_service.is_authenticated():
                auth_success = self.instagram_service.authenticate()
                if not auth_success:
                    return False, "Sorry sir, I could not authenticate with Instagram"
            
            messages = self.instagram_service.get_unread_messages(limit=limit)
            
            if not messages:
                self._speak("You have no unread Instagram messages")
                return True, "No unread Instagram messages"
            
            response = f"You have {len(messages)} unread Instagram messages. "
            
            # Group messages by sender
            messages_by_sender = {}
            for msg in messages:
                if msg.sender not in messages_by_sender:
                    messages_by_sender[msg.sender] = []
                messages_by_sender[msg.sender].append(msg)
            
            # Read messages grouped by sender
            for sender, sender_messages in messages_by_sender.items():
                sender_name = sender_messages[0].sender_name
                response += f"Message from {sender_name}. "
                
                for msg in sender_messages[:3]:  # Max 3 messages per sender
                    if msg.text:
                        response += f"{msg.text}. "
                
                if len(sender_messages) > 3:
                    response += f"And {len(sender_messages) - 3} more messages. "
            
            self._speak(response)
            logger.system(f"Read {len(messages)} Instagram messages")
            
            # Update context for potential reply
            if messages_by_sender:
                self._last_contact = list(messages_by_sender.keys())[0]
                self._last_platform = Platform.INSTAGRAM
            
            return True, response
            
        except Exception as e:
            logger.error(f"Error reading Instagram messages: {e}")
            return False, f"Sorry sir, I could not read Instagram messages: {str(e)}"
    
    def read_all_messages(self, limit: int = 10) -> Tuple[bool, str]:
        """Read unread messages from all platforms"""
        try:
            all_messages = []
            
            if self.whatsapp_service:
                whatsapp_messages = self.whatsapp_service.get_unread_messages(limit=limit)
                all_messages.extend(whatsapp_messages)
            
            if self.instagram_service:
                instagram_messages = self.instagram_service.get_unread_messages(limit=limit)
                all_messages.extend(instagram_messages)
            
            if not all_messages:
                self._speak("You have no unread messages")
                return True, "No unread messages"
            
            # Sort by timestamp
            all_messages.sort(key=lambda x: x.timestamp or datetime.min, reverse=True)
            
            response = f"You have {len(all_messages)} total unread messages. "
            
            # Count by platform
            whatsapp_count = sum(1 for m in all_messages if m.platform == Platform.WHATSAPP)
            instagram_count = sum(1 for m in all_messages if m.platform == Platform.INSTAGRAM)
            
            if whatsapp_count > 0:
                response += f"{whatsapp_count} on WhatsApp. "
            if instagram_count > 0:
                response += f"{instagram_count} on Instagram. "
            
            # Read latest messages
            for msg in all_messages[:5]:
                platform_name = "WhatsApp" if msg.platform == Platform.WHATSAPP else "Instagram"
                response += f"On {platform_name}, message from {msg.sender_name}. "
                if msg.text:
                    response += f"{msg.text}. "
            
            self._speak(response)
            logger.system(f"Read {len(all_messages)} total messages")
            
            return True, response
            
        except Exception as e:
            logger.error(f"Error reading all messages: {e}")
            return False, f"Sorry sir, I could not read messages: {str(e)}"
    
    def send_whatsapp_message(self, recipient: str, text: str) -> Tuple[bool, str]:
        """Send WhatsApp message"""
        try:
            if not self.whatsapp_service:
                return False, "Sorry sir, WhatsApp service is not enabled"
            
            if not self.whatsapp_service.is_authenticated():
                auth_success = self.whatsapp_service.authenticate()
                if not auth_success:
                    return False, "Sorry sir, I could not authenticate with WhatsApp"
            
            # Search for contact if not a phone number
            if not recipient.isdigit():
                contact = self.whatsapp_service.search_contact(recipient)
                if contact:
                    recipient = contact.phone or contact.id
                else:
                    return False, f"Sorry sir, I could not find contact {recipient}"
            
            success = self.whatsapp_service.send_message(recipient, text)
            
            if success:
                self._speak(f"Message sent to {recipient}")
                return True, f"Message sent to {recipient}"
            else:
                return False, "Sorry sir, I could not send the message"
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False, f"Sorry sir, I could not send WhatsApp message: {str(e)}"
    
    def send_instagram_message(self, recipient: str, text: str) -> Tuple[bool, str]:
        """Send Instagram message"""
        try:
            if not self.instagram_service:
                return False, "Sorry sir, Instagram service is not enabled"
            
            if not self.instagram_service.is_authenticated():
                auth_success = self.instagram_service.authenticate()
                if not auth_success:
                    return False, "Sorry sir, I could not authenticate with Instagram"
            
            # Search for contact
            contact = self.instagram_service.search_contact(recipient)
            if contact:
                recipient_id = contact.id
            else:
                recipient_id = recipient
            
            success = self.instagram_service.send_message(recipient_id, text)
            
            if success:
                self._speak(f"Message sent to {recipient}")
                return True, f"Message sent to {recipient}"
            else:
                return False, "Sorry sir, I could not send the message"
                
        except Exception as e:
            logger.error(f"Error sending Instagram message: {e}")
            return False, f"Sorry sir, I could not send Instagram message: {str(e)}"
    
    def reply_to_last_message(self, text: str) -> Tuple[bool, str]:
        """Reply to the last message that was read"""
        try:
            if not self._last_contact or not self._last_platform:
                return False, "Sorry sir, I don't know which message to reply to. Please specify the contact"
            
            service = self._get_service(self._last_platform)
            if not service:
                return False, f"Sorry sir, {self._last_platform.value} service is not enabled"
            
            success = service.send_message(self._last_contact, text)
            
            if success:
                self._speak("Reply sent")
                return True, "Reply sent"
            else:
                return False, "Sorry sir, I could not send the reply"
                
        except Exception as e:
            logger.error(f"Error replying to message: {e}")
            return False, f"Sorry sir, I could not send reply: {str(e)}"
    
    def get_whatsapp_unread_count(self) -> Tuple[bool, str]:
        """Get WhatsApp unread message count"""
        try:
            if not self.whatsapp_service:
                return False, "Sorry sir, WhatsApp service is not enabled"
            
            count = self.whatsapp_service.get_unread_count()
            response = f"You have {count} unread WhatsApp messages"
            self._speak(response)
            return True, response
            
        except Exception as e:
            logger.error(f"Error getting WhatsApp unread count: {e}")
            return False, f"Sorry sir, I could not get unread count: {str(e)}"
    
    def get_instagram_unread_count(self) -> Tuple[bool, str]:
        """Get Instagram unread message count"""
        try:
            if not self.instagram_service:
                return False, "Sorry sir, Instagram service is not enabled"
            
            count = self.instagram_service.get_unread_count()
            response = f"You have {count} unread Instagram messages"
            self._speak(response)
            return True, response
            
        except Exception as e:
            logger.error(f"Error getting Instagram unread count: {e}")
            return False, f"Sorry sir, I could not get unread count: {str(e)}"
    
    def get_total_unread_count(self) -> Tuple[bool, str]:
        """Get total unread message count across all platforms"""
        try:
            total = 0
            breakdown = {}
            
            if self.whatsapp_service:
                whatsapp_count = self.whatsapp_service.get_unread_count()
                total += whatsapp_count
                breakdown['WhatsApp'] = whatsapp_count
            
            if self.instagram_service:
                instagram_count = self.instagram_service.get_unread_count()
                total += instagram_count
                breakdown['Instagram'] = instagram_count
            
            response = f"You have {total} total unread messages"
            
            if breakdown:
                response += ". "
                for platform, count in breakdown.items():
                    if count > 0:
                        response += f"{count} on {platform}. "
            
            self._speak(response)
            return True, response
            
        except Exception as e:
            logger.error(f"Error getting total unread count: {e}")
            return False, f"Sorry sir, I could not get unread count: {str(e)}"
    
    def check_unread_alert(self) -> Tuple[bool, str]:
        """Check if unread alert should be triggered (messages not checked for days)"""
        try:
            if not self._last_check_time:
                return False, ""
            
            days_since_check = (datetime.now() - self._last_check_time).days
            
            if days_since_check >= self._unread_alert_threshold_days:
                total_count = 0
                if self.whatsapp_service:
                    total_count += self.whatsapp_service.get_unread_count()
                if self.instagram_service:
                    total_count += self.instagram_service.get_unread_count()
                
                if total_count > 0:
                    alert = f"Sir, you haven't checked your messages for {days_since_check} days. You have {total_count} unread messages"
                    self._speak(alert)
                    logger.warning(f"Unread alert triggered: {alert}")
                    return True, alert
            
            return False, ""
            
        except Exception as e:
            logger.error(f"Error checking unread alert: {e}")
            return False, ""
    
    def mark_all_as_read(self, platform: Optional[Platform] = None) -> Tuple[bool, str]:
        """Mark all messages as read"""
        try:
            service = None
            platform_name = ""
            
            if platform == Platform.WHATSAPP:
                service = self.whatsapp_service
                platform_name = "WhatsApp"
            elif platform == Platform.INSTAGRAM:
                service = self.instagram_service
                platform_name = "Instagram"
            else:
                # Mark all as read on all platforms
                if self.whatsapp_service:
                    self.whatsapp_service.mark_all_as_read()
                if self.instagram_service:
                    self.instagram_service.mark_all_as_read()
                self._speak("All messages marked as read")
                return True, "All messages marked as read"
            
            if not service:
                return False, f"Sorry sir, {platform_name} service is not enabled"
            
            # Mark messages as read
            unread_messages = service.get_unread_messages(limit=100)
            if unread_messages:
                message_ids = [msg.id for msg in unread_messages]
                service.mark_as_read(message_ids)
            
            self._speak(f"All {platform_name} messages marked as read")
            return True, f"All {platform_name} messages marked as read"
            
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            return False, f"Sorry sir, I could not mark messages as read: {str(e)}"
    
    def get_message_activity(self, days: int = 7) -> Tuple[bool, str]:
        """Get message activity for specified days"""
        try:
            total = 0
            breakdown = {}
            
            if self.whatsapp_service:
                whatsapp_count = self.whatsapp_service.get_message_count_since(days)
                total += whatsapp_count
                breakdown['WhatsApp'] = whatsapp_count
            
            if self.instagram_service:
                instagram_count = self.instagram_service.get_message_count_since(days)
                total += instagram_count
                breakdown['Instagram'] = instagram_count
            
            response = f"You have received {total} messages in the last {days} days"
            
            if breakdown:
                response += ". "
                for platform, count in breakdown.items():
                    if count > 0:
                        response += f"{count} on {platform}. "
            
            self._speak(response)
            return True, response
            
        except Exception as e:
            logger.error(f"Error getting message activity: {e}")
            return False, f"Sorry sir, I could not get message activity: {str(e)}"
    
    def check_messages_not_viewed(self, days: int = 3) -> Tuple[bool, str]:
        """Check if messages haven't been viewed for specified days and alert"""
        try:
            total_count = 0
            breakdown = {}
            
            if self.whatsapp_service:
                whatsapp_count = self.whatsapp_service.get_message_count_since(days)
                total_count += whatsapp_count
                breakdown['WhatsApp'] = whatsapp_count
            
            if self.instagram_service:
                instagram_count = self.instagram_service.get_message_count_since(days)
                total_count += instagram_count
                breakdown['Instagram'] = instagram_count
            
            if total_count > 0:
                response = f"Sir, you haven't checked your messages for {days} days. Total {total_count} messages have arrived. "
                
                for platform, count in breakdown.items():
                    if count > 0:
                        response += f"{count} on {platform}. "
                
                self._speak(response)
                logger.warning(f"Messages not viewed alert: {response}")
                return True, response
            else:
                return True, "No new messages in the specified period"
                
        except Exception as e:
            logger.error(f"Error checking messages not viewed: {e}")
            return False, f"Sorry sir, I could not check message status: {str(e)}"
    
    def update_last_check_time(self):
        """Update the last check time"""
        self._last_check_time = datetime.now()
