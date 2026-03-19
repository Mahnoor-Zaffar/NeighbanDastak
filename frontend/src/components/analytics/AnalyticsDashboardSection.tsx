import { useEffect, useMemo, useState, type ChangeEvent } from "react";
import { Activity, BarChart3, CalendarCheck2, ClipboardCheck, RefreshCw, Users } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getAnalyticsAppointmentStatusBreakdown,
  getAnalyticsAppointmentsByDay,
  getAnalyticsDoctorWorkload,
  getAnalyticsSummary,
  type AnalyticsAppointmentStatusBreakdownItem,
  type AnalyticsAppointmentStatusBreakdownResponse,
  type AnalyticsAppointmentsByDayResponse,
  type AnalyticsDoctorWorkloadResponse,
  type AnalyticsSummaryResponse,
  type DemoRole,
} from "../../app/api";
import { getStoredDoctorProfileId } from "../../app/doctorIdentity";

interface AnalyticsDashboardSectionProps {
  role: DemoRole;
}

type DateRangePreset = "7d" | "14d" | "30d" | "custom";

interface DoctorFilterOption {
  id: string;
  name: string;
}

const STATUS_COLORS: Record<string, string> = {
  scheduled: "#3b82f6",
  completed: "#10b981",
  cancelled: "#f97316",
  no_show: "#64748b",
};

const DATE_RANGE_PRESETS: Array<{ value: DateRangePreset; label: string; days?: number }> = [
  { value: "7d", label: "Last 7 days", days: 7 },
  { value: "14d", label: "Last 14 days", days: 14 },
  { value: "30d", label: "Last 30 days", days: 30 },
  { value: "custom", label: "Custom range" },
];

const MAX_ANALYTICS_DAYS = 90;

