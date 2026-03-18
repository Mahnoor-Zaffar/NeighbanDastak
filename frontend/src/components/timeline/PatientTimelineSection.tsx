import { useMemo, useState } from "react";
import { Activity, CalendarCheck2, CalendarClock, CalendarX2, ClipboardCheck, FileText, UserRoundPlus } from "lucide-react";
import { Link } from "react-router-dom";

import type { PatientTimelineEvent } from "../../app/api";

interface PatientTimelineSectionProps {
  loading: boolean;
  error: string | null;
  events: PatientTimelineEvent[];
}

interface EventDisplayConfig {
  label: string;
  icon: typeof Activity;
  toneClassName: string;
}

type TimelineFilterValue = "all" | "appointments" | "visits" | "prescriptions";

const EVENT_DISPLAY_MAP: Record<string, EventDisplayConfig> = {
  patient_created: {
    label: "Patient",
    icon: UserRoundPlus,
    toneClassName: "timeline-badge-patient",
  },
  appointment_scheduled: {
    label: "Appointment",
    icon: CalendarClock,
    toneClassName: "timeline-badge-appointment",
  },
  appointment_completed: {
    label: "Appointment",
    icon: CalendarCheck2,
    toneClassName: "timeline-badge-appointment",
  },
  appointment_cancelled: {
    label: "Appointment",
    icon: CalendarX2,
    toneClassName: "timeline-badge-appointment",
  },
  appointment_no_show: {
    label: "Appointment",
    icon: CalendarX2,
    toneClassName: "timeline-badge-appointment",
  },
  visit_created: {
    label: "Visit",
    icon: ClipboardCheck,
    toneClassName: "timeline-badge-visit",
  },
  prescription_created: {
    label: "Prescription",
    icon: FileText,
    toneClassName: "timeline-badge-prescription",
  },
};

