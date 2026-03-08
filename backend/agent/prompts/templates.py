"""
Multilingual Prompt Templates
Supports: English (en), Hindi (hi), Tamil (ta)
"""

from typing import Dict, Any, Optional


class PromptTemplates:
    """Manages all prompt templates for the voice AI agent"""
    
    # ==========================================================================
    # SLOT QUESTIONS - Questions to collect missing information
    # ==========================================================================
    
    SLOT_QUESTIONS = {
        "doctor_name_or_specialty": {
            "en": "Which doctor would you like to see, or what type of specialist do you need?",
            "hi": "आप किस डॉक्टर से मिलना चाहते हैं, या आपको किस विशेषज्ञ की जरूरत है?",
            "ta": "நீங்கள் எந்த மருத்துவரைப் பார்க்க விரும்புகிறீர்கள், அல்லது என்ன வகையான நிபுணர் தேவை?"
        },
        "date": {
            "en": "What date would work for you?",
            "hi": "आपके लिए कौन सी तारीख सही रहेगी?",
            "ta": "உங்களுக்கு எந்த தேதி வசதியாக இருக்கும்?"
        },
        "time": {
            "en": "What time would you prefer? Morning, afternoon, or evening?",
            "hi": "आप किस समय पसंद करेंगे? सुबह, दोपहर, या शाम?",
            "ta": "எந்த நேரம் விரும்புகிறீர்கள்? காலை, மதியம், அல்லது மாலை?"
        },
        "appointment_id_or_date": {
            "en": "Can you tell me the date of your appointment or the appointment number?",
            "hi": "क्या आप मुझे अपनी अपॉइंटमेंट की तारीख या नंबर बता सकते हैं?",
            "ta": "உங்கள் சந்திப்பு தேதி அல்லது சந்திப்பு எண்ணைச் சொல்ல முடியுமா?"
        },
        "new_date": {
            "en": "What new date would you like to reschedule to?",
            "hi": "आप किस नई तारीख पर रीशेड्यूल करना चाहेंगे?",
            "ta": "எந்த புதிய தேதிக்கு மறுதிட்டமிட விரும்புகிறீர்கள்?"
        },
        "new_time": {
            "en": "And what time on the new date?",
            "hi": "और नई तारीख पर किस समय?",
            "ta": "புதிய தேதியில் என்ன நேரம்?"
        },
        "doctor_name": {
            "en": "What is the doctor's name?",
            "hi": "डॉक्टर का नाम क्या है?",
            "ta": "மருத்துவரின் பெயர் என்ன?"
        },
        "specialty": {
            "en": "What specialty or department are you looking for?",
            "hi": "आप किस विशेषज्ञता या विभाग की तलाश कर रहे हैं?",
            "ta": "நீங்கள் எந்த நிபுணத்துவம் அல்லது துறையைத் தேடுகிறீர்கள்?"
        },
        "reason": {
            "en": "May I know the reason for your visit?",
            "hi": "क्या मैं आपकी विजिट का कारण जान सकता हूं?",
            "ta": "உங்கள் வருகையின் காரணத்தை அறியலாமா?"
        }
    }
    
    # ==========================================================================
    # GREETINGS AND COMMON RESPONSES
    # ==========================================================================
    
    GREETINGS = {
        "en": "Hello! Welcome to 2Care.ai. I can help you book, reschedule, or cancel appointments. How can I assist you today?",
        "hi": "नमस्ते! 2Care.ai में आपका स्वागत है। मैं आपकी अपॉइंटमेंट बुक करने, रीशेड्यूल करने या कैंसिल करने में मदद कर सकता हूं। आज मैं आपकी कैसे सहायता कर सकता हूं?",
        "ta": "வணக்கம்! 2Care.ai க்கு வரவேற்கிறோம். சந்திப்புகளை பதிவு செய்ய, மறுதிட்டமிட அல்லது ரத்து செய்ய நான் உதவ முடியும். இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?"
    }
    
    GOODBYES = {
        "en": "Thank you for calling 2Care.ai. Take care and have a great day!",
        "hi": "2Care.ai को कॉल करने के लिए धन्यवाद। अपना ख्याल रखें और आपका दिन शुभ हो!",
        "ta": "2Care.ai ஐ அழைத்ததற்கு நன்றி. கவனமாக இருங்கள், நல்ல நாள் வாழ்த்துக்கள்!"
    }
    
    HELP_MESSAGES = {
        "en": "I can help you with: booking a new appointment, checking doctor availability, rescheduling an existing appointment, or cancelling an appointment. What would you like to do?",
        "hi": "मैं इनमें आपकी मदद कर सकता हूं: नई अपॉइंटमेंट बुक करना, डॉक्टर की उपलब्धता जांचना, मौजूदा अपॉइंटमेंट को रीशेड्यूल करना, या अपॉइंटमेंट कैंसिल करना। आप क्या करना चाहेंगे?",
        "ta": "நான் இவற்றில் உதவ முடியும்: புதிய சந்திப்பு பதிவு, மருத்துவர் கிடைக்கும் நேரம் சரிபார்ப்பு, இருக்கும் சந்திப்பை மறுதிட்டமிடுதல், அல்லது சந்திப்பை ரத்து செய்தல். நீங்கள் என்ன செய்ய விரும்புகிறீர்கள்?"
    }
    
    CLARIFICATION_REQUESTS = {
        "en": "I'm sorry, I didn't quite understand that. Could you please rephrase or tell me if you'd like to book, reschedule, or cancel an appointment?",
        "hi": "मुझे खेद है, मैं ठीक से समझ नहीं पाया। क्या आप कृपया दोबारा बता सकते हैं कि आप अपॉइंटमेंट बुक, रीशेड्यूल या कैंसिल करना चाहते हैं?",
        "ta": "மன்னிக்கவும், நான் சரியாக புரிந்துகொள்ளவில்லை. சந்திப்பை பதிவு செய்ய, மறுதிட்டமிட அல்லது ரத்து செய்ய விரும்புகிறீர்களா என்று மீண்டும் சொல்ல முடியுமா?"
    }
    
    OUT_OF_SCOPE = {
        "en": "I'm sorry, I can only help with appointment bookings and scheduling. For other inquiries, please speak to our front desk at extension 100.",
        "hi": "मुझे खेद है, मैं केवल अपॉइंटमेंट बुकिंग और शेड्यूलिंग में मदद कर सकता हूं। अन्य पूछताछ के लिए, कृपया एक्सटेंशन 100 पर हमारे फ्रंट डेस्क से बात करें।",
        "ta": "மன்னிக்கவும், நான் சந்திப்பு பதிவு மற்றும் திட்டமிடலில் மட்டுமே உதவ முடியும். மற்ற விசாரணைகளுக்கு, எக்ஸ்டென்ஷன் 100 இல் எங்கள் முன் மேசையுடன் பேசவும்."
    }
    
    ERROR_RESPONSES = {
        "en": "I apologize, but I encountered an issue. Let me try again. What would you like help with?",
        "hi": "मुझे खेद है, लेकिन मुझे एक समस्या आई। मैं फिर से कोशिश करता हूं। आपको किस चीज़ में मदद चाहिए?",
        "ta": "மன்னிக்கவும், ஒரு சிக்கல் ஏற்பட்டது. நான் மீண்டும் முயற்சிக்கிறேன். உங்களுக்கு எதில் உதவி தேவை?"
    }
    
    # ==========================================================================
    # RESPONSE TEMPLATES
    # ==========================================================================
    
    BOOKING_SUCCESS = {
        "en": "Great! I've booked your appointment with {doctor_name} on {date} at {time}. Your appointment number is {appointment_id}. You'll receive a confirmation SMS shortly.",
        "hi": "बढ़िया! मैंने {date} को {time} पर {doctor_name} के साथ आपकी अपॉइंटमेंट बुक कर दी है। आपका अपॉइंटमेंट नंबर {appointment_id} है। आपको जल्द ही कन्फर्मेशन SMS मिल जाएगा।",
        "ta": "{date} அன்று {time} மணிக்கு {doctor_name} உடன் உங்கள் சந்திப்பை பதிவு செய்துவிட்டேன். உங்கள் சந்திப்பு எண் {appointment_id}. உறுதிப்படுத்தல் SMS விரைவில் வரும்."
    }
    
    BOOKING_FAILED = {
        "en": "I'm sorry, that time slot is not available. Would you like me to suggest alternative times?",
        "hi": "मुझे खेद है, वह समय स्लॉट उपलब्ध नहीं है। क्या आप चाहते हैं कि मैं वैकल्पिक समय सुझाऊं?",
        "ta": "மன்னிக்கவும், அந்த நேர இடைவெளி கிடைக்கவில்லை. மாற்று நேரங்களை பரிந்துரைக்கட்டுமா?"
    }
    
    CANCELLATION_SUCCESS = {
        "en": "Your appointment on {date} at {time} with {doctor_name} has been cancelled. Is there anything else I can help you with?",
        "hi": "{date} को {time} पर {doctor_name} के साथ आपकी अपॉइंटमेंट कैंसिल कर दी गई है। क्या मैं आपकी और किसी चीज़ में मदद कर सकता हूं?",
        "ta": "{date} அன்று {time} மணிக்கு {doctor_name} உடனான உங்கள் சந்திப்பு ரத்து செய்யப்பட்டது. வேறு ஏதாவது உதவ முடியுமா?"
    }
    
    RESCHEDULE_SUCCESS = {
        "en": "Done! Your appointment has been rescheduled to {new_date} at {new_time} with {doctor_name}.",
        "hi": "हो गया! आपकी अपॉइंटमेंट {new_date} को {new_time} पर {doctor_name} के साथ रीशेड्यूल कर दी गई है।",
        "ta": "முடிந்தது! உங்கள் சந்திப்பு {new_date} அன்று {new_time} மணிக்கு {doctor_name} உடன் மறுதிட்டமிடப்பட்டது."
    }
    
    AVAILABILITY_RESPONSE = {
        "en": "{doctor_name} is available on {date} at the following times: {slots}. Which time works for you?",
        "hi": "{doctor_name} {date} को इन समयों पर उपलब्ध हैं: {slots}। आपके लिए कौन सा समय सही है?",
        "ta": "{doctor_name} {date} அன்று பின்வரும் நேரங்களில் கிடைக்கும்: {slots}. எந்த நேரம் உங்களுக்கு வசதி?"
    }
    
    NO_AVAILABILITY = {
        "en": "I'm sorry, {doctor_name} doesn't have any available slots on {date}. Would you like to check another date?",
        "hi": "मुझे खेद है, {date} को {doctor_name} के पास कोई उपलब्ध स्लॉट नहीं है। क्या आप कोई और तारीख देखना चाहेंगे?",
        "ta": "மன்னிக்கவும், {date} அன்று {doctor_name} க்கு இடைவெளி இல்லை. வேறு தேதி பார்க்க விரும்புகிறீர்களா?"
    }
    
    # ==========================================================================
    # METHODS
    # ==========================================================================
    
    def get_slot_question(self, slot_name: str, language: str = "en") -> str:
        """Get the question for a specific slot"""
        questions = self.SLOT_QUESTIONS.get(slot_name, {})
        return questions.get(language, questions.get("en", f"Please provide {slot_name}"))
    
    def get_greeting(self, language: str = "en") -> str:
        return self.GREETINGS.get(language, self.GREETINGS["en"])
    
    def get_goodbye(self, language: str = "en") -> str:
        return self.GOODBYES.get(language, self.GOODBYES["en"])
    
    def get_help(self, language: str = "en") -> str:
        return self.HELP_MESSAGES.get(language, self.HELP_MESSAGES["en"])
    
    def get_clarification_request(self, language: str = "en") -> str:
        return self.CLARIFICATION_REQUESTS.get(language, self.CLARIFICATION_REQUESTS["en"])
    
    def get_out_of_scope(self, language: str = "en") -> str:
        return self.OUT_OF_SCOPE.get(language, self.OUT_OF_SCOPE["en"])
    
    def get_error_response(self, language: str = "en") -> str:
        return self.ERROR_RESPONSES.get(language, self.ERROR_RESPONSES["en"])
    
    def format_booking_response(self, result: Dict[str, Any], language: str = "en") -> str:
        """Format booking result into a response"""
        if result.get("success"):
            template = self.BOOKING_SUCCESS.get(language, self.BOOKING_SUCCESS["en"])
            return template.format(
                doctor_name=result.get("doctor_name", "the doctor"),
                date=result.get("date", ""),
                time=result.get("time", ""),
                appointment_id=result.get("appointment_id", "")[:8]
            )
        else:
            return self.BOOKING_FAILED.get(language, self.BOOKING_FAILED["en"])
    
    def format_cancellation_response(self, result: Dict[str, Any], language: str = "en") -> str:
        """Format cancellation result into a response"""
        if result.get("success"):
            template = self.CANCELLATION_SUCCESS.get(language, self.CANCELLATION_SUCCESS["en"])
            return template.format(
                doctor_name=result.get("doctor_name", "the doctor"),
                date=result.get("date", ""),
                time=result.get("time", "")
            )
        return self.get_error_response(language)
    
    def format_reschedule_response(self, result: Dict[str, Any], language: str = "en") -> str:
        """Format reschedule result into a response"""
        if result.get("success"):
            template = self.RESCHEDULE_SUCCESS.get(language, self.RESCHEDULE_SUCCESS["en"])
            return template.format(
                doctor_name=result.get("doctor_name", "the doctor"),
                new_date=result.get("new_date", ""),
                new_time=result.get("new_time", "")
            )
        return self.get_error_response(language)
    
    def format_availability_response(self, result: Dict[str, Any], language: str = "en") -> str:
        """Format availability result into a response"""
        if result.get("slots"):
            template = self.AVAILABILITY_RESPONSE.get(language, self.AVAILABILITY_RESPONSE["en"])
            slots_str = ", ".join(result["slots"][:5])  # Show max 5 slots
            return template.format(
                doctor_name=result.get("doctor_name", "The doctor"),
                date=result.get("date", ""),
                slots=slots_str
            )
        else:
            template = self.NO_AVAILABILITY.get(language, self.NO_AVAILABILITY["en"])
            return template.format(
                doctor_name=result.get("doctor_name", "The doctor"),
                date=result.get("date", "")
            )
    
    def format_appointment_details(self, result: Dict[str, Any], language: str = "en") -> str:
        """Format appointment details"""
        if not result.get("found"):
            messages = {
                "en": "I couldn't find that appointment. Could you please verify the date or appointment number?",
                "hi": "मुझे वह अपॉइंटमेंट नहीं मिली। क्या आप कृपया तारीख या अपॉइंटमेंट नंबर वेरिफाई कर सकते हैं?",
                "ta": "அந்த சந்திப்பை கண்டுபிடிக்க முடியவில்லை. தேதி அல்லது சந்திப்பு எண்ணை சரிபார்க்க முடியுமா?"
            }
            return messages.get(language, messages["en"])
        
        templates = {
            "en": "Your appointment is with {doctor_name} on {date} at {time}. Status: {status}.",
            "hi": "आपकी अपॉइंटमेंट {doctor_name} के साथ {date} को {time} पर है। स्थिति: {status}।",
            "ta": "உங்கள் சந்திப்பு {doctor_name} உடன் {date} அன்று {time} மணிக்கு. நிலை: {status}."
        }
        template = templates.get(language, templates["en"])
        return template.format(
            doctor_name=result.get("doctor_name", ""),
            date=result.get("date", ""),
            time=result.get("time", ""),
            status=result.get("status", "scheduled")
        )
    
    def format_doctor_list(self, result: Dict[str, Any], language: str = "en") -> str:
        """Format list of doctors"""
        doctors = result.get("doctors", [])
        if not doctors:
            messages = {
                "en": "I couldn't find any doctors matching your criteria.",
                "hi": "मुझे आपके मानदंड से मेल खाने वाले कोई डॉक्टर नहीं मिले।",
                "ta": "உங்கள் அளவுகோல்களுக்கு பொருந்தும் மருத்துவர்கள் கிடைக்கவில்லை."
            }
            return messages.get(language, messages["en"])
        
        doctor_names = ", ".join([d["name"] for d in doctors[:5]])
        templates = {
            "en": f"I found these doctors: {doctor_names}. Would you like to book with any of them?",
            "hi": f"मुझे ये डॉक्टर मिले: {doctor_names}। क्या आप इनमें से किसी के साथ बुक करना चाहेंगे?",
            "ta": f"இந்த மருத்துவர்கள் கிடைத்தனர்: {doctor_names}. இவர்களில் யாருடனாவது பதிவு செய்ய விரும்புகிறீர்களா?"
        }
        return templates.get(language, templates["en"])
    
    def format_doctor_info(self, result: Dict[str, Any], language: str = "en") -> str:
        """Format doctor information"""
        if not result.get("found"):
            messages = {
                "en": "I couldn't find information about that doctor.",
                "hi": "मुझे उस डॉक्टर के बारे में जानकारी नहीं मिली।",
                "ta": "அந்த மருத்துவரைப் பற்றிய தகவல் கிடைக்கவில்லை."
            }
            return messages.get(language, messages["en"])
        
        templates = {
            "en": "{name} is a {specialty} specialist with {experience} years of experience. Consultation fee is {fee} rupees.",
            "hi": "{name} {experience} साल के अनुभव के साथ {specialty} विशेषज्ञ हैं। परामर्श शुल्क {fee} रुपये है।",
            "ta": "{name} {experience} வருட அனுபவமுள்ள {specialty} நிபுணர். ஆலோசனை கட்டணம் {fee} ரூபாய்."
        }
        template = templates.get(language, templates["en"])
        return template.format(
            name=result.get("name", ""),
            specialty=result.get("specialty", ""),
            experience=result.get("experience_years", ""),
            fee=result.get("consultation_fee", "")
        )
