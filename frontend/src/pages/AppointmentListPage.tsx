import { useEffect, useState, type ChangeEvent } from "react";
import { Link, useOutletContext } from "react-router-dom";

import {
  deleteAppointment,
  listAppointments,
  listPatients,
  updateAppointment,
  type Appointment,
  type AppointmentListResponse,
  type AppointmentStatus,
  type Patient,
} from "../app/api";
import type { AppLayoutContext } from "../components/AppLayout";

const STATUS_OPTIONS: AppointmentStatus[] = ["scheduled", "completed", "cancelled", "no_show"];

export function AppointmentListPage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const [appointments, setAppointments] = useState<AppointmentListResponse | null>(null);
  const [patientsById, setPatientsById] = useState<Record<string, Patient>>({});
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | "all">("all");
  const [reloadKey, setReloadKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionBusyId, setActionBusyId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadData() {
      setLoading(true);
      try {
        const [appointmentResponse, patientResponse] = await Promise.all([
          listAppointments(role, statusFilter === "all" ? undefined : { status: statusFilter }),
          listPatients(role, "", false),
        ]);

        if (!active) {
          return;
        }

        const byId = Object.fromEntries(patientResponse.items.map((patient) => [patient.id, patient]));
        setPatientsById(byId);
        setAppointments(appointmentResponse);
        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setAppointments(null);
        setError(loadError instanceof Error ? loadError.message : "Unable to load appointments");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadData();
    return () => {
      active = false;
    };
  }, [reloadKey, role, statusFilter]);

  async function handleStatusUpdate(appointment: Appointment, nextStatus: AppointmentStatus) {
    if (nextStatus === "scheduled") {
      return;
    }

    setError(null);
    setActionBusyId(appointment.id);
    try {
      await updateAppointment(role, appointment.id, { status: nextStatus });
      const refreshed = await listAppointments(role, statusFilter === "all" ? undefined : { status: statusFilter });
      setAppointments(refreshed);
      setError(null);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Unable to update appointment");
    } finally {
      setActionBusyId(null);
    }
  }

  async function handleDelete(appointmentId: string) {
    setError(null);
    setActionBusyId(appointmentId);
    try {
      await deleteAppointment(role, appointmentId);
      const refreshed = await listAppointments(role, statusFilter === "all" ? undefined : { status: statusFilter });
      setAppointments(refreshed);
      setError(null);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete appointment");
    } finally {
      setActionBusyId(null);
    }
  }

  function renderPatientName(patientId: string): string {
    const patient = patientsById[patientId];
    if (!patient) {
      return patientId;
    }

    return `${patient.first_name} ${patient.last_name}`;
  }

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">Appointments</p>
          <h2 className="section-title">Upcoming and completed scheduling</h2>
          <p className="lede">Status handling is intentionally simple: scheduled, completed, cancelled, no-show.</p>
        </div>
        <Link className="primary-button link-button" to="/appointments/new">
          Create appointment
        </Link>
      </section>

      <section className="panel">
        <div className="toolbar">
          <label className="field-stack">
            <span className="field-label">Status filter</span>
            <select
              className="text-input"
              value={statusFilter}
              onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                setStatusFilter(event.target.value as AppointmentStatus | "all")
              }
            >
              <option value="all">All</option>
              {STATUS_OPTIONS.map((statusValue) => (
                <option key={statusValue} value={statusValue}>
                  {statusValue}
                </option>
              ))}
            </select>
          </label>
          <Link className="secondary-button link-button" to="/appointments/new">
            Quick create
          </Link>
        </div>

        {loading ? <p>Loading appointments...</p> : null}
        {error ? (
          <div className="empty-state">
            <p className="status-error">{error}</p>
            <button className="secondary-button" type="button" onClick={() => setReloadKey((current) => current + 1)}>
              Retry
            </button>
          </div>
        ) : null}
        {!loading && !error && appointments?.items.length === 0 ? (
          <div className="empty-state">
            <p>No appointments found for this filter.</p>
            <Link className="primary-button link-button" to="/appointments/new">
              Create first appointment
            </Link>
          </div>
        ) : null}
        {appointments?.items.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Scheduled for</th>
                  <th>Status</th>
                  <th>Reason</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {appointments.items.map((appointment) => (
                  <tr key={appointment.id}>
                    <td>{renderPatientName(appointment.patient_id)}</td>
                    <td>{formatDateTime(appointment.scheduled_for)}</td>
                    <td>{appointment.status}</td>
                    <td>{appointment.reason ?? "—"}</td>
                    <td className="table-actions">
                      <Link
                        className="table-link"
                        to={`/visits/new?patient_id=${appointment.patient_id}&appointment_id=${appointment.id}`}
                      >
                        Create visit
                      </Link>
                      {appointment.status === "scheduled" ? (
                        <select
                          className="text-input status-select"
                          defaultValue="scheduled"
                          disabled={actionBusyId === appointment.id}
                          onChange={(event) =>
                            void handleStatusUpdate(appointment, event.target.value as AppointmentStatus)
                          }
                        >
                          <option value="scheduled">Change status...</option>
                          <option value="completed">completed</option>
                          <option value="cancelled">cancelled</option>
                          <option value="no_show">no_show</option>
                        </select>
                      ) : null}
                      {role === "admin" ? (
                        <button
                          className="table-button"
                          type="button"
                          disabled={actionBusyId === appointment.id}
                          onClick={() => void handleDelete(appointment.id)}
                        >
                          Delete
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}
