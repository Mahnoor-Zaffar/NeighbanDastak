import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useOutletContext, useSearchParams } from "react-router-dom";

import {
  createVisit,
  listAppointments,
  listPatients,
  type Appointment,
  type Patient,
  type VisitFormPayload,
} from "../app/api";
import type { AppLayoutContext } from "../components/AppLayout";

export function VisitCreatePage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoadingPatients, setIsLoadingPatients] = useState(true);
  const [isLoadingAppointments, setIsLoadingAppointments] = useState(false);
  const [appointmentsError, setAppointmentsError] = useState<string | null>(null);
  const [formState, setFormState] = useState<VisitFormPayload>({
    patient_id: searchParams.get("patient_id") ?? "",
    appointment_id: searchParams.get("appointment_id") ?? "",
    started_at: getDefaultLocalDateTime(),
    ended_at: "",
    complaint: "",
    diagnosis_summary: "",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadPatients() {
      setIsLoadingPatients(true);
      try {
        const response = await listPatients(role, "", false);
        if (!active) {
          return;
        }

        setPatients(response.items);
        if (!formState.patient_id && response.items[0]) {
          setFormState((current) => ({ ...current, patient_id: response.items[0].id }));
        }
      } catch (loadError) {
        if (!active) {
          return;
        }

        setError(loadError instanceof Error ? loadError.message : "Unable to load patients");
      } finally {
        if (active) {
          setIsLoadingPatients(false);
        }
      }
    }

    void loadPatients();
    return () => {
      active = false;
    };
  }, [role]);

  useEffect(() => {
    if (!formState.patient_id) {
      setAppointments([]);
      setAppointmentsError(null);
      return;
    }

    let active = true;
    async function loadAppointments() {
      setIsLoadingAppointments(true);
      try {
        const response = await listAppointments(role, { patientId: formState.patient_id });
        if (!active) {
          return;
        }

        setAppointments(response.items);
        setAppointmentsError(null);
      } catch {
        if (!active) {
          return;
        }

        setAppointments([]);
        setAppointmentsError("Unable to load appointments for selected patient.");
      } finally {
        if (active) {
          setIsLoadingAppointments(false);
        }
      }
    }

    void loadAppointments();
    return () => {
      active = false;
    };
  }, [formState.patient_id, role]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setFormError(null);

    if (!formState.patient_id) {
      setFormError("Select a patient first.");
      setIsSubmitting(false);
      return;
    }
    if (!formState.started_at) {
      setFormError("Visit start date and time is required.");
      setIsSubmitting(false);
      return;
    }
    if (formState.ended_at && new Date(formState.ended_at) < new Date(formState.started_at)) {
      setFormError("Visit end time cannot be before start time.");
      setIsSubmitting(false);
      return;
    }
    if (formState.complaint.length > 255 || formState.diagnosis_summary.length > 255) {
      setFormError("Complaint and diagnosis summary must be 255 characters or fewer.");
      setIsSubmitting(false);
      return;
    }

    try {
      const visit = await createVisit(role, formState);
      navigate(`/visits/${visit.id}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to create visit");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">Create visit</p>
          <h2 className="section-title">New encounter record</h2>
        </div>
        <Link className="secondary-button link-button" to="/appointments">
          Back to appointments
        </Link>
      </section>
      {isLoadingPatients ? (
        <section className="panel">
          <p>Loading patients...</p>
        </section>
      ) : null}
      {!isLoadingPatients && !error && patients.length === 0 ? (
        <section className="panel">
          <p>No active patients found. Create a patient before creating a visit.</p>
          <Link className="primary-button link-button" to="/patients/new">
            Create patient
          </Link>
        </section>
      ) : null}
      {!isLoadingPatients && error && patients.length === 0 ? (
        <section className="panel empty-state">
          <p className="status-error">{error}</p>
          <Link className="secondary-button link-button" to="/appointments">
            Back to appointments
          </Link>
        </section>
      ) : null}

      {!isLoadingPatients && patients.length > 0 ? (
        <form className="panel form-stack" onSubmit={handleSubmit}>
          <label className="field-stack">
            <span className="field-label">Patient</span>
            <select
              className="text-input"
              value={formState.patient_id}
              onChange={(event) =>
                setFormState((current) => ({
                  ...current,
                  patient_id: event.target.value,
                  appointment_id: "",
                }))
              }
              required
              disabled={patients.length === 0}
            >
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.first_name} {patient.last_name} ({patient.record_number})
                </option>
              ))}
            </select>
          </label>

          <label className="field-stack">
            <span className="field-label">Linked appointment (optional)</span>
            <select
              className="text-input"
              value={formState.appointment_id}
              onChange={(event) => setFormState((current) => ({ ...current, appointment_id: event.target.value }))}
              disabled={isLoadingAppointments || appointments.length === 0}
            >
              <option value="">No linked appointment</option>
              {appointments.map((appointment) => (
                <option key={appointment.id} value={appointment.id}>
                  {new Date(appointment.scheduled_for).toLocaleString()} - {appointment.status}
                </option>
              ))}
            </select>
          </label>

          <div className="grid-two">
            <label className="field-stack">
              <span className="field-label">Started at</span>
              <input
                className="text-input"
                type="datetime-local"
                value={formState.started_at}
                onChange={(event) => setFormState((current) => ({ ...current, started_at: event.target.value }))}
                required
              />
            </label>
            <label className="field-stack">
              <span className="field-label">Ended at (optional)</span>
              <input
                className="text-input"
                type="datetime-local"
                value={formState.ended_at}
                onChange={(event) => setFormState((current) => ({ ...current, ended_at: event.target.value }))}
              />
            </label>
          </div>

          <label className="field-stack">
            <span className="field-label">Complaint</span>
            <input
              className="text-input"
              value={formState.complaint}
              onChange={(event) => setFormState((current) => ({ ...current, complaint: event.target.value }))}
              maxLength={255}
            />
          </label>

          <label className="field-stack">
            <span className="field-label">Diagnosis summary</span>
            <input
              className="text-input"
              value={formState.diagnosis_summary}
              onChange={(event) => setFormState((current) => ({ ...current, diagnosis_summary: event.target.value }))}
              maxLength={255}
            />
          </label>

          <label className="field-stack">
            <span className="field-label">Notes</span>
            <textarea
              className="text-area"
              rows={5}
              value={formState.notes}
              onChange={(event) => setFormState((current) => ({ ...current, notes: event.target.value }))}
              maxLength={2000}
            />
          </label>

          {isLoadingAppointments ? <p className="muted-note">Loading appointments for selected patient...</p> : null}
          {appointmentsError ? <p className="muted-note">{appointmentsError}</p> : null}
          {formError ? <p className="status-error">{formError}</p> : null}
          {error ? <p className="status-error">{error}</p> : null}
          <button className="primary-button" disabled={isSubmitting || patients.length === 0} type="submit">
            {isSubmitting ? "Creating..." : "Create visit"}
          </button>
        </form>
      ) : null}
    </div>
  );
}

function getDefaultLocalDateTime(): string {
  const now = new Date();
  now.setSeconds(0, 0);
  const offsetMs = now.getTimezoneOffset() * 60 * 1000;
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 16);
}
