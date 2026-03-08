"""
Slot Filler
Extracts structured slot values from user utterances
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date, time
import logging

logger = logging.getLogger(__name__)


class SlotFiller:
    """
    Extracts slot values from user utterances using:
    1. Pattern matching for dates, times, numbers
    2. Entity recognition for names, specialties
    """
    
    # Specialty mappings (including common variations)
    SPECIALTIES = {
        # English
        "cardiology": "Cardiology",
        "cardiologist": "Cardiology",
        "heart": "Cardiology",
        "heart doctor": "Cardiology",
        "pediatrics": "Pediatrics",
        "pediatrician": "Pediatrics",
        "child specialist": "Pediatrics",
        "children": "Pediatrics",
        "general medicine": "General Medicine",
        "general physician": "General Medicine",
        "gp": "General Medicine",
        "orthopedics": "Orthopedics",
        "orthopedic": "Orthopedics",
        "bone": "Orthopedics",
        "bone doctor": "Orthopedics",
        "dermatology": "Dermatology",
        "dermatologist": "Dermatology",
        "skin": "Dermatology",
        "skin specialist": "Dermatology",
        "ent": "ENT",
        "ear nose throat": "ENT",
        "gynecology": "Gynecology",
        "gynecologist": "Gynecology",
        "women": "Gynecology",
        "neurology": "Neurology",
        "neurologist": "Neurology",
        "brain": "Neurology",
        # Hindi
        "दिल": "Cardiology",
        "हृदय": "Cardiology",
        "बच्चों के": "Pediatrics",
        "हड्डी": "Orthopedics",
        "त्वचा": "Dermatology",
        # Tamil
        "இதயம்": "Cardiology",
        "குழந்தை": "Pediatrics",
        "எலும்பு": "Orthopedics",
        "தோல்": "Dermatology",
    }
    
    # Time period mappings
    TIME_PERIODS = {
        "morning": (time(9, 0), time(12, 0)),
        "afternoon": (time(12, 0), time(17, 0)),
        "evening": (time(17, 0), time(20, 0)),
        "सुबह": (time(9, 0), time(12, 0)),
        "दोपहर": (time(12, 0), time(17, 0)),
        "शाम": (time(17, 0), time(20, 0)),
        "காலை": (time(9, 0), time(12, 0)),
        "மதியம்": (time(12, 0), time(17, 0)),
        "மாலை": (time(17, 0), time(20, 0)),
    }
    
    # Day name mappings
    DAY_NAMES = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1, "tues": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3, "thurs": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6,
        # Hindi
        "सोमवार": 0, "मंगलवार": 1, "बुधवार": 2,
        "गुरुवार": 3, "शुक्रवार": 4, "शनिवार": 5, "रविवार": 6,
        # Tamil
        "திங்கள்": 0, "செவ்வாய்": 1, "புதன்": 2,
        "வியாழன்": 3, "வெள்ளி": 4, "சனி": 5, "ஞாயிறு": 6,
    }
    
    # Relative day mappings
    RELATIVE_DAYS = {
        "today": 0, "आज": 0, "இன்று": 0,
        "tomorrow": 1, "कल": 1, "நாளை": 1,
        "day after tomorrow": 2, "परसों": 2, "நாளை மறுநாள்": 2,
        "next week": 7,
    }
    
    def __init__(self):
        self.today = date.today()
    
    async def extract(
        self,
        text: str,
        intent: str,
        existing_slots: Dict[str, Any],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Extract slot values from text based on intent.
        Returns dictionary of extracted slots.
        """
        text = text.strip()
        extracted = {}
        
        # Extract based on intent requirements
        if intent in ["book_appointment", "check_availability"]:
            extracted.update(self._extract_doctor_or_specialty(text))
            extracted.update(self._extract_date(text))
            extracted.update(self._extract_time(text))
            extracted.update(self._extract_reason(text))
        
        elif intent in ["cancel_appointment", "get_appointment_details"]:
            extracted.update(self._extract_appointment_identifier(text, existing_slots))
        
        elif intent == "reschedule_appointment":
            extracted.update(self._extract_appointment_identifier(text, existing_slots))
            # Check for new date/time
            new_extracted = self._extract_date(text)
            if new_extracted.get("date"):
                extracted["new_date"] = new_extracted["date"]
            new_time = self._extract_time(text)
            if new_time.get("time"):
                extracted["new_time"] = new_time["time"]
        
        elif intent in ["list_doctors", "get_doctor_info"]:
            extracted.update(self._extract_doctor_or_specialty(text))
        
        return extracted
    
    def _extract_doctor_or_specialty(self, text: str) -> Dict[str, Any]:
        """Extract doctor name or specialty from text"""
        text_lower = text.lower()
        result = {}
        
        # Check for specialty keywords
        for keyword, specialty in self.SPECIALTIES.items():
            if keyword in text_lower:
                result["doctor_name_or_specialty"] = specialty
                result["specialty"] = specialty
                return result
        
        # Try to extract doctor name (pattern: "Dr. Name" or "Doctor Name")
        doctor_pattern = r"(?:dr\.?|doctor)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)"
        match = re.search(doctor_pattern, text, re.IGNORECASE)
        if match:
            result["doctor_name_or_specialty"] = match.group(1).strip()
            result["doctor_name"] = match.group(1).strip()
        
        return result
    
    def _extract_date(self, text: str) -> Dict[str, Any]:
        """Extract date from text"""
        text_lower = text.lower()
        result = {}
        
        # Check relative days first
        for phrase, days_offset in self.RELATIVE_DAYS.items():
            if phrase in text_lower:
                target_date = self.today + timedelta(days=days_offset)
                result["date"] = target_date.strftime("%Y-%m-%d")
                return result
        
        # Check day names (e.g., "this Monday", "next Friday")
        for day_name, day_num in self.DAY_NAMES.items():
            if day_name in text_lower:
                days_ahead = day_num - self.today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                if "next" in text_lower:
                    days_ahead += 7
                target_date = self.today + timedelta(days=days_ahead)
                result["date"] = target_date.strftime("%Y-%m-%d")
                return result
        
        # Try to parse explicit dates
        date_patterns = [
            # DD/MM/YYYY or DD-MM-YYYY
            (r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", "%d-%m-%Y"),
            # YYYY-MM-DD
            (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
            # Month DD, YYYY or DD Month YYYY
            (r"(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*", None),
            (r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?", None),
        ]
        
        for pattern, date_format in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if date_format:
                        date_str = "-".join(match.groups())
                        parsed = datetime.strptime(date_str, date_format)
                        result["date"] = parsed.strftime("%Y-%m-%d")
                    else:
                        # Handle month name patterns
                        groups = match.groups()
                        month_names = {
                            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
                        }
                        if groups[0].isdigit():
                            day = int(groups[0])
                            month = month_names.get(groups[1][:3], 1)
                        else:
                            month = month_names.get(groups[0][:3], 1)
                            day = int(groups[1])
                        year = self.today.year
                        if date(year, month, day) < self.today:
                            year += 1
                        result["date"] = f"{year}-{month:02d}-{day:02d}"
                    return result
                except ValueError:
                    continue
        
        return result
    
    def _extract_time(self, text: str) -> Dict[str, Any]:
        """Extract time from text"""
        text_lower = text.lower()
        result = {}
        
        # Check time periods
        for period, (start, end) in self.TIME_PERIODS.items():
            if period in text_lower:
                result["time"] = start.strftime("%H:%M")
                result["time_period"] = period
                return result
        
        # Try to parse explicit times
        time_patterns = [
            # 10 AM, 2:30 PM, etc.
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)",
            # 24-hour format
            r"(\d{1,2}):(\d{2})",
            # "at 10", "at 2"
            r"at\s+(\d{1,2})\b",
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                
                # Handle AM/PM
                if len(groups) > 2 and groups[2]:
                    if groups[2] == "pm" and hour < 12:
                        hour += 12
                    elif groups[2] == "am" and hour == 12:
                        hour = 0
                elif hour < 8:  # Assume PM for small numbers without AM/PM
                    hour += 12
                
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    result["time"] = f"{hour:02d}:{minute:02d}"
                    return result
        
        return result
    
    def _extract_reason(self, text: str) -> Dict[str, Any]:
        """Extract appointment reason from text"""
        result = {}
        
        # Common reason phrases
        reason_patterns = [
            r"for\s+(?:a\s+)?(.+?)(?:\.|$)",
            r"because\s+(?:of\s+)?(.+?)(?:\.|$)",
            r"having\s+(.+?)(?:\.|$)",
            r"suffering\s+from\s+(.+?)(?:\.|$)",
        ]
        
        for pattern in reason_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                reason = match.group(1).strip()
                if len(reason) > 3 and len(reason) < 200:
                    result["reason"] = reason
                    break
        
        return result
    
    def _extract_appointment_identifier(
        self,
        text: str,
        existing_slots: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract appointment identifier (ID or date reference)"""
        result = {}
        
        # First try to get a date
        date_slots = self._extract_date(text)
        if date_slots.get("date"):
            result["appointment_id_or_date"] = date_slots["date"]
            return result
        
        # Try to find appointment ID/number
        id_pattern = r"(?:appointment|booking)?\s*(?:number|id|#)?\s*([A-Za-z0-9-]{6,})"
        match = re.search(id_pattern, text, re.IGNORECASE)
        if match:
            result["appointment_id_or_date"] = match.group(1)
        
        return result
