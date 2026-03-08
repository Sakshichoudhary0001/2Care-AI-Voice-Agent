import { useState, useCallback, useRef, useEffect } from 'react';
import { Message, Language, Appointment, LANGUAGES } from '@/types';
import { MessageList } from './MessageList';
import { VoiceRecorder } from './VoiceRecorder';
import { LanguageSelector } from './LanguageSelector';
import { AppointmentCard } from './AppointmentCard';
import { Send, X } from 'lucide-react';
import clsx from 'clsx';

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}
interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
  onend: ((this: SpeechRecognition, ev: Event) => void) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
  start(): void;
  stop(): void;
}
declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface VoiceChatProps {
  sessionId: string;
}

// Simple responses for demo mode
const DEMO_RESPONSES: Record<Language, Record<string, string>> = {
  en: {
    default: "I understand you'd like help with an appointment. Could you please tell me which doctor or specialty you're looking for?",
    greeting: "Hello! Welcome to 2Care.ai. How can I assist you with booking an appointment today?",
    doctor: "We have several doctors available. Dr. Sharma specializes in General Medicine, Dr. Patel in Cardiology, and Dr. Kumar in Orthopedics. Which specialty interests you?",
    book: "I can help you book an appointment. Please provide your preferred date and time, and I'll check availability for you.",
    cancel: "I understand you want to cancel an appointment. Could you please provide the appointment details or your phone number?",
    time: "Our doctors are available Monday to Saturday, 9 AM to 6 PM. What time works best for you?",
    thanks: "You're welcome! Is there anything else I can help you with?",
  },
  hi: {
    default: "मैं समझता हूं कि आप अपॉइंटमेंट के लिए मदद चाहते हैं। कृपया बताएं कि आप किस डॉक्टर या विशेषज्ञता की तलाश में हैं?",
    greeting: "नमस्ते! 2Care.ai में आपका स्वागत है। आज मैं आपकी अपॉइंटमेंट बुक करने में कैसे मदद कर सकता हूं?",
    doctor: "हमारे पास कई डॉक्टर उपलब्ध हैं। डॉ. शर्मा जनरल मेडिसिन में, डॉ. पटेल कार्डियोलॉजी में विशेषज्ञ हैं।",
    book: "मैं आपकी अपॉइंटमेंट बुक करने में मदद कर सकता हूं। कृपया अपनी पसंदीदा तारीख और समय बताएं।",
    cancel: "मैं समझता हूं कि आप अपॉइंटमेंट रद्द करना चाहते हैं। कृपया विवरण दें।",
    time: "हमारे डॉक्टर सोमवार से शनिवार, सुबह 9 बजे से शाम 6 बजे तक उपलब्ध हैं।",
    thanks: "आपका स्वागत है! क्या कुछ और मदद चाहिए?",
  },
  ta: {
    default: "நீங்கள் சந்திப்புக்கு உதவி வேண்டும் என்று புரிகிறது. எந்த மருத்துவர் தேடுகிறீர்கள்?",
    greeting: "வணக்கம்! 2Care.ai க்கு வரவேற்கிறோம். சந்திப்பு முன்பதிவு செய்ய எப்படி உதவ முடியும்?",
    doctor: "எங்களிடம் பல மருத்துவர்கள் உள்ளனர். டாக்டர் ஷர்மா பொது மருத்துவம், டாக்டர் படேல் இதயவியல் நிபுணர்கள்.",
    book: "சந்திப்பு முன்பதிவு செய்ய உதவ முடியும். உங்கள் விருப்பமான தேதி மற்றும் நேரத்தை சொல்லுங்கள்.",
    cancel: "சந்திப்பை ரத்து செய்ய விரும்புகிறீர்கள் என்று புரிகிறது. விவரங்கள் தரவும்.",
    time: "எங்கள் மருத்துவர்கள் திங்கள் முதல் சனி வரை, காலை 9 மணி முதல் மாலை 6 மணி வரை கிடைக்கும்.",
    thanks: "நன்றி! வேறு ஏதாவது உதவி தேவையா?",
  },
};

function getResponse(text: string, language: Language): string {
  const responses = DEMO_RESPONSES[language];
  const lowerText = text.toLowerCase();
  
  if (lowerText.includes('hello') || lowerText.includes('hi') || lowerText.includes('hey') || lowerText.includes('नमस्ते') || lowerText.includes('வணக்கம்')) {
    return responses.greeting;
  }
  if (lowerText.includes('doctor') || lowerText.includes('specialist') || lowerText.includes('डॉक्टर') || lowerText.includes('மருத்துவர்')) {
    return responses.doctor;
  }
  if (lowerText.includes('book') || lowerText.includes('schedule') || lowerText.includes('appointment') || lowerText.includes('बुक') || lowerText.includes('முன்பதிவு')) {
    return responses.book;
  }
  if (lowerText.includes('cancel') || lowerText.includes('रद्द') || lowerText.includes('ரத்து')) {
    return responses.cancel;
  }
  if (lowerText.includes('time') || lowerText.includes('when') || lowerText.includes('available') || lowerText.includes('समय') || lowerText.includes('நேரம்')) {
    return responses.time;
  }
  if (lowerText.includes('thank') || lowerText.includes('धन्यवाद') || lowerText.includes('நன்றி')) {
    return responses.thanks;
  }
  return responses.default;
}

