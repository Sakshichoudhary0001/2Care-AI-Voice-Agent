"""
Response Generator
Generates natural language responses using LLM
"""

from typing import Dict, Any, Optional, List
import logging
from openai import AsyncOpenAI

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates natural, conversational responses.
    Uses LLM for complex responses, templates for simple ones.
    """
    
    SYSTEM_PROMPTS = {
        "en": """You are a friendly and professional medical receptionist AI assistant for 2Care.ai clinic. 
Your role is to help patients with appointment booking, rescheduling, and cancellations.
Keep responses concise (1-2 sentences), warm, and helpful.
Always confirm important details like dates and times.
If you don't have enough information, ask one clarifying question at a time.""",
        
        "hi": """आप 2Care.ai क्लिनिक के लिए एक मैत्रीपूर्ण और पेशेवर मेडिकल रिसेप्शनिस्ट AI सहायक हैं।
आपकी भूमिका मरीजों की अपॉइंटमेंट बुकिंग, रीशेड्यूलिंग और कैंसिलेशन में मदद करना है।
जवाब संक्षिप्त (1-2 वाक्य), गर्मजोशी भरे और सहायक रखें।
हमेशा तारीख और समय जैसे महत्वपूर्ण विवरण की पुष्टि करें।""",
        
        "ta": """நீங்கள் 2Care.ai கிளினிக்கின் நட்பான மற்றும் தொழில்முறை மருத்துவ வரவேற்பாளர் AI உதவியாளர்.
நோயாளிகளின் சந்திப்பு பதிவு, மறுதிட்டமிடல் மற்றும் ரத்துகளுக்கு உதவுவது உங்கள் பங்கு.
பதில்களை சுருக்கமாக (1-2 வாக்கியங்கள்), அன்பாக, உதவியாக வைக்கவும்.
தேதி, நேரம் போன்ற முக்கிய விவரங்களை எப்போதும் உறுதிப்படுத்தவும்."""
    }
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def generate(
        self,
        context: Dict[str, Any],
        user_message: str,
        language: str = "en",
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Generate a response based on context and user message.
        Falls back to template-based responses if LLM unavailable.
        """
        if not self.client:
            return self._generate_template_response(context, language)
        
        try:
            system_prompt = self.SYSTEM_PROMPTS.get(language, self.SYSTEM_PROMPTS["en"])
            
            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 6 turns)
            if conversation_history:
                for turn in conversation_history[-6:]:
                    messages.append({
                        "role": turn.get("role", "user"),
                        "content": turn.get("content", "")
                    })
            
            # Add context as system message
            context_str = f"""Current context:
- Intent: {context.get('current_intent', 'unknown')}
- Collected information: {context.get('collected_slots', {})}
- Patient ID: {context.get('patient_id', 'unknown')}"""
            messages.append({"role": "system", "content": context_str})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return self._generate_template_response(context, language)
    
    def _generate_template_response(self, context: Dict[str, Any], language: str) -> str:
        """Generate a template-based response as fallback"""
        intent = context.get("current_intent", "")
        slots = context.get("collected_slots", {})
        
        templates = {
            "en": {
                "book_appointment": "I'll help you book an appointment. ",
                "cancel_appointment": "I'll help you cancel your appointment. ",
                "reschedule_appointment": "I'll help you reschedule your appointment. ",
                "default": "How can I help you with your appointment today?"
            },
            "hi": {
                "book_appointment": "मैं आपकी अपॉइंटमेंट बुक करने में मदद करूंगा। ",
                "cancel_appointment": "मैं आपकी अपॉइंटमेंट कैंसिल करने में मदद करूंगा। ",
                "reschedule_appointment": "मैं आपकी अपॉइंटमेंट रीशेड्यूल करने में मदद करूंगा। ",
                "default": "मैं आपकी अपॉइंटमेंट में आज कैसे मदद कर सकता हूं?"
            },
            "ta": {
                "book_appointment": "உங்கள் சந்திப்பை பதிவு செய்ய உதவுகிறேன். ",
                "cancel_appointment": "உங்கள் சந்திப்பை ரத்து செய்ய உதவுகிறேன். ",
                "reschedule_appointment": "உங்கள் சந்திப்பை மறுதிட்டமிட உதவுகிறேன். ",
                "default": "இன்று உங்கள் சந்திப்பில் எவ்வாறு உதவ முடியும்?"
            }
        }
        
        lang_templates = templates.get(language, templates["en"])
        return lang_templates.get(intent, lang_templates["default"])
    
    async def generate_confirmation(
        self,
        action: str,
        details: Dict[str, Any],
        language: str = "en"
    ) -> str:
        """Generate a confirmation message for an action"""
        confirmations = {
            "book": {
                "en": f"Your appointment has been booked with {details.get('doctor_name', 'the doctor')} on {details.get('date', '')} at {details.get('time', '')}.",
                "hi": f"आपकी अपॉइंटमेंट {details.get('doctor_name', 'डॉक्टर')} के साथ {details.get('date', '')} को {details.get('time', '')} पर बुक हो गई है।",
                "ta": f"உங்கள் சந்திப்பு {details.get('doctor_name', 'மருத்துவர்')} உடன் {details.get('date', '')} அன்று {details.get('time', '')} மணிக்கு பதிவு செய்யப்பட்டது."
            },
            "cancel": {
                "en": f"Your appointment on {details.get('date', '')} has been cancelled.",
                "hi": f"{details.get('date', '')} की आपकी अपॉइंटमेंट कैंसिल कर दी गई है।",
                "ta": f"{details.get('date', '')} அன்று உங்கள் சந்திப்பு ரத்து செய்யப்பட்டது."
            },
            "reschedule": {
                "en": f"Your appointment has been rescheduled to {details.get('new_date', '')} at {details.get('new_time', '')}.",
                "hi": f"आपकी अपॉइंटमेंट {details.get('new_date', '')} को {details.get('new_time', '')} पर रीशेड्यूल हो गई है।",
                "ta": f"உங்கள் சந்திப்பு {details.get('new_date', '')} அன்று {details.get('new_time', '')} மணிக்கு மறுதிட்டமிடப்பட்டது."
            }
        }
        
        action_confirmations = confirmations.get(action, {})
        return action_confirmations.get(language, action_confirmations.get("en", "Action completed successfully."))
