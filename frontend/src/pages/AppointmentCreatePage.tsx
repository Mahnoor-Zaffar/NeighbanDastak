import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useOutletContext } from "react-router-dom";

import { createAppointment, listPatients, type AppointmentFormPayload, type Patient } from "../app/api";
import type { AppLayoutContext } from "../components/AppLayout";

export function AppointmentCreatePage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoadingPatients, setIsLoadingPatients] = useState(true);
  const [formState, setFormState] = useState<AppointmentFormPayload>({
    patient_id: "",
    scheduled_for: "",
    reason: "",
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
        setFormState((current) => ({
          ...current,
          patient_id: current.patient_id || response.items[0]?.id || "",
        }));
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setFormError(null);

    if (!formState.patient_id) {
      setFormError("Select a patient before creating an appointment.");
      setIsSubmitting(false);
      return;
    }
    if (!formState.scheduled_for) {
      setFormError("Scheduled date and time is required.");
      setIsSubmitting(false);
      return;
    }
    if (new Date(formState.scheduled_for).getTime() <= Date.now()) {
      setFormError("Scheduled time must be in the future.");
      setIsSubmitting(false);
      return;
    }
    if (formState.reason.length > 255) {
      setFormError("Reason must be 255 characters or fewer.");
      setIsSubmitting(false);
      return;
    }

    try {
      await createAppointment(role, formState);
      navigate("/appointments");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to create appointment");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">Create appointment</p>
          <h2 className="section-title">New scheduling entry</h2>
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
          <p>No active patients found. Create a patient before scheduling an appointment.</p>
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
              onChange={(event) => setFormState((current) => ({ ...current, patient_id: event.target.value }))}
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
            <span className="field-label">Scheduled for</span>
            <input
              className="text-input"
              type="datetime-local"
              value={formState.scheduled_for}
              onChange={(event) => setFormState((current) => ({ ...current, scheduled_for: event.target.value }))}
              required
              min={toLocalDateTimeValue(new Date(Date.now() + 5 * 60 * 1000))}
            />
          </label>

          <label className="field-stack">
            <span className="field-label">Reason</span>
            <input
              className="text-input"
              value={formState.reason}
              onChange={(event) => setFormState((current) => ({ ...current, reason: event.target.value }))}
              maxLength={255}
            />
          </label>

          <label className="field-stack">
            <span className="field-label">Notes</span>
            <textarea
              className="text-area"
              rows={4}
              value={formState.notes}
              onChange={(event) => setFormState((current) => ({ ...current, notes: event.target.value }))}
              maxLength={1000}
            />
          </label>

          {formError ? <p className="status-error">{formError}</p> : null}
          {error ? <p className="status-error">{error}</p> : null}
          <button className="primary-button" disabled={isSubmitting || patients.length === 0} type="submit">
            {isSubmitting ? "Creating..." : "Create appointment"}
          </button>
        </form>
      ) : null}
    </div>
  );
}

function toLocalDateTimeValue(value: Date): string {
  const offsetMs = value.getTimezoneOffset() * 60 * 1000;
  return new Date(value.getTime() - offsetMs).toISOString().slice(0, 16);
}
