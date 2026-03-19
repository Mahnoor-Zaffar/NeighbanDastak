import { useMemo, useState, useEffect } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";

import {
  createFollowUp,
  getPatient,
  getVisit,
  listVisitPrescriptions,
  type Patient,
  type Prescription,
  type Visit,
} from "../app/api";
import { getStoredDoctorDisplayName, getStoredDoctorProfileId } from "../app/doctorIdentity";
import type { AppLayoutContext } from "../components/AppLayout";
import { FollowUpForm, type FollowUpFormValues } from "../components/followUps/FollowUpForm";

export function VisitDetailPage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const { visitId } = useParams<{ visitId: string }>();
  const [visit, setVisit] = useState<Visit | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [isLoadingPrescriptions, setIsLoadingPrescriptions] = useState(false);
  const [prescriptionsError, setPrescriptionsError] = useState<string | null>(null);
  const [showFollowUpForm, setShowFollowUpForm] = useState(false);
  const [isSubmittingFollowUp, setIsSubmittingFollowUp] = useState(false);
  const [followUpSubmitError, setFollowUpSubmitError] = useState<string | null>(null);
  const [followUpSuccessMessage, setFollowUpSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const canCreatePrescription = role === "doctor";
  const canCreateFollowUp = role === "doctor";
  const doctorProfileId = getStoredDoctorProfileId().trim();
  const doctorDisplayName = getStoredDoctorDisplayName().trim();
  const followUpInitialValues = useMemo(
    () => ({
      due_date: new Date().toISOString().slice(0, 10),
    }),
    [],
  );

  useEffect(() => {
    const resolvedVisitId = visitId ?? "";
    if (!resolvedVisitId) {
      setVisit(null);
      setPatient(null);
      setPrescriptions([]);
      setIsLoadingPrescriptions(false);
      setPrescriptionsError(null);
      setIsLoading(false);
      setError("Missing visit identifier.");
      return;
    }

    let active = true;
    async function loadVisit() {
      setIsLoading(true);
      setIsLoadingPrescriptions(true);
      try {
        const visitResponse = await getVisit(role, resolvedVisitId);
        if (!active) {
          return;
        }

        setVisit(visitResponse);
        try {
          const [patientResponse, prescriptionResponse] = await Promise.all([
            getPatient(role, visitResponse.patient_id).catch(() => null),
            listVisitPrescriptions(role, visitResponse.id).catch(() => null),
          ]);
          if (!active) {
            return;
          }
          setPatient(patientResponse);
          if (prescriptionResponse) {
            setPrescriptions(prescriptionResponse.items);
            setPrescriptionsError(null);
          } else {
            setPrescriptions([]);
            setPrescriptionsError("Unable to load prescriptions for this visit.");
          }
        } catch {
          setPatient(null);
          setPrescriptions([]);
          setPrescriptionsError("Unable to load prescriptions for this visit.");
        } finally {
          setIsLoadingPrescriptions(false);
        }
        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setVisit(null);
        setPatient(null);
        setPrescriptions([]);
        setIsLoadingPrescriptions(false);
        setPrescriptionsError(null);
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

  async function handleCreateFollowUp(values: FollowUpFormValues) {
    if (!visit) {
      setFollowUpSubmitError("Visit context is missing.");
      return;
    }

    setIsSubmittingFollowUp(true);
    setFollowUpSubmitError(null);
    setFollowUpSuccessMessage(null);
    try {
      if (!doctorProfileId) {
        setFollowUpSubmitError("Doctor profile is not linked to this session. Switch demo user and try again.");
        return;
      }

      await createFollowUp(
        role,
        {
          patient_id: visit.patient_id,
          visit_id: visit.id,
          doctor_id: doctorProfileId,
          due_date: values.due_date,
          reason: values.reason,
          notes: values.notes,
        },
        doctorProfileId,
      );
      setShowFollowUpForm(false);
      setFollowUpSuccessMessage(`Follow-up created for ${new Date(`${values.due_date}T00:00:00`).toLocaleDateString()}.`);
    } catch (submitError) {
      setFollowUpSubmitError(submitError instanceof Error ? submitError.message : "Unable to create follow-up");
    } finally {
      setIsSubmittingFollowUp(false);
    }
  }

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
          {canCreatePrescription && visit ? (
            <Link
              className="secondary-button link-button"
              to={`/prescriptions/new?patient_id=${visit.patient_id}&visit_id=${visit.id}`}
            >
              Create prescription
            </Link>
          ) : null}
          {canCreateFollowUp ? (
            <button className="secondary-button" type="button" onClick={() => setShowFollowUpForm((current) => !current)}>
              {showFollowUpForm ? "Hide follow-up form" : "Create follow-up"}
            </button>
          ) : null}
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
        <>
          <section className="panel detail-grid">
            <DetailItem label="Patient" value={patient ? `${patient.first_name} ${patient.last_name}` : visit.patient_id} />
            <DetailItem label="Linked appointment" value={visit.appointment_id ?? "—"} />
            <DetailItem label="Started at" value={new Date(visit.started_at).toLocaleString()} />
            <DetailItem label="Ended at" value={visit.ended_at ? new Date(visit.ended_at).toLocaleString() : "—"} />
            <DetailItem label="Complaint" value={visit.complaint ?? "—"} />
            <DetailItem label="Diagnosis summary" value={visit.diagnosis_summary ?? "—"} />
            <DetailItem label="Notes" value={visit.notes ?? "—"} />
          </section>

          <section className="panel">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="eyebrow">Visit prescriptions</p>
                <h3 className="text-2xl font-semibold tracking-tight text-slate-900">Medication orders for this encounter</h3>
              </div>
              {canCreatePrescription ? (
                <Link
                  className="primary-button link-button"
                  to={`/prescriptions/new?patient_id=${visit.patient_id}&visit_id=${visit.id}`}
                >
                  Add prescription
                </Link>
              ) : null}
            </div>
            {isLoadingPrescriptions ? <p className="muted-note">Loading visit prescriptions...</p> : null}
            {prescriptionsError ? <p className="status-error">{prescriptionsError}</p> : null}
            {!isLoadingPrescriptions && !prescriptionsError && prescriptions.length === 0 ? (
              <p className="muted-note">No prescriptions recorded for this visit yet.</p>
            ) : null}
            {prescriptions.length > 0 ? (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Diagnosis</th>
                      <th>Medicines</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {prescriptions.map((prescription) => (
                      <tr key={prescription.id}>
                        <td>{new Date(prescription.created_at).toLocaleString()}</td>
                        <td>{prescription.diagnosis_summary}</td>
                        <td>{prescription.items.length}</td>
                        <td>
                          <Link className="table-link" to={`/prescriptions/${prescription.id}`}>
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>

          {canCreateFollowUp && visit ? (
            <>
              {followUpSuccessMessage ? <p className="muted-note">{followUpSuccessMessage}</p> : null}
              {showFollowUpForm ? (
                <FollowUpForm
                  role={role}
                  patientId={visit.patient_id}
                  visitId={visit.id}
                  doctorProfileId={doctorProfileId}
                  doctorDisplayName={doctorDisplayName}
                  initialValues={followUpInitialValues}
                  isSubmitting={isSubmittingFollowUp}
                  submitError={followUpSubmitError}
                  onSubmit={handleCreateFollowUp}
                  onCancel={() => setShowFollowUpForm(false)}
                />
              ) : (
                <section className="panel">
                  <p className="eyebrow">Follow-up reminders</p>
                  <h3 className="text-2xl font-semibold tracking-tight text-slate-900">Set next clinical reminder</h3>
                  <p className="muted-note">
                    Create follow-ups directly from this visit to track due care and overdue callbacks.
                  </p>
                </section>
              )}
            </>
          ) : null}
        </>
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
