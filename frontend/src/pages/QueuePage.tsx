import { useEffect, useMemo, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import {
  ClipboardCheck,
  RefreshCw,
  SkipForward,
  Stethoscope,
  Timer,
  UserRoundCheck,
  type LucideIcon,
} from "lucide-react";

import {
  callQueueEntry,
  checkInAppointment,
  completeQueueEntry,
  listAppointments,
  listQueue,
  skipQueueEntry,
  type Appointment,
  type AppointmentStatus,
  type QueueEntry,
} from "../app/api";
import {
  getStoredDoctorDisplayName,
  getStoredDoctorProfileId,
  storeDoctorDisplayName,
  storeDoctorProfileId,
} from "../app/doctorIdentity";
import type { AppLayoutContext } from "../components/AppLayout";
import { StatusBadge } from "../components/ui/StatusBadge";

const primaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition duration-200 hover:bg-indigo-700";

const secondaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition duration-200 hover:bg-slate-50";

const REFRESH_INTERVAL_MS = 20000;

export function QueuePage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const isDoctor = role === "doctor";
  const isAdmin = role === "admin";
  const [doctorProfileId, setDoctorProfileId] = useState(() => getStoredDoctorProfileId());
  const [doctorDisplayName, setDoctorDisplayName] = useState(() => getStoredDoctorDisplayName());
  const [draftDoctorId, setDraftDoctorId] = useState(() => getStoredDoctorProfileId());
  const [draftDoctorName, setDraftDoctorName] = useState(() => getStoredDoctorDisplayName());
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [queueEntries, setQueueEntries] = useState<QueueEntry[]>([]);
  const [reloadToken, setReloadToken] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyAppointmentId, setBusyAppointmentId] = useState<string | null>(null);
  const [assignedDoctorByAppointment, setAssignedDoctorByAppointment] = useState<Record<string, string>>({});

  const selectedDate = useMemo(() => new Date().toISOString().slice(0, 10), []);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setReloadToken((current) => current + 1);
    }, REFRESH_INTERVAL_MS);

    return () => {
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadData() {
      if (lastRefreshedAt === null) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setActionError(null);

      try {
        if (isDoctor) {
          if (!doctorProfileId) {
            if (!active) {
              return;
            }
            setQueueEntries([]);
            setAppointments([]);
            setError("Set your doctor profile ID to load your assigned queue.");
            return;
          }

          const queueResponse = await listQueue(role, {
            scheduledDate: selectedDate,
            includeHistory: true,
            actorUserId: doctorProfileId,
          });
          if (!active) {
            return;
          }
          setQueueEntries(queueResponse.items);
          setAppointments([]);
        } else {
          const dayRange = buildDayRange(selectedDate);
          const [appointmentResponse, queueResponse] = await Promise.all([
            listAppointments(role, {
              startsAt: dayRange.startsAt,
              endsAt: dayRange.endsAt,
            }),
            listQueue(role, {
              scheduledDate: selectedDate,
              includeHistory: true,
            }),
          ]);
          if (!active) {
            return;
          }

          setAppointments(appointmentResponse.items);
          setQueueEntries(queueResponse.items);
        }

        setError(null);
        setLastRefreshedAt(new Date());
      } catch (loadError) {
        if (!active) {
          return;
        }

        setAppointments([]);
        setQueueEntries([]);
        setError(loadError instanceof Error ? loadError.message : "Unable to load queue data");
      } finally {
        if (active) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void loadData();

    return () => {
      active = false;
    };
  }, [doctorProfileId, isDoctor, reloadToken, role, selectedDate]);

  const nowSeeing = useMemo(
    () => queueEntries.find((entry) => entry.queue_status === "in_progress") ?? null,
    [queueEntries],
  );
  const nextPatient = useMemo(
    () => queueEntries.find((entry) => entry.queue_status === "waiting") ?? null,
    [queueEntries],
  );
  const waitingCount = useMemo(
    () => queueEntries.filter((entry) => entry.queue_status === "waiting").length,
    [queueEntries],
  );
  const inProgressCount = useMemo(
    () => queueEntries.filter((entry) => entry.queue_status === "in_progress").length,
    [queueEntries],
  );
  const completedCount = useMemo(
    () => queueEntries.filter((entry) => entry.queue_status === "completed").length,
    [queueEntries],
  );

  const consultDurationsMinutes = useMemo(
    () =>
      queueEntries
        .filter((entry) => entry.called_at && entry.completed_at && entry.queue_status === "completed")
        .map((entry) => {
          const startedAt = new Date(entry.called_at as string).getTime();
          const endedAt = new Date(entry.completed_at as string).getTime();
          if (Number.isNaN(startedAt) || Number.isNaN(endedAt) || endedAt <= startedAt) {
            return null;
          }

          const minutes = Math.round((endedAt - startedAt) / (1000 * 60));
          if (minutes <= 0 || minutes > 240) {
            return null;
          }
          return minutes;
        })
        .filter((value): value is number => value !== null),
    [queueEntries],
  );

  const averageConsultMinutes = useMemo(() => {
    if (consultDurationsMinutes.length < 2) {
      return null;
    }

    const total = consultDurationsMinutes.reduce((sum, value) => sum + value, 0);
    return Math.round(total / consultDurationsMinutes.length);
  }, [consultDurationsMinutes]);

  const averageWaitEstimateMinutes = useMemo(() => {
    if (averageConsultMinutes === null || waitingCount === 0) {
      return null;
    }

    const queueUnitsAhead = waitingCount + (nowSeeing ? 1 : 0);
    return Math.max(1, queueUnitsAhead * averageConsultMinutes);
  }, [averageConsultMinutes, nowSeeing, waitingCount]);

  async function handleCheckIn(appointment: Appointment) {
    setActionError(null);
    const assignedDoctorRaw = assignedDoctorByAppointment[appointment.id] ?? "";
    const assignedDoctorId = assignedDoctorRaw.trim();
    if (assignedDoctorId && !isValidUuid(assignedDoctorId)) {
      setActionError("Assigned doctor ID must be a valid UUID.");
      return;
    }

    setBusyAppointmentId(appointment.id);
    try {
      await checkInAppointment(
        role,
        appointment.id,
        assignedDoctorId ? { assigned_doctor_id: assignedDoctorId } : undefined,
        isDoctor ? doctorProfileId : undefined,
      );
      setReloadToken((current) => current + 1);
    } catch (actionFailure) {
      setActionError(actionFailure instanceof Error ? actionFailure.message : "Unable to check in appointment");
    } finally {
      setBusyAppointmentId(null);
    }
  }

  async function handleQueueAction(appointmentId: string, action: "call" | "complete" | "skip") {
    setActionError(null);
    setBusyAppointmentId(appointmentId);
    try {
      if (action === "call") {
        await callQueueEntry(role, appointmentId, isDoctor ? doctorProfileId : undefined);
      }
      if (action === "complete") {
        await completeQueueEntry(role, appointmentId, isDoctor ? doctorProfileId : undefined);
      }
      if (action === "skip") {
        await skipQueueEntry(role, appointmentId, isDoctor ? doctorProfileId : undefined);
      }
      setReloadToken((current) => current + 1);
    } catch (actionFailure) {
      setActionError(actionFailure instanceof Error ? actionFailure.message : "Unable to update queue state");
    } finally {
      setBusyAppointmentId(null);
    }
  }

  async function handleCallNext() {
    if (!nextPatient) {
      return;
    }

    await handleQueueAction(nextPatient.appointment_id, "call");
  }

  function handleSaveDoctorProfile() {
    const nextDoctorId = draftDoctorId.trim();
    if (!nextDoctorId) {
      setError("Doctor profile ID is required.");
      return;
    }
    if (!isValidUuid(nextDoctorId)) {
      setError("Doctor profile ID must be a valid UUID.");
      return;
    }

    storeDoctorProfileId(nextDoctorId);
    storeDoctorDisplayName(draftDoctorName);
    setDoctorProfileId(nextDoctorId);
    setDoctorDisplayName(draftDoctorName.trim());
    setError(null);
    setReloadToken((current) => current + 1);
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Smart queue</p>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
              {isDoctor ? "Doctor Queue Dashboard" : "Reception Queue Control"}
            </h2>
            <p className="text-sm text-slate-500">
              {isDoctor
                ? "Track now seeing, next patient, and complete assigned queue actions."
                : "Check in today’s appointments and progress patient flow with quick actions."}
            </p>
            <p className="text-xs text-slate-500">
              Auto-refresh every 20 seconds{lastRefreshedAt ? ` · Last updated ${formatTimestamp(lastRefreshedAt.toISOString())}` : ""}
            </p>
          </div>
          <button
            className={secondaryButtonClass}
            type="button"
            onClick={() => setReloadToken((current) => current + 1)}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </section>

      {isDoctor ? (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] md:items-end">
            <label className="space-y-2">
              <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Doctor profile ID</span>
              <input
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                value={draftDoctorId}
                onChange={(event) => setDraftDoctorId(event.target.value)}
                placeholder="UUID from doctor account"
              />
            </label>
            <label className="space-y-2">
              <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Display name</span>
              <input
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                value={draftDoctorName}
                onChange={(event) => setDraftDoctorName(event.target.value)}
                placeholder="e.g. Dr. Sana"
              />
            </label>
            <button className={primaryButtonClass} type="button" onClick={handleSaveDoctorProfile}>
              Save profile
            </button>
          </div>
          {doctorDisplayName ? <p className="mt-2 text-sm text-slate-500">Signed in as {doctorDisplayName}</p> : null}
        </section>
      ) : null}

      {error ? (
        <section className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <p>{error}</p>
        </section>
      ) : null}
      {actionError ? (
        <section className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <p>{actionError}</p>
        </section>
      ) : null}
      {loading ? (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Loading queue data...</p>
        </section>
      ) : null}

      {isDoctor && !loading ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <DoctorMetricCard
              title="Now seeing"
              icon={Stethoscope}
              accentClass="bg-sky-50 text-sky-700"
              value={nowSeeing ? `${nowSeeing.patient_name} · #${nowSeeing.queue_number}` : "No active patient"}
            />
            <DoctorMetricCard
              title="Next patient"
              icon={UserRoundCheck}
              accentClass="bg-amber-50 text-amber-700"
              value={nextPatient ? `${nextPatient.patient_name} · #${nextPatient.queue_number}` : "Queue clear"}
            />
            <DoctorMetricCard
              title="Waiting count"
              icon={Timer}
              accentClass="bg-indigo-50 text-indigo-700"
              value={String(waitingCount)}
            />
            <DoctorMetricCard
              title="Avg wait estimate"
              icon={Timer}
              accentClass="bg-emerald-50 text-emerald-700"
              value={averageWaitEstimateMinutes !== null ? `~${averageWaitEstimateMinutes} min` : "Insufficient data"}
              note={
                averageWaitEstimateMinutes !== null
                  ? "Based on today's completed consult durations."
                  : "Needs at least 2 completed queue records today."
              }
            />
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-medium text-slate-900">Assigned queue</h3>
                <p className="text-sm text-slate-500">Only your queue is shown for {selectedDate}.</p>
              </div>
              <button
                className={primaryButtonClass}
                type="button"
                onClick={() => void handleCallNext()}
                disabled={!nextPatient || busyAppointmentId !== null}
              >
                <ClipboardCheck className="h-4 w-4" />
                Call next
              </button>
            </div>
            <QueueEntriesTable
              entries={queueEntries}
              busyAppointmentId={busyAppointmentId}
              onCall={(appointmentId) => void handleQueueAction(appointmentId, "call")}
              onComplete={(appointmentId) => void handleQueueAction(appointmentId, "complete")}
              onSkip={(appointmentId) => void handleQueueAction(appointmentId, "skip")}
              emptyMessage="No patients in your queue. Reception can check in and assign patients to you."
            />
          </section>
        </>
      ) : null}

      {!isDoctor && !loading ? (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <DoctorMetricCard
              title="Waiting"
              icon={Timer}
              accentClass="bg-amber-50 text-amber-700"
              value={String(waitingCount)}
            />
            <DoctorMetricCard
              title="In progress"
              icon={UserRoundCheck}
              accentClass="bg-sky-50 text-sky-700"
              value={String(inProgressCount)}
            />
            <DoctorMetricCard
              title="Completed"
              icon={ClipboardCheck}
              accentClass="bg-emerald-50 text-emerald-700"
              value={String(completedCount)}
            />
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-medium text-slate-900">Today's appointments</h3>
                <p className="text-sm text-slate-500">Check in scheduled patients and assign queue numbers.</p>
              </div>
              <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 ring-1 ring-inset ring-slate-200">
                {appointments.length} appointments
              </span>
            </div>

            {appointments.length === 0 ? (
              <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
                <p className="text-sm text-slate-600">No appointments scheduled for today.</p>
                {isAdmin ? (
                  <Link className={`${secondaryButtonClass} mt-4`} to="/appointments/new">
                    Create appointment
                  </Link>
                ) : null}
              </div>
            ) : (
              <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
                <table className="min-w-[900px] w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-4 py-3 text-left font-medium">Patient</th>
                      <th className="px-4 py-3 text-left font-medium">Scheduled</th>
                      <th className="px-4 py-3 text-left font-medium">Appointment status</th>
                      <th className="px-4 py-3 text-left font-medium">Queue</th>
                      <th className="px-4 py-3 text-left font-medium">Assign doctor (optional)</th>
                      <th className="px-4 py-3 text-left font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white text-slate-700">
                    {appointments.map((appointment) => {
                      const isCheckedIn = appointment.queue_status !== null;
                      return (
                        <tr
                          className={`transition duration-200 hover:bg-slate-50 ${getAppointmentRowClass(appointment)}`}
                          key={appointment.id}
                        >
                          <td className="px-4 py-3">
                            <p className="font-medium text-slate-900">{findPatientLabel(appointment, queueEntries)}</p>
                            <p className="text-xs text-slate-500">{appointment.patient_id}</p>
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-600">{formatTimestamp(appointment.scheduled_for)}</td>
                          <td className="px-4 py-3">
                            <StatusBadge label={formatAppointmentStatus(appointment.status)} tone={appointment.status} />
                          </td>
                          <td className="px-4 py-3">
                            {isCheckedIn && appointment.queue_status ? (
                              <div className="flex items-center gap-2">
                                <span className="inline-flex items-center rounded-lg border border-indigo-200 bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-700">
                                  #{appointment.queue_number}
                                </span>
                                <StatusBadge
                                  label={formatQueueStatus(appointment.queue_status)}
                                  tone={appointment.queue_status}
                                />
                              </div>
                            ) : (
                              <span className="text-xs text-slate-500">Not checked in</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <input
                              className="w-56 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                              value={assignedDoctorByAppointment[appointment.id] ?? ""}
                              onChange={(event) =>
                                setAssignedDoctorByAppointment((current) => ({
                                  ...current,
                                  [appointment.id]: event.target.value,
                                }))
                              }
                              placeholder="Doctor UUID"
                              disabled={isCheckedIn}
                            />
                          </td>
                          <td className="px-4 py-3">
                            <button
                              className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition duration-200 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                              type="button"
                              onClick={() => void handleCheckIn(appointment)}
                              disabled={
                                isCheckedIn || appointment.status !== "scheduled" || busyAppointmentId === appointment.id
                              }
                            >
                              {busyAppointmentId === appointment.id ? "Processing..." : "Check in"}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-medium text-slate-900">Live queue board</h3>
                <p className="text-sm text-slate-500">Quickly call, complete, or skip checked-in patients.</p>
              </div>
              <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 ring-1 ring-inset ring-slate-200">
                {queueEntries.length} in queue
              </span>
            </div>
            <QueueEntriesTable
              entries={queueEntries}
              busyAppointmentId={busyAppointmentId}
              onCall={(appointmentId) => void handleQueueAction(appointmentId, "call")}
              onComplete={(appointmentId) => void handleQueueAction(appointmentId, "complete")}
              onSkip={(appointmentId) => void handleQueueAction(appointmentId, "skip")}
              emptyMessage="No checked-in patients yet. Use check-in on scheduled appointments to populate the queue."
            />
          </section>
        </>
      ) : null}

      {isAdmin ? (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Admin mode includes receptionist queue controls and can also access standard appointment workflows.
          </p>
        </section>
      ) : null}
    </div>
  );
}

interface QueueEntriesTableProps {
  entries: QueueEntry[];
  busyAppointmentId: string | null;
  onCall: (appointmentId: string) => void;
  onComplete: (appointmentId: string) => void;
  onSkip: (appointmentId: string) => void;
  emptyMessage: string;
}

function QueueEntriesTable({
  entries,
  busyAppointmentId,
  onCall,
  onComplete,
  onSkip,
  emptyMessage,
}: QueueEntriesTableProps) {
  if (entries.length === 0) {
    return (
      <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
        <p className="text-sm text-slate-600">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-[920px] w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 text-left font-medium">Queue</th>
            <th className="px-4 py-3 text-left font-medium">Patient</th>
            <th className="px-4 py-3 text-left font-medium">Scheduled</th>
            <th className="px-4 py-3 text-left font-medium">Queue status</th>
            <th className="px-4 py-3 text-left font-medium">Appointment status</th>
            <th className="px-4 py-3 text-left font-medium">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white text-slate-700">
          {entries.map((entry) => {
            const isBusy = busyAppointmentId === entry.appointment_id;
            const canCall = entry.queue_status === "waiting";
            const canComplete = entry.queue_status === "in_progress";
            const canSkip = entry.queue_status === "waiting" || entry.queue_status === "in_progress";

            return (
              <tr
                className={`transition duration-200 hover:bg-slate-50 ${getQueueRowClass(entry.queue_status)}`}
                key={entry.appointment_id}
              >
                <td className="px-4 py-3">
                  <span className="inline-flex items-center rounded-lg border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700">
                    #{entry.queue_number}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-900">{entry.patient_name}</p>
                  <p className="text-xs text-slate-500">{entry.patient_record_number}</p>
                </td>
                <td className="px-4 py-3 text-sm text-slate-600">{formatTimestamp(entry.scheduled_for)}</td>
                <td className="px-4 py-3">
                  <StatusBadge label={formatQueueStatus(entry.queue_status)} tone={entry.queue_status} />
                </td>
                <td className="px-4 py-3">
                  <StatusBadge label={formatAppointmentStatus(entry.appointment_status)} tone={entry.appointment_status} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      className="inline-flex items-center gap-1 rounded-lg border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs font-medium text-sky-700 transition duration-200 hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-60"
                      type="button"
                      onClick={() => onCall(entry.appointment_id)}
                      disabled={!canCall || isBusy}
                    >
                      <UserRoundCheck className="h-3.5 w-3.5" />
                      Call
                    </button>
                    <button
                      className="inline-flex items-center gap-1 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 transition duration-200 hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-60"
                      type="button"
                      onClick={() => onComplete(entry.appointment_id)}
                      disabled={!canComplete || isBusy}
                    >
                      <ClipboardCheck className="h-3.5 w-3.5" />
                      Complete
                    </button>
                    <button
                      className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition duration-200 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                      type="button"
                      onClick={() => onSkip(entry.appointment_id)}
                      disabled={!canSkip || isBusy}
                    >
                      <SkipForward className="h-3.5 w-3.5" />
                      Skip
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function DoctorMetricCard({
  title,
  icon: Icon,
  accentClass,
  value,
  note,
}: {
  title: string;
  icon: LucideIcon;
  accentClass: string;
  value: string;
  note?: string;
}) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-600">{title}</p>
        <span className={`inline-flex h-9 w-9 items-center justify-center rounded-lg ${accentClass}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="mt-3 text-lg font-semibold tracking-tight text-slate-900">{value}</p>
      {note ? <p className="mt-1 text-xs text-slate-500">{note}</p> : null}
    </article>
  );
}

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString();
}

function formatAppointmentStatus(status: AppointmentStatus): string {
  if (status === "no_show") {
    return "No-show";
  }
  return `${status.slice(0, 1).toUpperCase()}${status.slice(1)}`;
}

function formatQueueStatus(status: QueueEntry["queue_status"]): string {
  if (status === "in_progress") {
    return "In progress";
  }
  return `${status.slice(0, 1).toUpperCase()}${status.slice(1)}`;
}

function findPatientLabel(appointment: Appointment, queueEntries: QueueEntry[]): string {
  const queueEntry = queueEntries.find((entry) => entry.appointment_id === appointment.id);
  if (queueEntry) {
    return queueEntry.patient_name;
  }

  return `Patient ${appointment.patient_id.slice(0, 8)}`;
}

function buildDayRange(scheduledDate: string): { startsAt: string; endsAt: string } {
  const [year, month, day] = scheduledDate.split("-").map((value) => Number.parseInt(value, 10));
  const start = new Date(year, month - 1, day, 0, 0, 0, 0);
  const end = new Date(year, month - 1, day, 23, 59, 59, 999);

  return {
    startsAt: start.toISOString(),
    endsAt: end.toISOString(),
  };
}

function getQueueRowClass(status: QueueEntry["queue_status"]): string {
  if (status === "in_progress") {
    return "bg-sky-50/40";
  }
  if (status === "waiting") {
    return "bg-amber-50/30";
  }
  if (status === "completed") {
    return "bg-emerald-50/25";
  }
  return "bg-slate-50/40";
}

function getAppointmentRowClass(appointment: Appointment): string {
  if (!appointment.queue_status) {
    return "";
  }
  return getQueueRowClass(appointment.queue_status);
}

function isValidUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}
