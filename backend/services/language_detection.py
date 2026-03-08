"""
Language Detection Service
Detects and identifies spoken/written language
Supports: English, Hindi, Tamil
"""

import re
import logging
from typing import Optional, Tuple, List
from collections import Counter

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Language detection for multilingual support.
    Uses character-based detection for written text and
    can integrate with speech-based language ID.
    
    Supports:
    - English (en)
    - Hindi (hi) - Devanagari script
    - Tamil (ta) - Tamil script
    """
    
    # Unicode ranges for scripts
    SCRIPT_RANGES = {
        "devanagari": (0x0900, 0x097F),  # Hindi
        "tamil": (0x0B80, 0x0BFF),        # Tamil
        "latin": (0x0041, 0x007A),         # English (A-Z, a-z)
    }
    
    # Common words for each language
    COMMON_WORDS = {
        "en": {
            "the", "is", "are", "was", "were", "have", "has", "had",
            "will", "would", "could", "should", "can", "may", "might",
            "i", "you", "he", "she", "it", "we", "they", "my", "your",
            "appointment", "doctor", "book", "cancel", "reschedule",
            "time", "date", "tomorrow", "today", "morning", "evening"
        },
        "hi": {
            "है", "हैं", "था", "थे", "थी", "हो", "हुआ", "हुई",
            "मैं", "मुझे", "आप", "आपको", "वह", "यह", "हम", "वे",
            "का", "की", "के", "में", "से", "को", "पर", "और", "या",
            "अपॉइंटमेंट", "डॉक्टर", "बुक", "कैंसिल", "समय", "तारीख",
            "कल", "आज", "सुबह", "शाम", "चाहिए", "करना", "करें"
        },
        "ta": {
            "இது", "அது", "என்", "உன்", "அவர்", "அவள்", "நாம்", "நான்",
            "இருக்கிறது", "இருக்கிறார்", "இருந்தது", "வேண்டும்", "முடியும்",
            "மற்றும்", "அல்லது", "என்ன", "எப்படி", "எப்போது", "எங்கே",
            "சந்திப்பு", "மருத்துவர்", "பதிவு", "ரத்து", "நேரம்", "தேதி",
            "நாளை", "இன்று", "காலை", "மாலை"
        }
    }
    
    def __init__(self):
        self.last_detected_language = "en"
        self.confidence_threshold = 0.6
    
    async def detect(self, text: str) -> str:
        """
        Detect the language of the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code (en, hi, ta)
        """
        if not text or not text.strip():
            return self.last_detected_language
        
        # First, try script-based detection
        script_lang = self._detect_by_script(text)
        if script_lang:
            self.last_detected_language = script_lang
            return script_lang
        
        # Fall back to word-based detection
        word_lang, confidence = self._detect_by_words(text)
        if confidence >= self.confidence_threshold:
            self.last_detected_language = word_lang
            return word_lang
        
        # Return last known language if uncertain
        return self.last_detected_language
    
    def _detect_by_script(self, text: str) -> Optional[str]:
        """Detect language based on script/character set"""
        devanagari_count = 0
        tamil_count = 0
        latin_count = 0
        total_alpha = 0
        
        for char in text:
            code_point = ord(char)
            
            # Check Devanagari (Hindi)
            if self.SCRIPT_RANGES["devanagari"][0] <= code_point <= self.SCRIPT_RANGES["devanagari"][1]:
                devanagari_count += 1
                total_alpha += 1
            # Check Tamil
            elif self.SCRIPT_RANGES["tamil"][0] <= code_point <= self.SCRIPT_RANGES["tamil"][1]:
                tamil_count += 1
                total_alpha += 1
            # Check Latin (English)
            elif char.isalpha() and code_point < 128:
                latin_count += 1
                total_alpha += 1
        
        if total_alpha == 0:
            return None
        
        # Determine dominant script
        if devanagari_count / total_alpha > 0.3:
            return "hi"
        elif tamil_count / total_alpha > 0.3:
            return "ta"
        elif latin_count / total_alpha > 0.5:
            return "en"
        
        return None
    
    def _detect_by_words(self, text: str) -> Tuple[str, float]:
        """Detect language based on common words"""
        # Tokenize
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not words:
            return "en", 0.0
        
        # Count matches for each language
        scores = {}
        for lang, common_words in self.COMMON_WORDS.items():
            matches = sum(1 for word in words if word in common_words)
            scores[lang] = matches / len(words)
        
        # Get best match
        best_lang = max(scores, key=scores.get)
        best_score = scores[best_lang]
        
        return best_lang, best_score
    
    async def detect_with_confidence(self, text: str) -> Tuple[str, float]:
        """
        Detect language with confidence score.
        
        Returns:
            Tuple of (language_code, confidence)
        """
        if not text or not text.strip():
            return self.last_detected_language, 0.5
        
        # Script-based detection is high confidence
        script_lang = self._detect_by_script(text)
        if script_lang:
            self.last_detected_language = script_lang
            return script_lang, 0.95
        
        # Word-based detection
        word_lang, confidence = self._detect_by_words(text)
        if confidence >= self.confidence_threshold:
            self.last_detected_language = word_lang
        
        return word_lang, confidence
    
    def detect_code_switching(self, text: str) -> List[Tuple[str, str]]:
        """
        Detect code-switching (mixing of languages) in text.
        
        Returns:
            List of (text_segment, language) tuples
        """
        segments = []
        current_segment = []
        current_lang = None
        
        words = text.split()
        
        for word in words:
            # Detect language of this word
            word_scripts = self._get_word_scripts(word)
            
            if "devanagari" in word_scripts:
                word_lang = "hi"
            elif "tamil" in word_scripts:
                word_lang = "ta"
            else:
                word_lang = "en"
            
            if current_lang is None:
                current_lang = word_lang
            
            if word_lang == current_lang:
                current_segment.append(word)
            else:
                # Language switch detected
                if current_segment:
                    segments.append((" ".join(current_segment), current_lang))
                current_segment = [word]
                current_lang = word_lang
        
        # Add final segment
        if current_segment:
            segments.append((" ".join(current_segment), current_lang))
        
        return segments
    
    def _get_word_scripts(self, word: str) -> set:
        """Get the scripts present in a word"""
        scripts = set()
        
        for char in word:
            code_point = ord(char)
            
            if self.SCRIPT_RANGES["devanagari"][0] <= code_point <= self.SCRIPT_RANGES["devanagari"][1]:
                scripts.add("devanagari")
            elif self.SCRIPT_RANGES["tamil"][0] <= code_point <= self.SCRIPT_RANGES["tamil"][1]:
                scripts.add("tamil")
            elif char.isalpha() and code_point < 128:
                scripts.add("latin")
        
        return scripts
    
    def get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        names = {
            "en": "English",
            "hi": "Hindi",
            "ta": "Tamil"
        }
        return names.get(code, "Unknown")
