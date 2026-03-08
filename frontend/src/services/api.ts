import { Appointment, Doctor, Patient, SlotInfo, Language } from '@/types';

const API_BASE = '/api/v1';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  return response.json();
}

// ============================================================================
// Appointment APIs
// ============================================================================

export async function getAppointments(
  patientId?: string,
  status?: string
): Promise<Appointment[]> {
  const params = new URLSearchParams();
  if (patientId) params.append('patient_id', patientId);
  if (status) params.append('status', status);
  
  return fetchApi<Appointment[]>(`/appointments?${params}`);
}

export async function getAppointment(id: string): Promise<Appointment> {
  return fetchApi<Appointment>(`/appointments/${id}`);
}

export async function createAppointment(data: {
  patientId: string;
  doctorId: string;
  date: string;
  time: string;
  notes?: string;
}): Promise<Appointment> {
  return fetchApi<Appointment>('/appointments', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAppointment(
  id: string,
  data: Partial<Appointment>
): Promise<Appointment> {
  return fetchApi<Appointment>(`/appointments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function cancelAppointment(id: string): Promise<void> {
  return fetchApi<void>(`/appointments/${id}/cancel`, {
    method: 'POST',
  });
}

// ============================================================================
// Doctor APIs
// ============================================================================

export async function getDoctors(
  specialty?: string,
  language?: Language
): Promise<Doctor[]> {
  const params = new URLSearchParams();
  if (specialty) params.append('specialty', specialty);
  if (language) params.append('language', language);
  
  return fetchApi<Doctor[]>(`/doctors?${params}`);
}

export async function getDoctor(id: string): Promise<Doctor> {
  return fetchApi<Doctor>(`/doctors/${id}`);
}

export async function getDoctorSlots(
  doctorId: string,
  date: string
): Promise<SlotInfo[]> {
  return fetchApi<SlotInfo[]>(`/doctors/${doctorId}/slots?date=${date}`);
}

// ============================================================================
// Patient APIs
// ============================================================================

export async function getPatient(id: string): Promise<Patient> {
  return fetchApi<Patient>(`/patients/${id}`);
}

export async function getPatientByPhone(phone: string): Promise<Patient | null> {
  try {
    return await fetchApi<Patient>(`/patients/phone/${phone}`);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      return null;
    }
    throw e;
  }
}

export async function createPatient(data: {
  fullName: string;
  phoneNumber: string;
  email?: string;
  preferredLanguage?: Language;
}): Promise<Patient> {
  return fetchApi<Patient>('/patients', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updatePatient(
  id: string,
  data: Partial<Patient>
): Promise<Patient> {
  return fetchApi<Patient>(`/patients/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ============================================================================
// Health Check
// ============================================================================

export async function checkHealth(): Promise<{ status: string }> {
  return fetchApi<{ status: string }>('/health');
}

// ============================================================================
// Text Chat API (fallback when voice is unavailable)
// ============================================================================

export async function sendTextMessage(
  sessionId: string,
  message: string,
  language: Language
): Promise<{ response: string; audioUrl?: string }> {
  return fetchApi<{ response: string; audioUrl?: string }>('/chat/text', {
    method: 'POST',
    body: JSON.stringify({ sessionId, message, language }),
  });
}
