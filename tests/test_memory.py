"""
Tests for Memory System
"""

import pytest
from datetime import datetime


class TestSessionMemory:
    """Test suite for session memory (Redis)"""

    @pytest.mark.asyncio
    async def test_create_session(self):
        """Should create a new session"""
        from backend.memory.session_memory import SessionMemory
        
        memory = SessionMemory()
        await memory.connect()
        
        result = await memory.create_session("test-session-123")
        
        assert result == True
        
        await memory.disconnect()

    @pytest.mark.asyncio
    async def test_store_and_retrieve_context(self):
        """Should store and retrieve conversation context"""
        from backend.memory.session_memory import SessionMemory
        
        memory = SessionMemory()
        await memory.connect()
        
        session_id = "test-session-456"
        await memory.create_session(session_id)
        
        # Update context
        await memory.update_context(session_id, {
            "current_intent": "book_appointment",
            "collected_slots": {"doctor": "cardiologist"}
        })
        
        # Retrieve
        session = await memory.get_session(session_id)
        
        assert session["current_intent"] == "book_appointment"
        assert session["collected_slots"]["doctor"] == "cardiologist"
        
        await memory.disconnect()

    @pytest.mark.asyncio
    async def test_add_to_history(self):
        """Should add messages to conversation history"""
        from backend.memory.session_memory import SessionMemory
        
        memory = SessionMemory()
        await memory.connect()
        
        session_id = "test-session-789"
        await memory.create_session(session_id)
        
        await memory.add_to_history(session_id, "user", "Book appointment")
        await memory.add_to_history(session_id, "assistant", "Which doctor?")
        
        session = await memory.get_session(session_id)
        
        assert len(session["conversation_history"]) == 2
        
        await memory.disconnect()

    @pytest.mark.asyncio
    async def test_session_expiry(self):
        """Session should have TTL"""
        from backend.memory.session_memory import SessionMemory
        
        memory = SessionMemory()
        await memory.connect()
        
        # Check that session has TTL set
        session_id = "test-ttl-session"
        await memory.create_session(session_id)
        
        if memory.client:
            ttl = await memory.client.ttl(memory._session_key(session_id))
            assert ttl > 0  # Has expiry
        
        await memory.disconnect()


class TestPersistentMemory:
    """Test suite for persistent memory (PostgreSQL)"""

    @pytest.mark.asyncio
    async def test_store_patient_preferences(self):
        """Should store patient preferences"""
        from backend.memory.persistent_memory import PersistentMemory
        
        memory = PersistentMemory()
        await memory.connect()
        
        await memory.update_patient_preferences(
            patient_id="patient-123",
            language="hi",
            preferred_hospital="Apollo"
        )
        
        prefs = await memory.get_patient_preferences("patient-123")
        
        assert prefs["language"] == "hi"
        
        await memory.disconnect()

    @pytest.mark.asyncio
    async def test_get_appointment_history(self):
        """Should retrieve past appointments"""
        from backend.memory.persistent_memory import PersistentMemory
        
        memory = PersistentMemory()
        await memory.connect()
        
        history = await memory.get_appointment_history(
            patient_id="patient-123",
            limit=5
        )
        
        assert isinstance(history, list)
        
        await memory.disconnect()