export function AnalyticsDashboardSection({ role }: AnalyticsDashboardSectionProps) {
  const doctorProfileId = getStoredDoctorProfileId().trim();
  const actorUserId = role === "doctor" ? doctorProfileId : undefined;
  const requiresDoctorIdentity = role === "doctor" && !doctorProfileId;
  const canFilterByDoctor = role === "admin";

  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null);
  const [appointmentsByDay, setAppointmentsByDay] = useState<AnalyticsAppointmentsByDayResponse | null>(null);
  const [statusBreakdown, setStatusBreakdown] = useState<AnalyticsAppointmentStatusBreakdownResponse | null>(null);
  const [doctorWorkload, setDoctorWorkload] = useState<AnalyticsDoctorWorkloadResponse | null>(null);
  const [doctorOptions, setDoctorOptions] = useState<DoctorFilterOption[]>([]);

  const [datePreset, setDatePreset] = useState<DateRangePreset>("14d");
  const [startsOn, setStartsOn] = useState(() => toDateInput(addDays(new Date(), -13)));
  const [endsOn, setEndsOn] = useState(() => toDateInput(new Date()));
  const [selectedDoctorId, setSelectedDoctorId] = useState("all");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const sectionTitle =
    role === "admin" ? "Clinic analytics overview" : role === "doctor" ? "My analytics overview" : "Operational analytics overview";

  const resolvedRange = useMemo(() => resolveDateRange(datePreset, startsOn, endsOn), [datePreset, startsOn, endsOn]);
  const selectedDoctorFilter = canFilterByDoctor && selectedDoctorId !== "all" ? selectedDoctorId : undefined;

  useEffect(() => {
    if (requiresDoctorIdentity) {
      setSummary(null);
      setAppointmentsByDay(null);
      setStatusBreakdown(null);
      setDoctorWorkload(null);
      setLoading(false);
      setError("Doctor profile is not linked to this session. Switch demo user and try again.");
      return;
    }

    if (!resolvedRange.ok) {
      setSummary(null);
      setAppointmentsByDay(null);
      setStatusBreakdown(null);
      setDoctorWorkload(null);
      setLoading(false);
      setError(resolvedRange.error);
      return;
    }
    const range = resolvedRange;

    let active = true;

    async function loadAnalytics() {
      if (reloadToken > 0) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      try {
        const { startsOn: rangeStartsOn, endsOn: rangeEndsOn, days } = range;

        const optionsDirectoryPromise = canFilterByDoctor
          ? getAnalyticsDoctorWorkload(role, {
              startsOn: rangeStartsOn,
              endsOn: rangeEndsOn,
            })
          : Promise.resolve<AnalyticsDoctorWorkloadResponse | null>(null);

        const [summaryResponse, byDayResponse, breakdownResponse, workloadResponse, optionsDirectory] = await Promise.all([
          getAnalyticsSummary(role, { actorUserId, doctorId: selectedDoctorFilter }),
          getAnalyticsAppointmentsByDay(role, {
            days,
            endsOn: rangeEndsOn,
            actorUserId,
            doctorId: selectedDoctorFilter,
          }),
          getAnalyticsAppointmentStatusBreakdown(role, {
            startsOn: rangeStartsOn,
            endsOn: rangeEndsOn,
            actorUserId,
            doctorId: selectedDoctorFilter,
          }),
          getAnalyticsDoctorWorkload(role, {
            startsOn: rangeStartsOn,
            endsOn: rangeEndsOn,
            actorUserId,
            doctorId: selectedDoctorFilter,
          }),
          optionsDirectoryPromise,
        ]);
        if (!active) {
          return;
        }

        setSummary(summaryResponse);
        setAppointmentsByDay(byDayResponse);
        setStatusBreakdown(breakdownResponse);
        setDoctorWorkload(workloadResponse);

        if (canFilterByDoctor && optionsDirectory) {
          const options = optionsDirectory.items.map((item) => ({ id: item.doctor_id, name: item.doctor_name }));
          setDoctorOptions(options);
          if (selectedDoctorId !== "all" && !options.some((option) => option.id === selectedDoctorId)) {
            setSelectedDoctorId("all");
          }
        }

        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setSummary(null);
        setAppointmentsByDay(null);
        setStatusBreakdown(null);
        setDoctorWorkload(null);
        setError(loadError instanceof Error ? loadError.message : "Unable to load analytics");
      } finally {
        if (active) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void loadAnalytics();
    return () => {
      active = false;
    };
  }, [
    actorUserId,
    canFilterByDoctor,
    reloadToken,
    requiresDoctorIdentity,
    resolvedRange,
    role,
    selectedDoctorFilter,
    selectedDoctorId,
  ]);

  const appointmentsByDayChartData = useMemo(
    () =>
      (appointmentsByDay?.items ?? []).map((item) => ({
        ...item,
        day_label: formatDayTick(item.day),
      })),
    [appointmentsByDay],
  );

  const statusBreakdownChartData = useMemo(
    () =>
      (statusBreakdown?.items ?? []).map((item) => ({
        ...item,
        status_label: formatStatusLabel(item.status),
      })),
    [statusBreakdown],
  );

  const hasAnyChartData =
    (appointmentsByDay?.items.length ?? 0) > 0 || (statusBreakdown?.items.length ?? 0) > 0 || (doctorWorkload?.items.length ?? 0) > 0;

  const summaryShowsNoOperationalData = summary
    ? summary.total_patients === 0 &&
      summary.appointments_today === 0 &&
      summary.appointments_this_week === 0 &&
      summary.completed_visits_today === 0
    : false;

  const selectedDoctorName =
    selectedDoctorId === "all" ? "All doctors" : doctorOptions.find((option) => option.id === selectedDoctorId)?.name ?? "Selected doctor";

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <h3 className="text-xl font-semibold tracking-tight text-slate-900">{sectionTitle}</h3>
          <p className="text-sm text-slate-500">Monitor volume, visit conversion, status mix, and doctor workload with lightweight filters.</p>
        </div>
        <button
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition duration-200 hover:bg-slate-50"
          type="button"
          onClick={() => setReloadToken((current) => current + 1)}
          disabled={refreshing}
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Date range</span>
            <select
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
              value={datePreset}
              onChange={(event: ChangeEvent<HTMLSelectElement>) => handleDatePresetChange(event, setDatePreset, setStartsOn, setEndsOn)}
            >
              {DATE_RANGE_PRESETS.map((preset) => (
                <option key={preset.value} value={preset.value}>
                  {preset.label}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Start date</span>
            <input
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100 disabled:text-slate-400"
              type="date"
              value={startsOn}
              onChange={(event) => {
                setDatePreset("custom");
                setStartsOn(event.target.value);
              }}
              disabled={datePreset !== "custom"}
            />
          </label>

          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">End date</span>
            <input
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100 disabled:text-slate-400"
              type="date"
              value={endsOn}
              onChange={(event) => {
                setDatePreset("custom");
                setEndsOn(event.target.value);
              }}
              disabled={datePreset !== "custom"}
            />
          </label>

          {canFilterByDoctor ? (
            <label className="space-y-1">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Doctor</span>
              <select
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
                value={selectedDoctorId}
                onChange={(event) => setSelectedDoctorId(event.target.value)}
              >
                <option value="all">All doctors</option>
                {doctorOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.name}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <div className="space-y-1">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Scope</span>
              <p className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                {summary?.scope === "doctor" ? "Doctor scope" : "Clinic scope"}
              </p>
            </div>
          )}

          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Active filter</span>
            <p className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
              {resolvedRange.ok ? `${resolvedRange.startsOn} to ${resolvedRange.endsOn}` : "Invalid range"}
              {canFilterByDoctor ? ` · ${selectedDoctorName}` : ""}
            </p>
          </div>
        </div>
      </div>

      {loading ? <p className="mt-4 text-sm text-slate-500">Loading analytics...</p> : null}

      {error ? (
        <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <p>{error}</p>
        </div>
      ) : null}

      {!loading && !error && summary ? (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              icon={Users}
              title="Total Patients"
              value={String(summary.total_patients)}
              note={summary.scope === "doctor" ? "Patients in your schedule" : "Active patient records"}
              accentClassName="bg-indigo-50 text-indigo-700"
              emphasis
            />
            <MetricCard
              icon={CalendarCheck2}
              title="Appointments Today"
              value={String(summary.appointments_today)}
              note="Scheduled on current date"
              accentClassName="bg-amber-50 text-amber-700"
              emphasis
            />
            <MetricCard
              icon={ClipboardCheck}
              title="Completed Visits"
              value={String(summary.completed_visits_today)}
              note="Visits completed today"
              accentClassName="bg-emerald-50 text-emerald-700"
            />
            <MetricCard
              icon={Activity}
              title="Active Doctors"
              value={String(summary.active_doctors)}
              note={summary.scope === "doctor" ? "Scoped to your profile" : "Active clinic doctors"}
              accentClassName="bg-sky-50 text-sky-700"
            />
          </div>

          <div className="mt-3">
            <MetricStrip
              icon={BarChart3}
              title="Appointments This Week"
              value={String(summary.appointments_this_week)}
              note={`Recent growth: ${formatGrowth(summary.recent_appointments_7d, summary.recent_appointments_previous_7d)}`}
            />
          </div>

          {summaryShowsNoOperationalData && !hasAnyChartData ? (
            <div className="mt-5 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-600">
              No analytics records are available for this period yet. Try expanding the range or selecting all doctors.
            </div>
          ) : (
            <div className="mt-5 grid gap-4 xl:grid-cols-3">
              <article className="rounded-lg border border-slate-200 bg-slate-50 p-4 xl:col-span-2">
                <div className="mb-3 space-y-1">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Appointments by day</p>
                  <p className="text-sm text-slate-600">Daily appointment trend for the selected period.</p>
                </div>
                <div className="h-72">
                  {appointmentsByDayChartData.length === 0 ? (
                    <EmptyChartState label="No appointment trend data in this filter." />
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={appointmentsByDayChartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                        <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                        <XAxis dataKey="day_label" tick={{ fontSize: 12 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                        <Tooltip formatter={(value: number) => [value, "Appointments"]} labelFormatter={(label) => `Day: ${label}`} />
                        <Line
                          type="monotone"
                          dataKey="appointments_count"
                          stroke="#2563eb"
                          strokeWidth={2}
                          dot={{ r: 2 }}
                          activeDot={{ r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </article>

              <article className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="mb-3 space-y-1">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Status breakdown</p>
                  <p className="text-sm text-slate-600">Appointment status distribution for selected dates.</p>
                </div>
                <div className="h-72">
                  {statusBreakdownChartData.every((item) => item.count === 0) ? (
                    <EmptyChartState label="No appointment status data in this filter." />
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={statusBreakdownChartData} dataKey="count" nameKey="status_label" innerRadius={52} outerRadius={84} paddingAngle={2}>
                          {statusBreakdownChartData.map((item: AnalyticsAppointmentStatusBreakdownItem) => (
                            <Cell key={item.status} fill={STATUS_COLORS[item.status] ?? "#94a3b8"} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value: number, name: string) => [value, name]} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </article>

              <article className="rounded-lg border border-slate-200 bg-slate-50 p-4 xl:col-span-3">
                <div className="mb-3 space-y-1">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Doctor workload</p>
                  <p className="text-sm text-slate-600">
                    {summary.scope === "doctor"
                      ? "Your workload in the selected date range."
                      : "Appointment count by doctor in the selected date range."}
                  </p>
                </div>
                <div className="h-72">
                  {(doctorWorkload?.items.length ?? 0) === 0 ? (
                    <EmptyChartState label="No workload data in this filter." />
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={doctorWorkload?.items ?? []} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                        <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                        <XAxis dataKey="doctor_name" tick={{ fontSize: 12 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                        <Tooltip formatter={(value: number) => [value, "Appointments"]} />
                        <Bar dataKey="appointments_count" fill="#0f766e" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </article>
            </div>
          )}
        </>
      ) : null}
    </section>
  );
}

interface MetricCardProps {
  icon: typeof Users;
  title: string;
  value: string;
  note: string;
  accentClassName: string;
  emphasis?: boolean;
}

function MetricCard({ icon: Icon, title, value, note, accentClassName, emphasis = false }: MetricCardProps) {
  return (
    <article className={`rounded-lg border border-slate-200 p-3.5 ${emphasis ? "bg-white shadow-sm" : "bg-slate-50"}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
          <p className="text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
          <p className="text-xs text-slate-500">{note}</p>
        </div>
        <span className={`inline-flex h-8 w-8 items-center justify-center rounded-lg ${accentClassName}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
    </article>
  );
}

interface MetricStripProps {
  icon: typeof BarChart3;
  title: string;
  value: string;
  note: string;
}

function MetricStrip({ icon: Icon, title, value, note }: MetricStripProps) {
  return (
    <article className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
          <p className="text-xs text-slate-500">{note}</p>
        </div>
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-violet-50 text-violet-700">
          <Icon className="h-5 w-5" />
        </span>
      </div>
    </article>
  );
}

function EmptyChartState({ label }: { label: string }) {
  return (
    <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
      {label}
    </div>
  );
}

function handleDatePresetChange(
  event: ChangeEvent<HTMLSelectElement>,
  setDatePreset: (value: DateRangePreset) => void,
  setStartsOn: (value: string) => void,
  setEndsOn: (value: string) => void,
): void {
  const value = event.target.value as DateRangePreset;
  setDatePreset(value);
  if (value === "custom") {
    return;
  }

  const preset = DATE_RANGE_PRESETS.find((item) => item.value === value);
  const days = preset?.days ?? 14;
  const end = new Date();
  const start = addDays(end, -(days - 1));
  setStartsOn(toDateInput(start));
  setEndsOn(toDateInput(end));
}

function resolveDateRange(datePreset: DateRangePreset, startsOn: string, endsOn: string):
  | { ok: true; startsOn: string; endsOn: string; days: number }
  | { ok: false; error: string } {
  if (datePreset !== "custom") {
    const preset = DATE_RANGE_PRESETS.find((item) => item.value === datePreset);
    const days = preset?.days ?? 14;
    const end = new Date();
    const start = addDays(end, -(days - 1));
    return {
      ok: true,
      startsOn: toDateInput(start),
      endsOn: toDateInput(end),
      days,
    };
  }

  if (!startsOn || !endsOn) {
    return { ok: false, error: "Select both start and end dates for custom range." };
  }

  const start = parseDateInput(startsOn);
  const end = parseDateInput(endsOn);
  if (!start || !end) {
    return { ok: false, error: "Use valid dates for analytics range." };
  }
  if (start > end) {
    return { ok: false, error: "Start date cannot be after end date." };
  }

  const days = diffDaysInclusive(start, end);
  if (days > MAX_ANALYTICS_DAYS) {
    return { ok: false, error: `Date range cannot exceed ${MAX_ANALYTICS_DAYS} days.` };
  }

  return {
    ok: true,
    startsOn,
    endsOn,
    days,
  };
}

function addDays(value: Date, days: number): Date {
  const next = new Date(value);
  next.setDate(next.getDate() + days);
  return next;
}

function parseDateInput(value: string): Date | null {
  if (!value) {
    return null;
  }
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function diffDaysInclusive(startsOn: Date, endsOn: Date): number {
  const msPerDay = 24 * 60 * 60 * 1000;
  return Math.floor((endsOn.getTime() - startsOn.getTime()) / msPerDay) + 1;
}

function toDateInput(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDayTick(value: string): string {
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function formatStatusLabel(status: string): string {
  if (status === "no_show") {
    return "No-show";
  }
  return status.replace("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatGrowth(current: number, previous: number): string {
  if (previous <= 0) {
    return current > 0 ? `+${current} vs previous window` : "No change";
  }

  const delta = current - previous;
  const percent = Math.round((Math.abs(delta) / previous) * 100);
  if (delta === 0) {
    return "0% vs previous window";
  }
  return `${delta > 0 ? "+" : "-"}${percent}% vs previous window`;
}
