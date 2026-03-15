const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
const DEMO_ROLE_HEADER = "X-Demo-Role";
export type DemoRole = "admin" | "doctor";

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  version: string;
  database: string;
}

export interface Patient {
  id: string;
  record_number: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  email: string | null;
  phone: string | null;
  city: string | null;
  notes: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PatientListResponse {
  items: Patient[];
  total: number;
}

export type AppointmentStatus = "scheduled" | "completed" | "cancelled" | "no_show";

export interface Appointment {
  id: string;
  patient_id: string;
  scheduled_for: string;
  status: AppointmentStatus;
  reason: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppointmentListResponse {
  items: Appointment[];
  total: number;
}

export interface AppointmentFormPayload {
  patient_id: string;
  scheduled_for: string;
  reason: string;
  notes: string;
}

export interface Visit {
  id: string;
  patient_id: string;
  appointment_id: string | null;
  started_at: string;
  ended_at: string | null;
  complaint: string | null;
  diagnosis_summary: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface VisitFormPayload {
  patient_id: string;
  appointment_id: string;
  started_at: string;
  ended_at: string;
  complaint: string;
  diagnosis_summary: string;
  notes: string;
}

export interface PatientFormPayload {
  record_number: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  email: string;
  phone: string;
  city: string;
  notes: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

async function request<T>(path: string, role: DemoRole, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      [DEMO_ROLE_HEADER]: role,
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const errorMessage =
      errorBody?.error?.message ??
      (typeof errorBody?.detail === "string" ? errorBody.detail : undefined);

    throw new Error(errorMessage ?? `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function requestNoContent(path: string, role: DemoRole, init?: RequestInit): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      [DEMO_ROLE_HEADER]: role,
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const errorMessage =
      errorBody?.error?.message ??
      (typeof errorBody?.detail === "string" ? errorBody.detail : undefined);

    throw new Error(errorMessage ?? `Request failed with status ${response.status}`);
  }
}

export function listPatients(
  role: DemoRole,
  search: string,
  includeArchived: boolean,
): Promise<PatientListResponse> {
  const params = new URLSearchParams();
  if (search) {
    params.set("q", search);
  }
  if (includeArchived) {
    params.set("include_archived", "true");
  }

  const query = params.toString();
  const path = query ? `/patients?${query}` : "/patients";
  return request<PatientListResponse>(path, role);
}

export function getPatient(role: DemoRole, patientId: string): Promise<Patient> {
  return request<Patient>(`/patients/${patientId}`, role);
}

export function createPatient(
  role: DemoRole,
  payload: PatientFormPayload,
): Promise<Patient> {
  return request<Patient>("/patients", role, {
    method: "POST",
    body: JSON.stringify(normalizePatientPayload(payload)),
  });
}

export function updatePatient(
  role: DemoRole,
  patientId: string,
  payload: PatientFormPayload,
): Promise<Patient> {
  return request<Patient>(`/patients/${patientId}`, role, {
    method: "PATCH",
    body: JSON.stringify(normalizePatientPayload(payload)),
  });
}

export function archivePatient(role: DemoRole, patientId: string): Promise<Patient> {
  return request<Patient>(`/patients/${patientId}`, role, {
    method: "DELETE",
  });
}

export function listAppointments(
  role: DemoRole,
  filters?: {
    patientId?: string;
    status?: AppointmentStatus;
  },
): Promise<AppointmentListResponse> {
  const params = new URLSearchParams();
  if (filters?.patientId) {
    params.set("patient_id", filters.patientId);
  }
  if (filters?.status) {
    params.set("status", filters.status);
  }

  const query = params.toString();
  const path = query ? `/appointments?${query}` : "/appointments";
  return request<AppointmentListResponse>(path, role);
}

export function createAppointment(role: DemoRole, payload: AppointmentFormPayload): Promise<Appointment> {
  return request<Appointment>("/appointments", role, {
    method: "POST",
    body: JSON.stringify(normalizeAppointmentPayload(payload)),
  });
}

export function updateAppointment(
  role: DemoRole,
  appointmentId: string,
  payload: Partial<AppointmentFormPayload> & { status?: AppointmentStatus },
): Promise<Appointment> {
  return request<Appointment>(`/appointments/${appointmentId}`, role, {
    method: "PATCH",
    body: JSON.stringify(normalizeAppointmentUpdatePayload(payload)),
  });
}

export function deleteAppointment(role: DemoRole, appointmentId: string): Promise<void> {
  return requestNoContent(`/appointments/${appointmentId}`, role, { method: "DELETE" });
}

export function createVisit(role: DemoRole, payload: VisitFormPayload): Promise<Visit> {
  return request<Visit>("/visits", role, {
    method: "POST",
    body: JSON.stringify(normalizeVisitPayload(payload)),
  });
}

export function getVisit(role: DemoRole, visitId: string): Promise<Visit> {
  return request<Visit>(`/visits/${visitId}`, role);
}

function normalizePatientPayload(payload: PatientFormPayload) {
  return {
    record_number: payload.record_number || null,
    first_name: payload.first_name,
    last_name: payload.last_name,
    date_of_birth: payload.date_of_birth,
    email: payload.email || null,
    phone: payload.phone || null,
    city: payload.city || null,
    notes: payload.notes || null,
  };
}

function normalizeAppointmentPayload(payload: AppointmentFormPayload) {
  return {
    patient_id: payload.patient_id,
    scheduled_for: toIsoString(payload.scheduled_for),
    reason: payload.reason || null,
    notes: payload.notes || null,
  };
}

function normalizeAppointmentUpdatePayload(
  payload: Partial<AppointmentFormPayload> & { status?: AppointmentStatus },
) {
  return {
    patient_id: payload.patient_id ?? undefined,
    scheduled_for: payload.scheduled_for ? toIsoString(payload.scheduled_for) : undefined,
    status: payload.status,
    reason: payload.reason ? payload.reason : undefined,
    notes: payload.notes ? payload.notes : undefined,
  };
}

function normalizeVisitPayload(payload: VisitFormPayload) {
  return {
    patient_id: payload.patient_id,
    appointment_id: payload.appointment_id || null,
    started_at: toIsoString(payload.started_at),
    ended_at: payload.ended_at ? toIsoString(payload.ended_at) : null,
    complaint: payload.complaint || null,
    diagnosis_summary: payload.diagnosis_summary || null,
    notes: payload.notes || null,
  };
}

function toIsoString(value: string): string {
  return new Date(value).toISOString();
}
