import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  cancelFollowUp,
  completeFollowUp,
  listPatientFollowUps,
  type DemoRole,
  type FollowUp,
  type FollowUpStatus,
} from "../../app/api";
import { StatusBadge } from "../ui/StatusBadge";

interface PatientFollowUpsSectionProps {
  role: DemoRole;
  patientId: string;
}

type FollowUpStatusFilter = "all" | FollowUpStatus;
type FollowUpWindowFilter = "all" | "due_today" | "overdue" | "upcoming";
type FollowUpSort = "due_asc" | "due_desc" | "created_desc" | "created_asc";

export function PatientFollowUpsSection({ role, patientId }: PatientFollowUpsSectionProps) {
  const [statusFilter, setStatusFilter] = useState<FollowUpStatusFilter>("all");
  const [dueBeforeFilter, setDueBeforeFilter] = useState("");
  const [windowFilter, setWindowFilter] = useState<FollowUpWindowFilter>("all");
  const [sortBy, setSortBy] = useState<FollowUpSort>("due_asc");
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyFollowUpId, setBusyFollowUpId] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const canManage = role === "doctor" || role === "admin";
  const todayIso = toDateOnly(new Date());

  useEffect(() => {
    if (!canManage) {
      setFollowUps([]);
      setError(null);
      setIsLoading(false);
      return;
    }

    let active = true;
    async function loadFollowUps() {
      setIsLoading(true);
      setActionError(null);
      try {
        const response = await listPatientFollowUps(role, patientId, {
          status: statusFilter === "all" ? undefined : statusFilter,
          dueBefore: dueBeforeFilter || undefined,
          limit: 100,
          offset: 0,
        });
        if (!active) {
          return;
        }
        setFollowUps(response.items);
        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setFollowUps([]);
        setError(loadError instanceof Error ? loadError.message : "Unable to load follow-up reminders");
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadFollowUps();
    return () => {
      active = false;
    };
  }, [canManage, dueBeforeFilter, patientId, reloadToken, role, statusFilter]);

  const filteredFollowUps = useMemo(() => {
    let next = [...followUps];

    if (windowFilter === "due_today") {
      next = next.filter((item) => item.status === "pending" && item.due_date === todayIso);
    }
    if (windowFilter === "overdue") {
      next = next.filter((item) => item.status === "overdue");
    }
    if (windowFilter === "upcoming") {
      next = next.filter((item) => item.status === "pending" && item.due_date > todayIso);
    }

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
  }, [followUps, sortBy, todayIso, windowFilter]);

  async function handleAction(followUpId: string, action: "complete" | "cancel") {
    if (!canManage) {
      return;
    }

    setActionError(null);
    setBusyFollowUpId(followUpId);
    try {
      if (action === "complete") {
        await completeFollowUp(role, followUpId);
      } else {
        await cancelFollowUp(role, followUpId);
      }
      setReloadToken((current) => current + 1);
    } catch (actionFailure) {
      setActionError(actionFailure instanceof Error ? actionFailure.message : "Unable to update follow-up status");
    } finally {
      setBusyFollowUpId(null);
    }
  }

  if (!canManage) {
    return (
      <section className="panel">
        <div>
          <p className="eyebrow">Follow-up reminders</p>
          <h3 className="text-2xl font-semibold tracking-tight text-slate-900">Reminder history</h3>
          <p className="mt-1 text-sm text-slate-500">
            Follow-up reminders are visible to clinical roles only in this phase.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">Follow-up reminders</p>
          <h3 className="text-2xl font-semibold tracking-tight text-slate-900">Reminder history</h3>
          <p className="mt-1 text-sm text-slate-500">Track pending, overdue, completed, and cancelled reminders.</p>
        </div>
        {role === "doctor" ? (
          <Link className="secondary-button link-button" to={`/visits/new?patient_id=${patientId}`}>
            Start visit
          </Link>
        ) : null}
      </div>

      <div className="grid gap-3 md:grid-cols-[180px_180px_220px_260px_auto] md:items-end">
        <label className="field-stack">
          <span className="field-label">Status</span>
          <select
            className="text-input"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value as FollowUpStatusFilter)}
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="overdue">Overdue</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </label>
        <label className="field-stack">
          <span className="field-label">Window</span>
          <select
            className="text-input"
            value={windowFilter}
            onChange={(event) => setWindowFilter(event.target.value as FollowUpWindowFilter)}
          >
            <option value="all">All windows</option>
            <option value="due_today">Due today</option>
            <option value="overdue">Overdue</option>
            <option value="upcoming">Upcoming</option>
          </select>
        </label>
        <label className="field-stack">
          <span className="field-label">Due on or before</span>
          <input
            className="text-input"
            type="date"
            value={dueBeforeFilter}
            onChange={(event) => setDueBeforeFilter(event.target.value)}
          />
        </label>
        <label className="field-stack">
          <span className="field-label">Sort</span>
          <select
            className="text-input"
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value as FollowUpSort)}
          >
            <option value="due_asc">Due date (oldest first)</option>
            <option value="due_desc">Due date (newest first)</option>
            <option value="created_desc">Created (newest first)</option>
            <option value="created_asc">Created (oldest first)</option>
          </select>
        </label>
        <button
          className="secondary-button"
          type="button"
          onClick={() => {
            setStatusFilter("all");
            setWindowFilter("all");
            setDueBeforeFilter("");
            setSortBy("due_asc");
          }}
        >
          Clear filters
        </button>
      </div>

      {isLoading ? <p className="muted-note">Loading follow-up reminders...</p> : null}
      {error ? <p className="status-error">{error}</p> : null}
      {actionError ? <p className="status-error">{actionError}</p> : null}

      {!isLoading && !error && filteredFollowUps.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
          No follow-up reminders found for the selected filters.
        </div>
      ) : null}

      {filteredFollowUps.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Due date</th>
                <th>Status</th>
                <th>Reason</th>
                <th>Notes</th>
                <th>Visit</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredFollowUps.map((followUp) => {
                const canTransition = followUp.status === "pending" || followUp.status === "overdue";
                const isBusy = busyFollowUpId === followUp.id;
                return (
                  <tr key={followUp.id}>
                    <td>{new Date(`${followUp.due_date}T00:00:00`).toLocaleDateString()}</td>
                    <td>
                      <StatusBadge label={formatFollowUpStatus(followUp.status)} tone={followUp.status} />
                    </td>
                    <td>{followUp.reason}</td>
                    <td>{followUp.notes ?? "—"}</td>
                    <td>
                      <Link className="table-link" to={`/visits/${followUp.visit_id}`}>
                        Open visit
                      </Link>
                    </td>
                    <td>{new Date(followUp.created_at).toLocaleString()}</td>
                    <td>
                      {canTransition ? (
                        <div className="table-actions">
                          <button
                            className="table-button"
                            type="button"
                            onClick={() => void handleAction(followUp.id, "complete")}
                            disabled={isBusy}
                          >
                            Complete
                          </button>
                          <button
                            className="table-button"
                            type="button"
                            onClick={() => void handleAction(followUp.id, "cancel")}
                            disabled={isBusy}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <span className="muted-note">No actions</span>
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

function formatFollowUpStatus(status: FollowUpStatus): string {
  return status.replace("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function toDateOnly(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