export function VoiceChat({ sessionId: _sessionId }: VoiceChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [language, setLanguage] = useState<Language>('en');
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [currentAppointment, setCurrentAppointment] = useState<Appointment | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const addMessage = useCallback((type: Message['type'], content: string, audioUrl?: string) => {
    const message: Message = {
      id: generateId(),
      type,
      content,
      timestamp: new Date(),
      language,
      audioUrl,
    };
    setMessages((prev) => [...prev, message]);
  }, [language]);

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
    }
  }, []);

  useEffect(() => {
    const welcomeMessages: Record<Language, string> = {
      en: "Hello! I'm your 2Care.ai assistant. How can I help you with your appointment today?",
      hi: "नमस्ते! मैं आपका 2Care.ai सहायक हूं। आज मैं आपकी अपॉइंटमेंट में कैसे मदद कर सकता हूं?",
      ta: "வணக்கம்! நான் உங்கள் 2Care.ai உதவியாளர். இன்று உங்கள் சந்திப்பில் நான் எவ்வாறு உதவ முடியும்?",
    };
    addMessage('assistant', welcomeMessages[language]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const processUserInput = useCallback((userText: string) => {
    addMessage('user', userText);
    setIsProcessing(true);
    
    setTimeout(() => {
      const response = getResponse(userText, language);
      addMessage('assistant', response);
      setIsProcessing(false);
    }, 600 + Math.random() * 400);
  }, [language, addMessage]);

  const handleLanguageChange = (newLanguage: Language) => {
    setLanguage(newLanguage);
    addMessage('system', `Language changed to ${LANGUAGES[newLanguage].name}`);
  };

  const handleSendText = useCallback(() => {
    if (!textInput.trim() || isProcessing) return;
    processUserInput(textInput.trim());
    setTextInput('');
  }, [textInput, isProcessing, processUserInput]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  const playAudio = (audioUrl: string) => {
    if (audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play().catch(console.error);
    }
  };

  const toggleRecording = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      addMessage('system', 'Voice recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
      return;
    }

    const recognition = recognitionRef.current;
    if (!recognition) return;

    // Set language for recognition
    const langMap: Record<Language, string> = { en: 'en-US', hi: 'hi-IN', ta: 'ta-IN' };
    recognition.lang = langMap[language];

    recognition.onstart = () => setIsRecording(true);
    recognition.onend = () => setIsRecording(false);
    recognition.onerror = (event) => {
      setIsRecording(false);
      if (event.error === 'no-speech') {
        addMessage('system', 'No speech detected. Please try again.');
      } else if (event.error === 'not-allowed') {
        addMessage('system', 'Microphone access denied. Please allow microphone permission.');
      }
    };
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript.trim()) {
        processUserInput(transcript.trim());
      }
    };

    recognition.start();
  }, [isRecording, language, addMessage, processUserInput]);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-care-blue to-care-green flex items-center justify-center">
            <span className="text-white font-bold text-lg">2C</span>
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">2Care.ai Assistant</h1>
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full" />
              Demo Mode - Ready
            </p>
          </div>
        </div>
        <LanguageSelector language={language} onChange={handleLanguageChange} disabled={isProcessing} />
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col">
          <MessageList messages={messages} isProcessing={isProcessing} onPlayAudio={playAudio} />

          <div className="bg-white border-t border-gray-200 p-4">
            <div className="flex items-center gap-2">
              <VoiceRecorder isRecording={isRecording} isProcessing={isProcessing} audioLevel={0} hasPermission={true} onToggle={toggleRecording} disabled={isProcessing} />
              <input
                ref={inputRef}
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={language === 'en' ? 'Type or tap mic to speak...' : language === 'hi' ? 'टाइप करें या माइक दबाएं...' : 'தட்டச்சு செய்யவும் அல்லது மைக்கைத் தட்டவும்...'}
                className="flex-1 px-4 py-2 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-care-blue focus:border-transparent"
                disabled={isProcessing}
                autoFocus
              />
              <button
                onClick={handleSendText}
                disabled={!textInput.trim() || isProcessing}
                className={clsx('w-10 h-10 rounded-full flex items-center justify-center transition-colors', textInput.trim() && !isProcessing ? 'bg-care-blue text-white hover:bg-blue-700' : 'bg-gray-100 text-gray-400')}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {currentAppointment && (
          <div className="w-80 border-l border-gray-200 bg-white p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900">Your Appointment</h2>
              <button onClick={() => setCurrentAppointment(null)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <AppointmentCard appointment={currentAppointment} onCancel={() => { addMessage('user', 'I want to cancel this appointment'); setCurrentAppointment(null); }} />
          </div>
        )}
      </div>

      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
