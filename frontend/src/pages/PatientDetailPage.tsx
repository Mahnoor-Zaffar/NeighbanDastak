import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";

import { getPatient, getPatientTimeline, listPatientPrescriptions, type Patient, type PatientTimelineEvent, type Prescription } from "../app/api";
import type { AppLayoutContext } from "../components/AppLayout";
import { PatientFollowUpsSection } from "../components/followUps/PatientFollowUpsSection";
import { PatientPrescriptionsSection } from "../components/prescriptions/PatientPrescriptionsSection";
import { PatientTimelineSection } from "../components/timeline/PatientTimelineSection";

export function PatientDetailPage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const { patientId } = useParams<{ patientId: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<PatientTimelineEvent[]>([]);
  const [isLoadingPrescriptions, setIsLoadingPrescriptions] = useState(false);
  const [isLoadingTimeline, setIsLoadingTimeline] = useState(false);
  const [prescriptionError, setPrescriptionError] = useState<string | null>(null);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const resolvedPatientId = patientId ?? "";
    if (!resolvedPatientId) {
      setPatient(null);
      setPrescriptions([]);
      setTimelineEvents([]);
      setIsLoadingPrescriptions(false);
      setIsLoadingTimeline(false);
      setPrescriptionError(null);
      setTimelineError(null);
      setIsLoading(false);
      setError("Missing patient identifier.");
      return;
    }

    let active = true;

    async function loadPatient() {
      setIsLoading(true);
      try {
        const response = await getPatient(role, resolvedPatientId);
        if (!active) {
          return;
        }

        setPatient(response);
        setIsLoadingPrescriptions(true);
        setIsLoadingTimeline(true);
        const [prescriptionResult, timelineResult] = await Promise.allSettled([
          listPatientPrescriptions(role, resolvedPatientId),
          getPatientTimeline(role, resolvedPatientId),
        ]);

        if (!active) {
          return;
        }

        if (prescriptionResult.status === "fulfilled") {
          setPrescriptions(prescriptionResult.value.items);
          setPrescriptionError(null);
        } else {
          setPrescriptions([]);
          setPrescriptionError(
            prescriptionResult.reason instanceof Error
              ? prescriptionResult.reason.message
              : "Unable to load patient prescriptions",
          );
        }

        if (timelineResult.status === "fulfilled") {
          setTimelineEvents(timelineResult.value.items);
          setTimelineError(null);
        } else {
          setTimelineEvents([]);
          setTimelineError(
            timelineResult.reason instanceof Error
              ? timelineResult.reason.message
              : "Unable to load patient timeline",
          );
        }

        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setPatient(null);
        setPrescriptions([]);
        setTimelineEvents([]);
        setPrescriptionError(null);
        setTimelineError(null);
        setError(loadError instanceof Error ? loadError.message : "Unable to load patient");
      } finally {
        if (active) {
          setIsLoading(false);
          setIsLoadingPrescriptions(false);
          setIsLoadingTimeline(false);
        }
      }
    }

    void loadPatient();

    return () => {
      active = false;
    };
  }, [patientId, role]);

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">Patient detail</p>
          <h2 className="section-title">{patient ? `${patient.first_name} ${patient.last_name}` : "Patient record"}</h2>
        </div>
        <div className="action-row">
          <Link className="secondary-button link-button" to="/patients">
            Back to list
          </Link>
          {patient && role === "admin" ? (
            <Link className="primary-button link-button" to={`/patients/${patient.id}/edit`}>
              Edit patient
            </Link>
          ) : null}
        </div>
      </section>

      {isLoading ? (
        <section className="panel">
          <p>Loading patient...</p>
        </section>
      ) : null}
      {error ? <p className="status-error">{error}</p> : null}
      {patient ? (
        <>
          <section className="panel detail-grid">
            <DetailItem label="Record number" value={patient.record_number} />
            <DetailItem label="Date of birth" value={patient.date_of_birth} />
            <DetailItem label="Email" value={patient.email ?? "—"} />
            <DetailItem label="Phone" value={patient.phone ?? "—"} />
            <DetailItem label="City" value={patient.city ?? "—"} />
            <DetailItem label="Status" value={patient.archived_at ? "Archived" : "Active"} />
            <DetailItem label="Notes" value={patient.notes ?? "—"} />
          </section>
          <PatientTimelineSection loading={isLoadingTimeline} error={timelineError} events={timelineEvents} />
          <PatientFollowUpsSection role={role} patientId={patient.id} />
          <PatientPrescriptionsSection
            role={role}
            patientId={patient.id}
            loading={isLoadingPrescriptions}
            error={prescriptionError}
            prescriptions={prescriptions}
          />
        </>
      ) : null}
      {!isLoading && !error && !patient ? (
        <section className="panel empty-state">
          <p>Patient not found.</p>
          <Link className="secondary-button link-button" to="/patients">
            Back to patient list
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
