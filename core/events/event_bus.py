"""
Event Bus System
Implements event-driven architecture for loose coupling between components
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for the voice assistant"""
    AUDIO_STARTED = "audio_started"
    AUDIO_STOPPED = "audio_stopped"
    SPEECH_DETECTED = "speech_detected"
    SPEECH_ENDED = "speech_ended"
    SPEECH_RECOGNIZED = "speech_recognized"
    INTENT_DETECTED = "intent_detected"
    COMMAND_EXECUTED = "command_executed"
    TTS_STARTED = "tts_started"
    TTS_STOPPED = "tts_stopped"
    ERROR_OCCURRED = "error_occurred"
    TRACKING_STARTED = "tracking_started"
    TRACKING_STOPPED = "tracking_stopped"
    LOCATION_UPDATE = "location_update"


@dataclass
class Event:
    """Event data structure"""
    type: EventType    
    data: Any
    timestamp: float


class EventBus:
    """Event bus for publishing and subscribing to events"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue: asyncio.Queue = None
        self._running = False
        self._loop = None
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """
        Subscribe to event type
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """
        Unsubscribe from event type
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Callback function to remove
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed from event: {event_type}")
    
    async def publish(self, event: Event):
        """
        Publish event to all subscribers
        
        Args:
            event: Event to publish
        """
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Event handler error for {event.type}: {e}", exc_info=True)
    
    async def publish_sync(self, event: Event):
        """
        Publish event synchronously (for non-async contexts)
        
        Args:
            event: Event to publish
        """
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Event handler error for {event.type}: {e}", exc_info=True)
    
    async def start(self):
        """Start event processing loop"""
        self._event_queue = asyncio.Queue()
        self._running = True
        self._loop = asyncio.get_event_loop()
        
        logger.info("Event bus started")
        
        while self._running:
            event = await self._event_queue.get()
            await self.publish(event)
    
    def stop(self):
        """Stop event processing"""
        self._running = False
        logger.info("Event bus stopped")
    
    async def queue_event(self, event: Event):
        """
        Queue event for processing
        
        Args:
            event: Event to queue
        """
        if self._event_queue:
            await self._event_queue.put(event)
    
    def create_event(self, event_type: EventType, data: Any = None) -> Event:
        """
        Create an event with current timestamp
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Event object
        """
        return Event(
            type=event_type,
            data=data,
            timestamp=time.time()
        )
