import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";

import { getPatient, getVisit, type Patient, type Visit } from "../app/api";
import type { AppLayoutContext } from "../components/AppLayout";

export function VisitDetailPage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const { visitId } = useParams<{ visitId: string }>();
  const [visit, setVisit] = useState<Visit | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const resolvedVisitId = visitId;
    if (!resolvedVisitId) {
      setVisit(null);
      setPatient(null);
      setIsLoading(false);
      setError("Missing visit identifier.");
      return;
    }

    let active = true;
    async function loadVisit() {
      setIsLoading(true);
      try {
        const visitResponse = await getVisit(role, resolvedVisitId);
        if (!active) {
          return;
        }

        setVisit(visitResponse);
        try {
          const patientResponse = await getPatient(role, visitResponse.patient_id);
          if (!active) {
            return;
          }
          setPatient(patientResponse);
        } catch {
          if (!active) {
            return;
          }
          setPatient(null);
        }
        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setVisit(null);
        setPatient(null);
        setError(loadError instanceof Error ? loadError.message : "Unable to load visit detail");
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadVisit();
    return () => {
      active = false;
    };
  }, [role, visitId]);

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">Visit detail</p>
          <h2 className="section-title">Encounter record</h2>
        </div>
        <div className="action-row">
          <Link className="secondary-button link-button" to="/appointments">
            Appointments
          </Link>
          <Link className="primary-button link-button" to="/visits/new">
            New visit
          </Link>
        </div>
      </section>

      {isLoading ? (
        <section className="panel">
          <p>Loading visit...</p>
        </section>
      ) : null}
      {error ? <p className="status-error">{error}</p> : null}
      {visit ? (
        <section className="panel detail-grid">
          <DetailItem label="Patient" value={patient ? `${patient.first_name} ${patient.last_name}` : visit.patient_id} />
          <DetailItem label="Linked appointment" value={visit.appointment_id ?? "—"} />
          <DetailItem label="Started at" value={new Date(visit.started_at).toLocaleString()} />
          <DetailItem label="Ended at" value={visit.ended_at ? new Date(visit.ended_at).toLocaleString() : "—"} />
          <DetailItem label="Complaint" value={visit.complaint ?? "—"} />
          <DetailItem label="Diagnosis summary" value={visit.diagnosis_summary ?? "—"} />
          <DetailItem label="Notes" value={visit.notes ?? "—"} />
        </section>
      ) : null}
      {!isLoading && !error && !visit ? (
        <section className="panel empty-state">
          <p>Visit not found.</p>
          <Link className="secondary-button link-button" to="/appointments">
            Back to appointments
          </Link>
        </section>
      ) : null}
    </div>
  );
}

interface DetailItemProps {
  label: string;
  value: string;
}

function DetailItem({ label, value }: DetailItemProps) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
