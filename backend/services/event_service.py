"""
Event Service for ChargeShield Phase 9 Real-Time Event Intelligence.
Provides thread-safe event publishing, retrieval, and streaming with explicit data-state labeling.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import threading
import uuid

class EventService:
    def __init__(self, max_events: int = 500):
        self.max_events = max_events
        self._events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def publish_event(
        self,
        event_type: str,
        message: str,
        data_state: str = "SIMULATION",
        dispute_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        source: str = "SIMULATION_ENGINE",
        status: str = "COMPLETED",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Publish a structured lifecycle event into the in-memory event stream.
        """
        event = {
            "event_id": f"EVT_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6].upper()}",
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dispute_id": dispute_id,
            "transaction_id": transaction_id,
            "source": source,
            "data_state": data_state,  # "SIMULATION", "HISTORICAL", or "PRODUCTION"
            "status": status,
            "message": message,
            "metadata": metadata or {}
        }

        with self._lock:
            self._events.append(event)
            if len(self._events) > self.max_events:
                self._events.pop(0)

        return event

    def get_events(
        self,
        limit: int = 50,
        data_state: Optional[str] = None,
        dispute_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chronological events filtered by data_state or dispute_id.
        """
        with self._lock:
            filtered = list(self._events)

        if data_state:
            filtered = [e for e in filtered if e.get("data_state") == data_state]

        if dispute_id:
            filtered = [e for e in filtered if e.get("dispute_id") == dispute_id]

        # Return latest events sorted chronologically
        return filtered[-limit:]

    def clear_events(self):
        """Clear event stream buffer."""
        with self._lock:
            self._events.clear()

# Global singleton instance
event_service = EventService()
