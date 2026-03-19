import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CalendarDays, CheckCircle2, Clock3, RefreshCw } from "lucide-react";

import {
  cancelFollowUp,
  completeFollowUp,
  listFollowUps,
  type DemoRole,
  type FollowUp,
  type FollowUpStatus,
} from "../../app/api";
import { StatusBadge } from "../ui/StatusBadge";

type FollowUpWindowFilter = "all" | "due_today" | "overdue" | "upcoming";
type FollowUpSort = "due_asc" | "due_desc" | "created_desc" | "created_asc";

interface FollowUpDashboardSectionProps {
  role: DemoRole;
}

const WINDOW_OPTIONS: Array<{ value: FollowUpWindowFilter; label: string }> = [
  { value: "all", label: "All windows" },
  { value: "due_today", label: "Due today" },
  { value: "overdue", label: "Overdue" },
  { value: "upcoming", label: "Upcoming" },
];

const STATUS_OPTIONS: Array<{ value: "all" | FollowUpStatus; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "overdue", label: "Overdue" },
  { value: "completed", label: "Completed" },
  { value: "cancelled", label: "Cancelled" },
];

const SORT_OPTIONS: Array<{ value: FollowUpSort; label: string }> = [
  { value: "due_asc", label: "Due date (oldest first)" },
  { value: "due_desc", label: "Due date (newest first)" },
  { value: "created_desc", label: "Created (newest first)" },
  { value: "created_asc", label: "Created (oldest first)" },
];

