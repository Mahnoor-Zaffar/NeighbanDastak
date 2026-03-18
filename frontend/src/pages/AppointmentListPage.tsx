import { useEffect, useState, type ChangeEvent } from "react";
import { CalendarPlus, ClipboardPlus, RefreshCw, Trash2 } from "lucide-react";
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
import { AnalyticsDashboardSection } from "../components/analytics/AnalyticsDashboardSection";
import { FollowUpDashboardSection } from "../components/followUps/FollowUpDashboardSection";
import { StatusBadge } from "../components/ui/StatusBadge";

const STATUS_OPTIONS: AppointmentStatus[] = ["scheduled", "completed", "cancelled", "no_show"];

const primaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition duration-200 hover:bg-indigo-700";

const secondaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition duration-200 hover:bg-slate-50";

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
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <h2 className="text-lg font-medium text-slate-900">Appointments</h2>
            <p className="text-sm text-slate-500">Manage scheduling, status updates, and visit handoff in one place.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link className={secondaryButtonClass} to="/visits/new">
              <ClipboardPlus className="h-4 w-4" />
              Start visit
            </Link>
            <Link className={primaryButtonClass} to="/appointments/new">
              <CalendarPlus className="h-4 w-4" />
              Create appointment
            </Link>
          </div>
        </div>
      </section>

      <AnalyticsDashboardSection role={role} />

      {role !== "receptionist" ? <FollowUpDashboardSection role={role} /> : null}

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <label className="space-y-2">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Status filter</span>
            <select
              className="w-full min-w-[220px] rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition duration-200 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              value={statusFilter}
              onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                setStatusFilter(event.target.value as AppointmentStatus | "all")
              }
            >
              <option value="all">All statuses</option>
              {STATUS_OPTIONS.map((statusValue) => (
                <option key={statusValue} value={statusValue}>
                  {formatStatusLabel(statusValue)}
                </option>
              ))}
            </select>
          </label>

          <button className={secondaryButtonClass} onClick={() => setReloadKey((current) => current + 1)} type="button">
            <RefreshCw className="h-4 w-4" />
            Refresh data
          </button>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-slate-900">Appointment list</h3>
            <p className="text-sm text-slate-500">{appointments?.total ?? 0} total</p>
          </div>

          {loading ? <p className="text-sm text-slate-500">Loading appointments...</p> : null}

          {error ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
              <p>{error}</p>
              <button
                className="mt-3 inline-flex items-center rounded-lg border border-rose-300 bg-white px-3 py-1.5 text-xs font-medium text-rose-700 transition duration-200 hover:bg-rose-100"
                onClick={() => setReloadKey((current) => current + 1)}
                type="button"
              >
                Retry
              </button>
            </div>
          ) : null}

          {!loading && !error && appointments?.items.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
              <p className="text-sm text-slate-600">No appointments found for this filter.</p>
              <Link className={`${primaryButtonClass} mt-4`} to="/appointments/new">
                Create first appointment
              </Link>
            </div>
          ) : null}

          {appointments?.items.length ? (
            <div className="overflow-x-auto rounded-lg border border-slate-200">
              <table className="min-w-[760px] w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Patient</th>
                    <th className="px-4 py-3 text-left font-medium">Doctor</th>
                    <th className="px-4 py-3 text-left font-medium">Time</th>
                    <th className="px-4 py-3 text-left font-medium">Status</th>
                    <th className="px-4 py-3 text-left font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white text-slate-700">
                  {appointments.items.map((appointment) => (
                    <tr className="transition duration-200 hover:bg-slate-50" key={appointment.id}>
                      <td className="px-4 py-3">
                        <p className="font-medium text-slate-900">{renderPatientName(appointment.patient_id)}</p>
                        <p className="text-xs text-slate-500">{appointment.reason ?? "General consultation"}</p>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{role === "doctor" ? "Assigned to you" : "Assigned doctor"}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{formatDateTime(appointment.scheduled_for)}</td>
                      <td className="px-4 py-3">
                        <StatusBadge label={formatStatusLabel(appointment.status)} tone={appointment.status} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <Link
                            className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition duration-200 hover:bg-slate-50"
                            to={`/visits/new?patient_id=${appointment.patient_id}&appointment_id=${appointment.id}`}
                          >
                            Create visit
                          </Link>

                          {appointment.status === "scheduled" ? (
                            <select
                              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 transition duration-200 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                              defaultValue="scheduled"
                              disabled={actionBusyId === appointment.id}
                              onChange={(event) =>
                                void handleStatusUpdate(appointment, event.target.value as AppointmentStatus)
                              }
                            >
                              <option value="scheduled">Update status</option>
                              <option value="completed">Completed</option>
                              <option value="cancelled">Cancelled</option>
                              <option value="no_show">No-show</option>
                            </select>
                          ) : null}

                          {role === "admin" ? (
                            <button
                              className="inline-flex items-center gap-1 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-700 transition duration-200 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60"
                              type="button"
                              disabled={actionBusyId === appointment.id}
                              onClick={() => void handleDelete(appointment.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                              Delete
                            </button>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="space-y-1">
          <h3 className="text-lg font-medium text-slate-900">Quick actions</h3>
          <p className="text-sm text-slate-500">Common workflow shortcuts for faster intake.</p>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link className={primaryButtonClass} to="/appointments/new">
            <CalendarPlus className="h-4 w-4" />
            New appointment
          </Link>
          <Link className={secondaryButtonClass} to="/visits/new">
            <ClipboardPlus className="h-4 w-4" />
            New visit
          </Link>
        </div>
      </section>
    </div>
  );
}

function formatStatusLabel(status: AppointmentStatus): string {
  if (status === "no_show") {
    return "No-show";
  }

  return `${status.slice(0, 1).toUpperCase()}${status.slice(1)}`;
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}
