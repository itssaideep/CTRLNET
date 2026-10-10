import asyncio
from typing import Dict, Any, Callable

class EventBus:
    """Async event bus for real-time WebSocket communication."""
    
    def __init__(self):
        self._subscribers = set()
        
    def subscribe(self, queue: asyncio.Queue):
        """Add a subscriber queue."""
        self._subscribers.add(queue)
        
    def unsubscribe(self, queue: asyncio.Queue):
        """Remove a subscriber queue."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)
            
    async def emit(self, event_name: str, payload: Dict[str, Any]):
        """Emit an event to all subscribers."""
        message = {
            "event": event_name,
            "data": payload
        }
        
        for queue in self._subscribers:
            await queue.put(message)

# Global singleton
event_bus = EventBus()
