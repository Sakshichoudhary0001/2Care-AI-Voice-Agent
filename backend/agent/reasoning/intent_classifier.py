"""
Intent Classifier
Classifies user utterances into predefined intents
Uses both rule-based patterns and LLM for fallback
"""

import re
from typing import Tuple, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Hybrid intent classifier using:
    1. Rule-based pattern matching (fast, high precision)
    2. LLM fallback (for ambiguous cases)
    """
    
    # Intent patterns for each language
    PATTERNS = {
        "book_appointment": {
            "en": [
                r"\b(book|schedule|make|set up|arrange|get)\b.*(appointment|booking|slot|visit|consultation)",
                r"\bwant to see\b.*doctor",
                r"\bneed an? appointment\b",
                r"\bwant to (visit|consult|meet)\b",
                r"\bavailable.*slot\b",
            ],
            "hi": [
                r"\b(बुक|अपॉइंटमेंट लें|मिलना है|दिखाना है)\b",
                r"\bडॉक्टर से मिलना\b",
                r"\bअपॉइंटमेंट (चाहिए|कराना है)\b",
            ],
            "ta": [
                r"\b(பதிவு|சந்திப்பு)\b",
                r"\bமருத்துவரை பார்க்க\b",
                r"\bஅப்பாயின்ட்மென்ட்\b",
            ]
        },
        "cancel_appointment": {
            "en": [
                r"\b(cancel|delete|remove)\b.*(appointment|booking)",
                r"\bdon'?t want\b.*appointment",
                r"\bcan'?t (come|make it|attend)\b",
            ],
            "hi": [
                r"\b(कैंसिल|रद्द)\b.*अपॉइंटमेंट",
                r"\bअपॉइंटमेंट.*कैंसिल\b",
                r"\bनहीं आ (पाऊंगा|सकता)\b",
            ],
            "ta": [
                r"\b(ரத்து|கேன்சல்)\b",
                r"\bசந்திப்பை ரத்து\b",
            ]
        },
        "reschedule_appointment": {
            "en": [
                r"\b(reschedule|change|move|postpone|shift)\b.*(appointment|booking|date|time)",
                r"\bdifferent (time|date|day)\b",
                r"\bchange.*to\b",
            ],
            "hi": [
                r"\b(रीशेड्यूल|बदलना है|आगे करना)\b",
                r"\bसमय बदलना\b",
                r"\bदूसरी तारीख\b",
            ],
            "ta": [
                r"\b(மாற்ற|மறுதிட்டமிட)\b",
                r"\bநேரம் மாற்ற\b",
            ]
        },
        "check_availability": {
            "en": [
                r"\b(check|see|know|when|what).*(available|availability|free|open)",
                r"\bwhen (is|can I see)\b.*doctor",
                r"\bavailable\b.*\b(slot|time|date)\b",
            ],
            "hi": [
                r"\bकब (खाली|फ्री|उपलब्ध)\b",
                r"\bउपलब्धता (देखें|चेक करें)\b",
            ],
            "ta": [
                r"\bகிடைக்கும்\b",
                r"\bநேரம் இருக்கிறதா\b",
            ]
        },
        "get_appointment_details": {
            "en": [
                r"\b(my|check|view|see)\b.*(appointment|booking)s?\b",
                r"\bwhen.*my appointment\b",
                r"\bappointment (details|information|info)\b",
            ],
            "hi": [
                r"\bमेरी अपॉइंटमेंट\b",
                r"\bअपॉइंटमेंट (का|की) (जानकारी|डिटेल)\b",
            ],
            "ta": [
                r"\bஎன் சந்திப்பு\b",
                r"\bசந்திப்பு விவரங்கள்\b",
            ]
        },
        "list_doctors": {
            "en": [
                r"\b(list|show|tell|which|all)\b.*doctors?\b",
                r"\bwho (are|is)\b.*doctors?\b",
                r"\bdoctors?.*available\b",
            ],
            "hi": [
                r"\bडॉक्टर (कौन|कौन-कौन) हैं\b",
                r"\bसभी डॉक्टर\b",
            ],
            "ta": [
                r"\bமருத்துவர்கள் யார்\b",
                r"\bஎல்லா மருத்துவர்கள்\b",
            ]
        },
        "get_doctor_info": {
            "en": [
                r"\b(tell|about|info|information|details)\b.*doctor",
                r"\bdoctor.*(specialization|specialty|experience)\b",
                r"\bwho is (dr|doctor)\b",
            ],
            "hi": [
                r"\bडॉक्टर (के बारे में|की जानकारी)\b",
            ],
            "ta": [
                r"\bமருத்துவர் பற்றி\b",
            ]
        },
        "greeting": {
            "en": [
                r"^\s*(hi|hello|hey|good morning|good afternoon|good evening|namaste)\s*$",
                r"^\s*(hi|hello)\b",
            ],
            "hi": [
                r"^\s*(नमस्ते|हेलो|हाय|नमस्कार)\b",
            ],
            "ta": [
                r"^\s*(வணக்கம்|ஹலோ)\b",
            ]
        },
        "goodbye": {
            "en": [
                r"\b(bye|goodbye|thank you|thanks|that'?s all|done)\b",
                r"^\s*(ok|okay|alright).*thanks?\b",
            ],
            "hi": [
                r"\b(धन्यवाद|अलविदा|बस इतना ही)\b",
            ],
            "ta": [
                r"\b(நன்றி|போய் வருகிறேன்)\b",
            ]
        },
        "help": {
            "en": [
                r"\b(help|assist|what can you do|options)\b",
                r"^\s*\?\s*$",
            ],
            "hi": [
                r"\b(मदद|सहायता|क्या कर सकते हो)\b",
            ],
            "ta": [
                r"\b(உதவி|என்ன செய்ய முடியும்)\b",
            ]
        }
    }
    
    def __init__(self):
        # Compile patterns for efficiency
        self.compiled_patterns: Dict[str, Dict[str, List[re.Pattern]]] = {}
        for intent, lang_patterns in self.PATTERNS.items():
            self.compiled_patterns[intent] = {}
            for lang, patterns in lang_patterns.items():
                self.compiled_patterns[intent][lang] = [
                    re.compile(p, re.IGNORECASE | re.UNICODE) 
                    for p in patterns
                ]
    
    async def classify(
        self,
        text: str,
        conversation_history: List[Dict] = None,
        language: str = "en"
    ) -> Tuple[str, float]:
        """
        Classify the intent of the given text.
        Returns (intent, confidence) tuple.
        """
        text = text.strip().lower()
        
        # Try rule-based classification first
        intent, confidence = self._rule_based_classify(text, language)
        
        if confidence >= 0.8:
            return intent, confidence
        
        # Check conversation context for continuation
        if conversation_history and len(conversation_history) >= 2:
            context_intent = self._get_context_intent(conversation_history)
            if context_intent:
                # User might be providing additional info for previous intent
                return context_intent, 0.7
        
        # Low confidence - could use LLM here for better classification
        if confidence < 0.6:
            return "clarification", confidence
        
        return intent, confidence
    
    def _rule_based_classify(self, text: str, language: str) -> Tuple[str, float]:
        """Apply rule-based pattern matching"""
        best_intent = "out_of_scope"
        best_confidence = 0.0
        
        for intent, lang_patterns in self.compiled_patterns.items():
            # Check patterns for specified language
            patterns = lang_patterns.get(language, [])
            # Also check English patterns as fallback
            if language != "en":
                patterns = patterns + lang_patterns.get("en", [])
            
            for pattern in patterns:
                if pattern.search(text):
                    # Calculate confidence based on match quality
                    confidence = 0.9 if pattern.pattern.startswith("^") else 0.85
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
        
        return best_intent, best_confidence
    
    def _get_context_intent(self, history: List[Dict]) -> Optional[str]:
        """Extract the current intent from conversation history"""
        # Look at the last agent message to understand context
        for turn in reversed(history):
            if turn.get("role") == "assistant":
                content = turn.get("content", "").lower()
                
                # Check if agent asked for specific slots
                if any(q in content for q in ["which doctor", "what date", "what time"]):
                    return "book_appointment"
                if "new date" in content or "reschedule" in content:
                    return "reschedule_appointment"
                if "cancel" in content:
                    return "cancel_appointment"
                
                break
        
        return None