export function PatientTimelineSection({ loading, error, events }: PatientTimelineSectionProps) {
  const [typeFilter, setTypeFilter] = useState<TimelineFilterValue>("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const orderedEvents = useMemo(
    () =>
      [...events].sort(
        (first, second) => new Date(second.event_timestamp).getTime() - new Date(first.event_timestamp).getTime(),
      ),
    [events],
  );
  const filteredEvents = useMemo(
    () =>
      orderedEvents.filter((event) => {
        if (!matchesTypeFilter(event.event_type, typeFilter)) {
          return false;
        }
        return matchesDateRange(event.event_timestamp, dateFrom, dateTo);
      }),
    [dateFrom, dateTo, orderedEvents, typeFilter],
  );

  return (
    <section className="panel timeline-panel">
      <div>
        <p className="eyebrow">Medical timeline</p>
        <h3 className="timeline-title">Chronological clinical history</h3>
        <p className="timeline-subtitle">Newest events first for faster clinical review.</p>
      </div>

      {!loading && !error && events.length > 0 ? (
        <div className="timeline-filter-row">
          <label className="field-stack timeline-filter-item" htmlFor="timeline-type-filter">
            <span className="field-label">Event type</span>
            <select
              id="timeline-type-filter"
              className="text-input timeline-filter-control"
              value={typeFilter}
              onChange={(event) => {
                setTypeFilter(event.target.value as TimelineFilterValue);
              }}
            >
              <option value="all">All events</option>
              <option value="appointments">Appointments</option>
              <option value="visits">Visits</option>
              <option value="prescriptions">Prescriptions</option>
            </select>
          </label>
          <label className="field-stack timeline-filter-item" htmlFor="timeline-date-from">
            <span className="field-label">From date</span>
            <input
              id="timeline-date-from"
              className="text-input timeline-filter-control"
              type="date"
              value={dateFrom}
              onChange={(event) => {
                setDateFrom(event.target.value);
              }}
            />
          </label>
          <label className="field-stack timeline-filter-item" htmlFor="timeline-date-to">
            <span className="field-label">To date</span>
            <input
              id="timeline-date-to"
              className="text-input timeline-filter-control"
              type="date"
              value={dateTo}
              onChange={(event) => {
                setDateTo(event.target.value);
              }}
            />
          </label>
          <button
            className="secondary-button timeline-clear-button"
            type="button"
            onClick={() => {
              setTypeFilter("all");
              setDateFrom("");
              setDateTo("");
            }}
            disabled={typeFilter === "all" && !dateFrom && !dateTo}
          >
            Clear filters
          </button>
        </div>
      ) : null}

      {loading ? <p className="muted-note">Loading patient timeline...</p> : null}
      {error ? <p className="status-error">{error}</p> : null}

      {!loading && !error && events.length === 0 ? (
        <div className="timeline-empty-state">
          <p>No clinical events recorded yet for this patient.</p>
        </div>
      ) : null}

      {!loading && !error && events.length > 0 && filteredEvents.length === 0 ? (
        <div className="timeline-empty-state">
          <p>No timeline events match the selected filters.</p>
        </div>
      ) : null}

      {!loading && !error && filteredEvents.length > 0 ? (
        <ol className="timeline-list">
          {filteredEvents.map((event) => {
            const display = EVENT_DISPLAY_MAP[event.event_type] ?? {
              label: "Event",
              icon: Activity,
              toneClassName: "timeline-badge-default",
            };
            const Icon = display.icon;
            const linkPath = getEntityLinkPath(event.related_entity_type, event.related_entity_id);

            const eventBody = (
              <article className="timeline-card">
                <div className="timeline-card-header">
                  <span className={`timeline-type-badge ${display.toneClassName}`}>{display.label}</span>
                  <time className="timeline-time">{formatTimestamp(event.event_timestamp)}</time>
                </div>
                <h4 className="timeline-event-title">{event.title}</h4>
                {event.subtitle ? <p className="timeline-event-subtitle">{event.subtitle}</p> : null}
                <div className="timeline-meta-row">
                  {event.actor_name ? <span>Actor: {event.actor_name}</span> : <span>Actor: System</span>}
                  <span>Reference: {shortEntityLabel(event.related_entity_type, event.related_entity_id)}</span>
                  {linkPath ? <span className="timeline-open-indicator">Open details</span> : null}
                </div>
              </article>
            );

            return (
              <li className="timeline-item" key={event.id}>
                <div className={`timeline-icon ${display.toneClassName}`}>
                  <Icon aria-hidden className="timeline-icon-svg" />
                </div>
                {linkPath ? (
                  <Link className="timeline-card-link" to={linkPath}>
                    {eventBody}
                  </Link>
                ) : (
                  eventBody
                )}
              </li>
            );
          })}
        </ol>
      ) : null}
    </section>
  );
}

function formatTimestamp(value: string): string {
  const timestamp = new Date(value);
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(timestamp);
}

function shortEntityLabel(entityType: string, entityId: string): string {
  const shortId = entityId.length > 8 ? entityId.slice(0, 8) : entityId;
  return `${entityType} #${shortId}`;
}

function getEntityLinkPath(entityType: string, entityId: string): string | null {
  if (entityType === "visit") {
    return `/visits/${entityId}`;
  }
  if (entityType === "prescription") {
    return `/prescriptions/${entityId}`;
  }
  return null;
}

function matchesTypeFilter(eventType: string, filter: TimelineFilterValue): boolean {
  if (filter === "all") {
    return true;
  }
  if (filter === "appointments") {
    return eventType.startsWith("appointment_");
  }
  if (filter === "visits") {
    return eventType.startsWith("visit_");
  }
  return eventType.startsWith("prescription_");
}

function matchesDateRange(eventTimestamp: string, dateFrom: string, dateTo: string): boolean {
  const eventDate = new Date(eventTimestamp);
  if (Number.isNaN(eventDate.getTime())) {
    return false;
  }

  if (dateFrom) {
    const fromDate = new Date(`${dateFrom}T00:00:00`);
    if (eventDate < fromDate) {
      return false;
    }
  }

  if (dateTo) {
    const toDate = new Date(`${dateTo}T23:59:59.999`);
    if (eventDate > toDate) {
      return false;
    }
  }

  return true;
}