export function FollowUpDashboardSection({ role }: FollowUpDashboardSectionProps) {
  const [items, setItems] = useState<FollowUp[]>([]);
  const [windowFilter, setWindowFilter] = useState<FollowUpWindowFilter>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | FollowUpStatus>("all");
  const [sortBy, setSortBy] = useState<FollowUpSort>("due_asc");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const canManage = role === "doctor" || role === "admin";
  const todayIso = toDateOnly(new Date());

  useEffect(() => {
    if (!canManage) {
      setItems([]);
      setLoading(false);
      setError(null);
      return;
    }

    let active = true;

    async function loadData() {
      if (items.length > 0) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setActionError(null);
      try {
        const response = await listFollowUps(role, {
          limit: 100,
          offset: 0,
        });
        if (!active) {
          return;
        }
        setItems(response.items);
        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setItems([]);
        setError(loadError instanceof Error ? loadError.message : "Unable to load follow-up reminders");
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
  }, [canManage, reloadToken, role]);

  const dueTodayItems = useMemo(
    () =>
      sortItems(
        items.filter((item) => item.status === "pending" && item.due_date === todayIso),
        "due_asc",
      ),
    [items, todayIso],
  );
  const overdueItems = useMemo(
    () =>
      sortItems(
        items.filter((item) => item.status === "overdue"),
        "due_asc",
      ),
    [items],
  );
  const upcomingItems = useMemo(
    () =>
      sortItems(
        items.filter((item) => item.status === "pending" && item.due_date > todayIso),
        "due_asc",
      ),
    [items, todayIso],
  );

  const filteredItems = useMemo(() => {
    let next = [...items];

    if (windowFilter === "due_today") {
      next = next.filter((item) => item.status === "pending" && item.due_date === todayIso);
    }
    if (windowFilter === "overdue") {
      next = next.filter((item) => item.status === "overdue");
    }
    if (windowFilter === "upcoming") {
      next = next.filter((item) => item.status === "pending" && item.due_date > todayIso);
    }

    if (statusFilter !== "all") {
      next = next.filter((item) => item.status === statusFilter);
    }

    return sortItems(next, sortBy);
  }, [items, sortBy, statusFilter, todayIso, windowFilter]);

  async function handleTransition(followUp: FollowUp, action: "complete" | "cancel") {
    if (!canManage) {
      return;
    }
    if (followUp.status !== "pending" && followUp.status !== "overdue") {
      return;
    }

    setActionError(null);
    setBusyId(followUp.id);
    try {
      if (action === "complete") {
        await completeFollowUp(role, followUp.id);
      } else {
        await cancelFollowUp(role, followUp.id);
      }
      setReloadToken((current) => current + 1);
    } catch (transitionError) {
      setActionError(
        transitionError instanceof Error ? transitionError.message : "Unable to change follow-up status",
      );
    } finally {
      setBusyId(null);
    }
  }

  if (!canManage) {
    return null;
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-medium text-slate-900">Follow-up reminders</h3>
          <p className="text-sm text-slate-500">Operational queue for due today, overdue, and upcoming reminders.</p>
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

      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <SummaryPanel
          title="Due today"
          icon={CalendarDays}
          accentClassName="bg-sky-50 text-sky-700"
          items={dueTodayItems}
          emptyMessage="No reminders due today."
          busyId={busyId}
          onComplete={(item) => void handleTransition(item, "complete")}
          onCancel={(item) => void handleTransition(item, "cancel")}
        />
        <SummaryPanel
          title="Overdue"
          icon={AlertTriangle}
          accentClassName="bg-rose-50 text-rose-700"
          items={overdueItems}
          emptyMessage="No overdue reminders."
          busyId={busyId}
          onComplete={(item) => void handleTransition(item, "complete")}
          onCancel={(item) => void handleTransition(item, "cancel")}
        />
        <SummaryPanel
          title="Upcoming"
          icon={Clock3}
          accentClassName="bg-amber-50 text-amber-700"
          items={upcomingItems}
          emptyMessage="No upcoming reminders."
          busyId={busyId}
          onComplete={(item) => void handleTransition(item, "complete")}
          onCancel={(item) => void handleTransition(item, "cancel")}
        />
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-[220px_220px_280px_auto] md:items-end">
        <label className="space-y-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Window</span>
          <select
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition duration-200 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            value={windowFilter}
            onChange={(event) => setWindowFilter(event.target.value as FollowUpWindowFilter)}
          >
            {WINDOW_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Status</span>
          <select
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition duration-200 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as "all" | FollowUpStatus)}
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Sort</span>
          <select
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition duration-200 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value as FollowUpSort)}
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <button
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition duration-200 hover:bg-slate-50"
          type="button"
          onClick={() => {
            setWindowFilter("all");
            setStatusFilter("all");
            setSortBy("due_asc");
          }}
        >
          Reset filters
        </button>
      </div>

      {loading ? <p className="mt-4 text-sm text-slate-500">Loading follow-up reminders...</p> : null}
      {error ? (
        <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <p>{error}</p>
        </div>
      ) : null}
      {actionError ? (
        <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <p>{actionError}</p>
        </div>
      ) : null}

      {!loading && !error && filteredItems.length === 0 ? (
        <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">
          No reminders found for the selected filters.
        </div>
      ) : null}

      {!loading && !error && filteredItems.length > 0 ? (
        <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-[920px] w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Due date</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">Reason</th>
                <th className="px-4 py-3 text-left font-medium">Patient</th>
                <th className="px-4 py-3 text-left font-medium">Created</th>
                <th className="px-4 py-3 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white text-slate-700">
              {filteredItems.map((item) => {
                const canTransition = item.status === "pending" || item.status === "overdue";
                return (
                  <tr key={item.id}>
                    <td className="px-4 py-3">{formatDate(item.due_date)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge label={formatFollowUpStatus(item.status)} tone={item.status} />
                    </td>
                    <td className="px-4 py-3">{item.reason}</td>
                    <td className="px-4 py-3 text-xs text-slate-500">{item.patient_id}</td>
                    <td className="px-4 py-3">{new Date(item.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3">
                      {canTransition ? (
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            className="inline-flex items-center gap-1 rounded-lg border border-emerald-200 bg-white px-3 py-1.5 text-xs font-medium text-emerald-700 transition duration-200 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-60"
                            type="button"
                            onClick={() => void handleTransition(item, "complete")}
                            disabled={busyId === item.id}
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Complete
                          </button>
                          <button
                            className="inline-flex items-center rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-700 transition duration-200 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60"
                            type="button"
                            onClick={() => void handleTransition(item, "cancel")}
                            disabled={busyId === item.id}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">No actions</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

interface SummaryPanelProps {
  title: string;
  icon: typeof CalendarDays;
  accentClassName: string;
  items: FollowUp[];
  emptyMessage: string;
  busyId: string | null;
  onComplete: (item: FollowUp) => void;
  onCancel: (item: FollowUp) => void;
}

function SummaryPanel({
  title,
  icon: Icon,
  accentClassName,
  items,
  emptyMessage,
  busyId,
  onComplete,
  onCancel,
}: SummaryPanelProps) {
  return (
    <article className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
          <p className="text-2xl font-semibold tracking-tight text-slate-900">{items.length}</p>
        </div>
        <span className={`inline-flex h-9 w-9 items-center justify-center rounded-lg ${accentClassName}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>

      <div className="mt-3 space-y-2">
        {items.slice(0, 3).map((item) => {
          const canTransition = item.status === "pending" || item.status === "overdue";
          return (
            <div className="rounded-lg border border-slate-200 bg-white p-2.5" key={item.id}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-semibold text-slate-700">{formatDate(item.due_date)}</p>
                <StatusBadge label={formatFollowUpStatus(item.status)} tone={item.status} />
              </div>
              <p className="mt-1 text-xs text-slate-600">{item.reason}</p>
              {canTransition ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    className="inline-flex items-center gap-1 rounded-lg border border-emerald-200 bg-white px-2.5 py-1 text-[11px] font-medium text-emerald-700 transition duration-200 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-60"
                    type="button"
                    onClick={() => onComplete(item)}
                    disabled={busyId === item.id}
                  >
                    Complete
                  </button>
                  <button
                    className="inline-flex items-center rounded-lg border border-rose-200 bg-white px-2.5 py-1 text-[11px] font-medium text-rose-700 transition duration-200 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60"
                    type="button"
                    onClick={() => onCancel(item)}
                    disabled={busyId === item.id}
                  >
                    Cancel
                  </button>
                </div>
              ) : null}
            </div>
          );
        })}
        {items.length === 0 ? <p className="text-xs text-slate-500">{emptyMessage}</p> : null}
      </div>
    </article>
  );
}

function sortItems(items: FollowUp[], sortBy: FollowUpSort): FollowUp[] {
  const next = [...items];
  next.sort((left, right) => {
    if (sortBy === "due_asc") {
      return left.due_date.localeCompare(right.due_date);
    }
    if (sortBy === "due_desc") {
      return right.due_date.localeCompare(left.due_date);
    }
    if (sortBy === "created_asc") {
      return new Date(left.created_at).getTime() - new Date(right.created_at).getTime();
    }
    return new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
  });
  return next;
}

function toDateOnly(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDate(value: string): string {
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function formatFollowUpStatus(status: FollowUpStatus): string {
  return status.replace("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
