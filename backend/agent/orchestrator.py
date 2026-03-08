"""
Agent Orchestrator - Main brain of the voice AI agent
Coordinates intent classification, slot filling, tool execution, and response generation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from backend.agent.reasoning.intent_classifier import IntentClassifier
from backend.agent.reasoning.slot_filler import SlotFiller
from backend.agent.reasoning.response_generator import ResponseGenerator
from backend.agent.tools.appointment_tools import AppointmentTools
from backend.agent.prompts.templates import PromptTemplates
from backend.memory.session_memory import SessionMemory
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Main orchestrator for the voice AI agent.
    Implements a ReAct-style reasoning loop:
    1. Observe: Receive user input
    2. Think: Classify intent, extract slots
    3. Act: Execute tools if needed
    4. Respond: Generate natural language response
    """
    
    # Supported intents
    INTENTS = [
        "book_appointment",
        "cancel_appointment", 
        "reschedule_appointment",
        "check_availability",
        "get_appointment_details",
        "list_doctors",
        "get_doctor_info",
        "greeting",
        "goodbye",
        "help",
        "out_of_scope",
        "clarification"
    ]
    
    # Required slots per intent
    REQUIRED_SLOTS = {
        "book_appointment": ["doctor_name_or_specialty", "date", "time"],
        "cancel_appointment": ["appointment_id_or_date"],
        "reschedule_appointment": ["appointment_id_or_date", "new_date", "new_time"],
        "check_availability": ["doctor_name_or_specialty", "date"],
        "get_appointment_details": ["appointment_id_or_date"],
        "list_doctors": [],  # Optional: specialty filter
        "get_doctor_info": ["doctor_name"],
    }
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.intent_classifier = IntentClassifier()
        self.slot_filler = SlotFiller()
        self.response_generator = ResponseGenerator()
        self.tools = AppointmentTools()
        self.prompts = PromptTemplates()
        
        # Conversation state
        self.context = {
            "current_intent": None,
            "collected_slots": {},
            "pending_slots": [],
            "conversation_history": [],
            "patient_id": None,
            "language": "en",
            "turn_count": 0
        }
    
    async def process(self, user_input: str, language: str = "en") -> str:
        """
        Main processing pipeline for user input.
        Returns agent response text.
        """
        self.context["language"] = language
        self.context["turn_count"] += 1
        
        logger.info(f"[{self.session_id}] Processing: {user_input[:50]}...")
        
        # Add to conversation history
        self.context["conversation_history"].append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            # Step 1: Classify intent
            intent, confidence = await self.intent_classifier.classify(
                user_input,
                self.context["conversation_history"],
                language
            )
            
            logger.info(f"Intent: {intent} (confidence: {confidence})")
            
            # Handle low confidence
            if confidence < 0.6:
                response = await self._handle_clarification(user_input, language)
                return response
            
            # Step 2: Extract and fill slots
            new_slots = await self.slot_filler.extract(
                user_input,
                intent,
                self.context["collected_slots"],
                language
            )
            
            # Merge new slots
            self.context["collected_slots"].update(new_slots)
            self.context["current_intent"] = intent
            
            # Step 3: Check if we have all required slots
            missing_slots = self._get_missing_slots(intent)
            
            if missing_slots:
                # Ask for missing information
                response = await self._ask_for_slots(missing_slots, language)
            else:
                # Execute the action
                response = await self._execute_intent(intent, language)
                # Reset slots after successful execution
                if "error" not in response.lower():
                    self.context["collected_slots"] = {}
                    self.context["current_intent"] = None
            
            # Add response to history
            self.context["conversation_history"].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return self.prompts.get_error_response(language)
    
    def _get_missing_slots(self, intent: str) -> List[str]:
        """Check which required slots are missing"""
        required = self.REQUIRED_SLOTS.get(intent, [])
        collected = set(self.context["collected_slots"].keys())
        return [slot for slot in required if slot not in collected]
    
    async def _ask_for_slots(self, missing_slots: List[str], language: str) -> str:
        """Generate a question to collect missing slots"""
        slot_to_ask = missing_slots[0]  # Ask one at a time
        return self.prompts.get_slot_question(slot_to_ask, language)
    
    async def _execute_intent(self, intent: str, language: str) -> str:
        """Execute the intent with collected slots"""
        slots = self.context["collected_slots"]
        
        try:
            if intent == "book_appointment":
                result = await self.tools.book_appointment(
                    patient_id=self.context.get("patient_id"),
                    doctor_spec=slots.get("doctor_name_or_specialty"),
                    date=slots.get("date"),
                    time=slots.get("time"),
                    reason=slots.get("reason")
                )
                return self.prompts.format_booking_response(result, language)
            
            elif intent == "cancel_appointment":
                result = await self.tools.cancel_appointment(
                    appointment_identifier=slots.get("appointment_id_or_date"),
                    patient_id=self.context.get("patient_id")
                )
                return self.prompts.format_cancellation_response(result, language)
            
            elif intent == "reschedule_appointment":
                result = await self.tools.reschedule_appointment(
                    appointment_identifier=slots.get("appointment_id_or_date"),
                    new_date=slots.get("new_date"),
                    new_time=slots.get("new_time"),
                    patient_id=self.context.get("patient_id")
                )
                return self.prompts.format_reschedule_response(result, language)
            
            elif intent == "check_availability":
                result = await self.tools.check_availability(
                    doctor_spec=slots.get("doctor_name_or_specialty"),
                    date=slots.get("date")
                )
                return self.prompts.format_availability_response(result, language)
            
            elif intent == "get_appointment_details":
                result = await self.tools.get_appointment_details(
                    appointment_identifier=slots.get("appointment_id_or_date"),
                    patient_id=self.context.get("patient_id")
                )
                return self.prompts.format_appointment_details(result, language)
            
            elif intent == "list_doctors":
                result = await self.tools.list_doctors(
                    specialty=slots.get("specialty")
                )
                return self.prompts.format_doctor_list(result, language)
            
            elif intent == "get_doctor_info":
                result = await self.tools.get_doctor_info(
                    doctor_name=slots.get("doctor_name")
                )
                return self.prompts.format_doctor_info(result, language)
            
            elif intent == "greeting":
                return self.prompts.get_greeting(language)
            
            elif intent == "goodbye":
                return self.prompts.get_goodbye(language)
            
            elif intent == "help":
                return self.prompts.get_help(language)
            
            else:
                return self.prompts.get_out_of_scope(language)
                
        except Exception as e:
            logger.error(f"Error executing intent {intent}: {e}")
            return self.prompts.get_error_response(language)
    
    async def _handle_clarification(self, user_input: str, language: str) -> str:
        """Handle unclear input by asking for clarification"""
        return self.prompts.get_clarification_request(language)
    
    def set_patient_context(self, patient_id: str, patient_info: Dict[str, Any]):
        """Set patient context for personalization"""
        self.context["patient_id"] = patient_id
        self.context["patient_info"] = patient_info
        if patient_info.get("preferred_language"):
            self.context["language"] = patient_info["preferred_language"]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of the conversation for logging"""
        return {
            "session_id": self.session_id,
            "turn_count": self.context["turn_count"],
            "final_intent": self.context["current_intent"],
            "collected_slots": self.context["collected_slots"],
            "history_length": len(self.context["conversation_history"])
        }
