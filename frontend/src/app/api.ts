import { getStoredDemoSession } from "./demoRole";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
const DEMO_ROLE_HEADER = "X-Demo-Role";
const DEMO_USER_ID_HEADER = "X-Demo-User-Id";
export type DemoRole = "admin" | "doctor" | "receptionist";

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

export interface PatientTimelineEvent {
  id: string;
  event_type: string;
  event_timestamp: string;
  title: string;
  subtitle: string | null;
  actor_name: string | null;
  related_entity_type: string;
  related_entity_id: string;
  metadata: Record<string, unknown>;
}

export interface PatientTimelineResponse {
  patient_id: string;
  sort_order: "asc" | "desc" | string;
  items: PatientTimelineEvent[];
  total: number;
}

export type AppointmentStatus = "scheduled" | "completed" | "cancelled" | "no_show";
export type QueueStatus = "waiting" | "in_progress" | "completed" | "skipped";

export interface Appointment {
  id: string;
  patient_id: string;
  scheduled_for: string;
  scheduled_date: string;
  status: AppointmentStatus;
  queue_number: number | null;
  queue_status: QueueStatus | null;
  checked_in_at: string | null;
  called_at: string | null;
  completed_at: string | null;
  assigned_doctor_id: string | null;
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

export interface QueueEntry {
  appointment_id: string;
  patient_id: string;
  patient_record_number: string;
  patient_name: string;
  scheduled_for: string;
  scheduled_date: string;
  appointment_status: AppointmentStatus;
  queue_number: number;
  queue_status: QueueStatus;
  checked_in_at: string | null;
  called_at: string | null;
  completed_at: string | null;
  assigned_doctor_id: string | null;
}

export interface QueueListResponse {
  scheduled_date: string;
  doctor_id: string | null;
  include_history: boolean;
  items: QueueEntry[];
  total: number;
}

export interface QueueCheckInPayload {
  assigned_doctor_id?: string;
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

export interface PrescriptionItem {
  id: string;
  prescription_id: string;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions: string | null;
  created_at: string;
  updated_at: string;
}

export interface Prescription {
  id: string;
  patient_id: string;
  visit_id: string;
  doctor_id: string;
  diagnosis_summary: string;
  notes: string | null;
  items: PrescriptionItem[];
  created_at: string;
  updated_at: string;
}

export interface PrescriptionListResponse {
  items: Prescription[];
  total: number;
}

export interface PrescriptionItemFormPayload {
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions: string;
}

export interface PrescriptionCreatePayload {
  patient_id: string;
  visit_id: string;
  doctor_id: string;
  diagnosis_summary: string;
  notes: string;
  items: PrescriptionItemFormPayload[];
}

export interface PrescriptionUpdatePayload {
  diagnosis_summary: string;
  notes: string;
  items: PrescriptionItemFormPayload[];
}

export type FollowUpStatus = "pending" | "completed" | "cancelled" | "overdue";

export interface FollowUp {
  id: string;
  patient_id: string;
  visit_id: string;
  doctor_id: string;
  due_date: string;
  reason: string;
  notes: string | null;
  status: FollowUpStatus;
  created_at: string;
  updated_at: string;
}

export interface FollowUpListResponse {
  items: FollowUp[];
  total: number;
}

export interface FollowUpCreatePayload {
  patient_id: string;
  visit_id: string;
  doctor_id: string;
  due_date: string;
  reason: string;
  notes: string;
}

export interface FollowUpUpdatePayload {
  due_date?: string;
  reason?: string;
  notes?: string;
}

export interface DemoDoctorProfile {
  id: string;
  full_name: string;
  email: string;
  specialty: string | null;
}

export interface DemoDoctorProfileListResponse {
  items: DemoDoctorProfile[];
  total: number;
}

export interface DemoCurrentUserResponse {
  role: DemoRole;
  user_id: string | null;
  doctor_profile_id: string | null;
  full_name: string | null;
  email: string | null;
}

export interface AnalyticsSummaryResponse {
  reference_date: string;
  scope: "clinic" | "doctor" | string;
  total_patients: number;
  active_doctors: number;
  appointments_today: number;
  completed_visits_today: number;
  appointments_this_week: number;
  recent_new_patients_7d: number;
  recent_new_patients_previous_7d: number;
  recent_appointments_7d: number;
  recent_appointments_previous_7d: number;
}

export interface AnalyticsAppointmentsByDayPoint {
  day: string;
  appointments_count: number;
}

export interface AnalyticsAppointmentsByDayResponse {
  starts_on: string;
  ends_on: string;
  items: AnalyticsAppointmentsByDayPoint[];
  total: number;
}

export interface AnalyticsDoctorWorkloadItem {
  doctor_id: string;
  doctor_name: string;
  appointments_count: number;
}

export interface AnalyticsDoctorWorkloadResponse {
  starts_on: string;
  ends_on: string;
  items: AnalyticsDoctorWorkloadItem[];
  total: number;
}

export interface AnalyticsAppointmentStatusBreakdownItem {
  status: AppointmentStatus;
  count: number;
}

export interface AnalyticsAppointmentStatusBreakdownResponse {
  starts_on: string;
  ends_on: string;
  items: AnalyticsAppointmentStatusBreakdownItem[];
  total: number;
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

export async function listDemoDoctorProfiles(): Promise<DemoDoctorProfileListResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/demo/doctors`, {
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const errorMessage =
      errorBody?.error?.message ??
      (typeof errorBody?.detail === "string" ? errorBody.detail : undefined);
    throw new Error(errorMessage ?? `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<DemoDoctorProfileListResponse>;
}

export async function loginDemoUser(payload: {
  role: DemoRole;
  doctor_profile_id?: string;
}): Promise<DemoCurrentUserResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/demo/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const errorMessage =
      errorBody?.error?.message ??
      (typeof errorBody?.detail === "string" ? errorBody.detail : undefined);
    throw new Error(errorMessage ?? `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<DemoCurrentUserResponse>;
}

export function getDemoCurrentUser(role: DemoRole, actorUserId?: string): Promise<DemoCurrentUserResponse> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<DemoCurrentUserResponse>("/auth/demo/current-user", role, headers);
}

async function request<T>(path: string, role: DemoRole, init?: RequestInit): Promise<T> {
  return requestWithHeaders<T>(path, role, undefined, init);
}

async function requestWithHeaders<T>(
  path: string,
  role: DemoRole,
  extraHeaders?: Record<string, string>,
  init?: RequestInit,
): Promise<T> {
  const actorUserId = resolveActorUserId(role, extraHeaders);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      [DEMO_ROLE_HEADER]: role,
      ...(actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : {}),
      ...(extraHeaders ?? {}),
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
  const actorUserId = resolveActorUserId(role);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      [DEMO_ROLE_HEADER]: role,
      ...(actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : {}),
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

function resolveActorUserId(role: DemoRole, extraHeaders?: Record<string, string>): string | undefined {
  if (role !== "doctor") {
    return undefined;
  }

  const explicitHeader = (extraHeaders?.[DEMO_USER_ID_HEADER] ?? "").trim();
  if (explicitHeader) {
    return explicitHeader;
  }

  const session = getStoredDemoSession();
  if (session?.role === "doctor") {
    return session.doctorProfileId ?? undefined;
  }

  return undefined;
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

export function getPatientTimeline(role: DemoRole, patientId: string): Promise<PatientTimelineResponse> {
  return request<PatientTimelineResponse>(`/patients/${patientId}/timeline`, role);
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
    startsAt?: string;
    endsAt?: string;
  },
): Promise<AppointmentListResponse> {
  const params = new URLSearchParams();
  if (filters?.patientId) {
    params.set("patient_id", filters.patientId);
  }
  if (filters?.status) {
    params.set("status", filters.status);
  }
  if (filters?.startsAt) {
    params.set("starts_at", filters.startsAt);
  }
  if (filters?.endsAt) {
    params.set("ends_at", filters.endsAt);
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

export function checkInAppointment(
  role: DemoRole,
  appointmentId: string,
  payload?: QueueCheckInPayload,
  actorUserId?: string,
): Promise<QueueEntry> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<QueueEntry>(`/appointments/${appointmentId}/check-in`, role, headers, {
    method: "POST",
    body: JSON.stringify(payload ?? {}),
  });
}

export function listQueue(
  role: DemoRole,
  options?: {
    scheduledDate?: string;
    includeHistory?: boolean;
    doctorId?: string;
    actorUserId?: string;
  },
): Promise<QueueListResponse> {
  const params = new URLSearchParams();
  if (options?.scheduledDate) {
    params.set("scheduled_date", options.scheduledDate);
  }
  if (options?.includeHistory) {
    params.set("include_history", "true");
  }

  const pathBase = options?.doctorId ? `/queue/doctor/${options.doctorId}` : "/queue";
  const path = params.toString() ? `${pathBase}?${params.toString()}` : pathBase;
  const headers = options?.actorUserId ? { [DEMO_USER_ID_HEADER]: options.actorUserId } : undefined;

  return requestWithHeaders<QueueListResponse>(path, role, headers);
}

export function callQueueEntry(
  role: DemoRole,
  appointmentId: string,
  actorUserId?: string,
): Promise<QueueEntry> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<QueueEntry>(`/queue/${appointmentId}/call`, role, headers, {
    method: "POST",
  });
}

export function completeQueueEntry(
  role: DemoRole,
  appointmentId: string,
  actorUserId?: string,
): Promise<QueueEntry> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<QueueEntry>(`/queue/${appointmentId}/complete`, role, headers, {
    method: "POST",
  });
}

export function skipQueueEntry(
  role: DemoRole,
  appointmentId: string,
  actorUserId?: string,
): Promise<QueueEntry> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<QueueEntry>(`/queue/${appointmentId}/skip`, role, headers, {
    method: "POST",
  });
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

export function createPrescription(role: DemoRole, payload: PrescriptionCreatePayload): Promise<Prescription> {
  return request<Prescription>("/prescriptions", role, {
    method: "POST",
    body: JSON.stringify(normalizePrescriptionCreatePayload(payload)),
  });
}

export function getPrescription(role: DemoRole, prescriptionId: string): Promise<Prescription> {
  return request<Prescription>(`/prescriptions/${prescriptionId}`, role);
}

export function listPatientPrescriptions(
  role: DemoRole,
  patientId: string,
  limit = 25,
  offset = 0,
): Promise<PrescriptionListResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  return request<PrescriptionListResponse>(`/patients/${patientId}/prescriptions?${params.toString()}`, role);
}

export function listVisitPrescriptions(
  role: DemoRole,
  visitId: string,
  limit = 25,
  offset = 0,
): Promise<PrescriptionListResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  return request<PrescriptionListResponse>(`/visits/${visitId}/prescriptions?${params.toString()}`, role);
}

export function updatePrescription(
  role: DemoRole,
  prescriptionId: string,
  payload: PrescriptionUpdatePayload,
): Promise<Prescription> {
  return request<Prescription>(`/prescriptions/${prescriptionId}`, role, {
    method: "PUT",
    body: JSON.stringify(normalizePrescriptionUpdatePayload(payload)),
  });
}

export function deletePrescription(role: DemoRole, prescriptionId: string): Promise<void> {
  return requestNoContent(`/prescriptions/${prescriptionId}`, role, {
    method: "DELETE",
  });
}

export function createFollowUp(
  role: DemoRole,
  payload: FollowUpCreatePayload,
  actorUserId?: string,
): Promise<FollowUp> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<FollowUp>("/follow-ups", role, headers, {
    method: "POST",
    body: JSON.stringify(normalizeFollowUpCreatePayload(payload)),
  });
}

export function listFollowUps(
  role: DemoRole,
  options?: {
    status?: FollowUpStatus;
    dueBefore?: string;
    limit?: number;
    offset?: number;
    actorUserId?: string;
  },
): Promise<FollowUpListResponse> {
  const params = new URLSearchParams();
  if (options?.status) {
    params.set("status", options.status);
  }
  if (options?.dueBefore) {
    params.set("due_before", options.dueBefore);
  }
  params.set("limit", String(options?.limit ?? 25));
  params.set("offset", String(options?.offset ?? 0));
  const headers = options?.actorUserId ? { [DEMO_USER_ID_HEADER]: options.actorUserId } : undefined;
  return requestWithHeaders<FollowUpListResponse>(`/follow-ups?${params.toString()}`, role, headers);
}

export function listPatientFollowUps(
  role: DemoRole,
  patientId: string,
  options?: {
    status?: FollowUpStatus;
    dueBefore?: string;
    limit?: number;
    offset?: number;
    actorUserId?: string;
  },
): Promise<FollowUpListResponse> {
  const params = new URLSearchParams();
  if (options?.status) {
    params.set("status", options.status);
  }
  if (options?.dueBefore) {
    params.set("due_before", options.dueBefore);
  }
  params.set("limit", String(options?.limit ?? 25));
  params.set("offset", String(options?.offset ?? 0));
  const headers = options?.actorUserId ? { [DEMO_USER_ID_HEADER]: options.actorUserId } : undefined;
  return requestWithHeaders<FollowUpListResponse>(
    `/patients/${patientId}/follow-ups?${params.toString()}`,
    role,
    headers,
  );
}

export function updateFollowUp(
  role: DemoRole,
  followUpId: string,
  payload: FollowUpUpdatePayload,
  actorUserId?: string,
): Promise<FollowUp> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<FollowUp>(`/follow-ups/${followUpId}`, role, headers, {
    method: "PUT",
    body: JSON.stringify(normalizeFollowUpUpdatePayload(payload)),
  });
}

export function completeFollowUp(role: DemoRole, followUpId: string, actorUserId?: string): Promise<FollowUp> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<FollowUp>(`/follow-ups/${followUpId}/complete`, role, headers, {
    method: "POST",
  });
}

export function cancelFollowUp(role: DemoRole, followUpId: string, actorUserId?: string): Promise<FollowUp> {
  const headers = actorUserId ? { [DEMO_USER_ID_HEADER]: actorUserId } : undefined;
  return requestWithHeaders<FollowUp>(`/follow-ups/${followUpId}/cancel`, role, headers, {
    method: "POST",
  });
}

export function getAnalyticsSummary(
  role: DemoRole,
  options?: {
    actorUserId?: string;
    doctorId?: string;
  },
): Promise<AnalyticsSummaryResponse> {
  const params = new URLSearchParams();
  if (options?.doctorId) {
    params.set("doctor_id", options.doctorId);
  }
  const path = params.toString() ? `/insights/summary?${params.toString()}` : "/insights/summary";
  const headers = options?.actorUserId ? { [DEMO_USER_ID_HEADER]: options.actorUserId } : undefined;
  return requestWithHeaders<AnalyticsSummaryResponse>(path, role, headers);
}

export function getAnalyticsAppointmentsByDay(
  role: DemoRole,
  options?: {
    days?: number;
    endsOn?: string;
    actorUserId?: string;
    doctorId?: string;
  },
): Promise<AnalyticsAppointmentsByDayResponse> {
  const params = new URLSearchParams();
  params.set("days", String(options?.days ?? 14));
  if (options?.endsOn) {
    params.set("ends_on", options.endsOn);
  }
  if (options?.doctorId) {
    params.set("doctor_id", options.doctorId);
  }
  const headers = options?.actorUserId ? { [DEMO_USER_ID_HEADER]: options.actorUserId } : undefined;
  return requestWithHeaders<AnalyticsAppointmentsByDayResponse>(
    `/insights/appointments-by-day?${params.toString()}`,
    role,
    headers,
  );
}

export function getAnalyticsDoctorWorkload(
  role: DemoRole,
  options?: {
    startsOn?: string;
    endsOn?: string;
    actorUserId?: string;
    doctorId?: string;
  },
): Promise<AnalyticsDoctorWorkloadResponse> {
  const params = new URLSearchParams();
  if (options?.startsOn) {
    params.set("starts_on", options.startsOn);
  }
  if (options?.endsOn) {
    params.set("ends_on", options.endsOn);
  }
  if (options?.doctorId) {
    params.set("doctor_id", options.doctorId);
  }
  const path = params.toString() ? `/insights/doctor-workload?${params.toString()}` : "/insights/doctor-workload";
  const headers = options?.actorUserId ? { [DEMO_USER_ID_HEADER]: options.actorUserId } : undefined;
  return requestWithHeaders<AnalyticsDoctorWorkloadResponse>(path, role, headers);
}

export function getAnalyticsAppointmentStatusBreakdown(
  role: DemoRole,
  options?: {
    startsOn?: string;
    endsOn?: string;
    actorUserId?: string;
    doctorId?: string;
  },
): Promise<AnalyticsAppointmentStatusBreakdownResponse> {
  const params = new URLSearchParams();
  if (options?.startsOn) {
    params.set("starts_on", options.startsOn);
  }
  if (options?.endsOn) {
    params.set("ends_on", options.endsOn);
  }
  if (options?.doctorId) {
    params.set("doctor_id", options.doctorId);
  }
  const path = params.toString()
    ? `/insights/appointment-status-breakdown?${params.toString()}`
    : "/insights/appointment-status-breakdown";
  const headers = options?.actorUserId ? { [DEMO_USER_ID_HEADER]: options.actorUserId } : undefined;
  return requestWithHeaders<AnalyticsAppointmentStatusBreakdownResponse>(path, role, headers);
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

function normalizePrescriptionCreatePayload(payload: PrescriptionCreatePayload) {
  return {
    patient_id: payload.patient_id,
    visit_id: payload.visit_id,
    doctor_id: payload.doctor_id,
    diagnosis_summary: payload.diagnosis_summary.trim(),
    notes: payload.notes.trim() || null,
    items: payload.items.map((item) => ({
      medicine_name: item.medicine_name.trim(),
      dosage: item.dosage.trim(),
      frequency: item.frequency.trim(),
      duration: item.duration.trim(),
      instructions: item.instructions.trim() || null,
    })),
  };
}

function normalizePrescriptionUpdatePayload(payload: PrescriptionUpdatePayload) {
  return {
    diagnosis_summary: payload.diagnosis_summary.trim(),
    notes: payload.notes.trim() || null,
    items: payload.items.map((item) => ({
      medicine_name: item.medicine_name.trim(),
      dosage: item.dosage.trim(),
      frequency: item.frequency.trim(),
      duration: item.duration.trim(),
      instructions: item.instructions.trim() || null,
    })),
  };
}

function normalizeFollowUpCreatePayload(payload: FollowUpCreatePayload) {
  return {
    patient_id: payload.patient_id,
    visit_id: payload.visit_id,
    doctor_id: payload.doctor_id.trim(),
    due_date: payload.due_date,
    reason: payload.reason.trim(),
    notes: payload.notes.trim() || null,
  };
}

function normalizeFollowUpUpdatePayload(payload: FollowUpUpdatePayload) {
  return {
    due_date: payload.due_date,
    reason: payload.reason !== undefined ? payload.reason.trim() : undefined,
    notes: payload.notes !== undefined ? payload.notes.trim() || null : undefined,
  };
}

function toIsoString(value: string): string {
  return new Date(value).toISOString();
}
