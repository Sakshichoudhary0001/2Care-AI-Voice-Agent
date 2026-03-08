// Type definitions for 2Care.ai Frontend

export type Language = 'en' | 'hi' | 'ta';

export interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  language?: Language;
  audioUrl?: string;
}

export interface Appointment {
  id: string;
  patientName: string;
  doctorName: string;
  specialty: string;
  date: string;
  time: string;
  status: 'scheduled' | 'confirmed' | 'cancelled' | 'completed';
  notes?: string;
}

export interface Doctor {
  id: string;
  name: string;
  specialty: string;
  languages: Language[];
  available: boolean;
  nextAvailable?: string;
  imageUrl?: string;
}

export interface Patient {
  id: string;
  fullName: string;
  phoneNumber: string;
  email?: string;
  preferredLanguage: Language;
}

export interface SlotInfo {
  date: string;
  time: string;
  available: boolean;
  doctorId: string;
}

export interface ConversationState {
  sessionId: string;
  intent?: string;
  slots: Record<string, string>;
  stage: 'greeting' | 'collecting_info' | 'confirming' | 'completed';
}

export interface WebSocketMessage {
  type: 'audio' | 'text' | 'transcript' | 'response' | 'error' | 'status';
  data: unknown;
  language?: Language;
  sessionId?: string;
}

export interface VoiceState {
  isListening: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  audioLevel: number;
}

export const LANGUAGES: Record<Language, { name: string; nativeName: string }> = {
  en: { name: 'English', nativeName: 'English' },
  hi: { name: 'Hindi', nativeName: 'हिंदी' },
  ta: { name: 'Tamil', nativeName: 'தமிழ்' },
};

export const SPECIALTIES = [
  'General Medicine',
  'Cardiology',
  'Dermatology',
  'Orthopedics',
  'Pediatrics',
  'Gynecology',
  'Neurology',
  'ENT',
  'Ophthalmology',
  'Psychiatry',
];
