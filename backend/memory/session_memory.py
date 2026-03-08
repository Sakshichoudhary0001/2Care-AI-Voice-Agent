"""
Session Memory
Short-term memory using Redis for active conversation sessions
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis.asyncio as redis

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class SessionMemory:
    """
    Redis-based session memory for managing conversation state.
    
    Features:
    - Stores current conversation context
    - Maintains slot values during multi-turn dialogs
    - Auto-expires after inactivity (default: 30 minutes)
    - Fast access for low-latency responses
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.ttl = settings.SESSION_TTL_SECONDS
        self.client: Optional[redis.Redis] = None
        self.key_prefix = "session:"
    
    async def connect(self):
        """Establish Redis connection"""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")
    
    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"{self.key_prefix}{session_id}"
    
    async def create_session(self, session_id: str, initial_data: Dict[str, Any] = None) -> bool:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            initial_data: Initial session data
            
        Returns:
            True if created successfully
        """
        if not self.client:
            logger.warning("Redis not connected, using in-memory fallback")
            return False
        
        try:
            data = {
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "language": "en",
                "current_intent": None,
                "collected_slots": {},
                "conversation_history": [],
                "patient_id": None,
                "turn_count": 0,
                **(initial_data or {})
            }
            
            key = self._session_key(session_id)
            await self.client.setex(key, self.ttl, json.dumps(data))
            logger.debug(f"Session created: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dict or None if not found
        """
        if not self.client:
            return None
        
        try:
            key = self._session_key(session_id)
            data = await self.client.get(key)
            
            if data:
                # Refresh TTL on access
                await self.client.expire(key, self.ttl)
                return json.loads(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully
        """
        if not self.client:
            return False
        
        try:
            # Get existing data
            current = await self.get_session(session_id)
            if not current:
                return False
            
            # Merge updates
            current.update(updates)
            current["updated_at"] = datetime.utcnow().isoformat()
            
            # Save back
            key = self._session_key(session_id)
            await self.client.setex(key, self.ttl, json.dumps(current))
            return True
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    async def add_turn(self, session_id: str, role: str, content: str, metadata: Dict = None) -> bool:
        """
        Add a conversation turn to history.
        
        Args:
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (intent, slots, etc.)
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            turn = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            history = session.get("conversation_history", [])
            history.append(turn)
            
            # Keep only last 20 turns to manage memory
            if len(history) > 20:
                history = history[-20:]
            
            return await self.update_session(session_id, {
                "conversation_history": history,
                "turn_count": session.get("turn_count", 0) + 1
            })
            
        except Exception as e:
            logger.error(f"Error adding turn: {e}")
            return False
    
    async def get_conversation_history(self, session_id: str, last_n: int = None) -> List[Dict]:
        """Get conversation history for a session"""
        session = await self.get_session(session_id)
        if not session:
            return []
        
        history = session.get("conversation_history", [])
        if last_n:
            return history[-last_n:]
        return history
    
    async def set_slots(self, session_id: str, slots: Dict[str, Any]) -> bool:
        """Update collected slots for the session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        current_slots = session.get("collected_slots", {})
        current_slots.update(slots)
        
        return await self.update_session(session_id, {"collected_slots": current_slots})
    
    async def get_slots(self, session_id: str) -> Dict[str, Any]:
        """Get collected slots for the session"""
        session = await self.get_session(session_id)
        if not session:
            return {}
        return session.get("collected_slots", {})
    
    async def clear_slots(self, session_id: str) -> bool:
        """Clear collected slots (after successful action)"""
        return await self.update_session(session_id, {"collected_slots": {}, "current_intent": None})
    
    async def set_intent(self, session_id: str, intent: str) -> bool:
        """Set the current intent for the session"""
        return await self.update_session(session_id, {"current_intent": intent})
    
    async def set_patient(self, session_id: str, patient_id: str, patient_info: Dict = None) -> bool:
        """Associate a patient with the session"""
        updates = {"patient_id": patient_id}
        if patient_info:
            updates["patient_info"] = patient_info
            if patient_info.get("preferred_language"):
                updates["language"] = patient_info["preferred_language"]
        return await self.update_session(session_id, updates)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if not self.client:
            return False
        
        try:
            key = self._session_key(session_id)
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        if not self.client:
            return False
        
        try:
            key = self._session_key(session_id)
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking session: {e}")
            return False
