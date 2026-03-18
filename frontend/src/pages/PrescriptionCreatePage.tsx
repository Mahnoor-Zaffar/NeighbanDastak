import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useOutletContext, useSearchParams } from "react-router-dom";

import { createPrescription, getPatient, getVisit, type Patient, type Visit } from "../app/api";
import { getStoredDoctorDisplayName, getStoredDoctorProfileId, rememberDoctorProfile } from "../app/doctorIdentity";
import type { AppLayoutContext } from "../components/AppLayout";
import { PrescriptionForm, type PrescriptionFormValues } from "../components/prescriptions/PrescriptionForm";

export function PrescriptionCreatePage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const patientId = searchParams.get("patient_id") ?? "";
  const visitId = searchParams.get("visit_id") ?? "";
  const [patient, setPatient] = useState<Patient | null>(null);
  const [visit, setVisit] = useState<Visit | null>(null);
  const [isLoadingContext, setIsLoadingContext] = useState(true);
  const [contextError, setContextError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canWrite = role === "doctor";
  const initialDoctorProfile = useMemo(
    () => ({ doctor_id: getStoredDoctorProfileId(), doctor_name: getStoredDoctorDisplayName() }),
    [],
  );

  useEffect(() => {
    if (!patientId || !visitId) {
      setIsLoadingContext(false);
      setContextError("Missing patient or visit context. Start prescription flow from a visit detail page.");
      return;
    }

    let active = true;
    async function loadContext() {
      setIsLoadingContext(true);
      try {
        const [visitResponse, patientResponse] = await Promise.all([getVisit(role, visitId), getPatient(role, patientId)]);
        if (!active) {
          return;
        }
        setVisit(visitResponse);
        setPatient(patientResponse);
        setContextError(null);
      } catch (error) {
        if (!active) {
          return;
        }
        setVisit(null);
        setPatient(null);
        setContextError(error instanceof Error ? error.message : "Unable to load prescription context");
      } finally {
        if (active) {
          setIsLoadingContext(false);
        }
      }
    }

    void loadContext();
    return () => {
      active = false;
    };
  }, [patientId, role, visitId]);

  async function handleSubmit(values: PrescriptionFormValues) {
    if (!canWrite) {
      setSubmitError("You do not have permission to create prescriptions.");
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const created = await createPrescription(role, {
        patient_id: patientId,
        visit_id: visitId,
        doctor_id: values.doctor_id,
        diagnosis_summary: values.diagnosis_summary,
        notes: values.notes,
        items: values.items,
      });
      rememberDoctorProfile(values.doctor_id, values.doctor_name);
      navigate(`/prescriptions/${created.id}`, { replace: true });
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Unable to create prescription");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">Prescription workflow</p>
          <h2 className="section-title">Create clinical prescription</h2>
          {patient ? <p className="lede">Patient: {patient.first_name} {patient.last_name}</p> : null}
        </div>
        <div className="action-row">
          <Link className="secondary-button link-button" to={visitId ? `/visits/${visitId}` : "/appointments"}>
            Back to visit
          </Link>
        </div>
      </section>

      {isLoadingContext ? (
        <section className="panel">
          <p>Loading prescription context...</p>
        </section>
      ) : null}

      {!isLoadingContext && contextError ? (
        <section className="panel empty-state">
          <p className="status-error">{contextError}</p>
          <Link className="secondary-button link-button" to="/appointments">
            Go to appointments
          </Link>
        </section>
      ) : null}

      {!isLoadingContext && !contextError && patient && visit && role === "doctor" ? (
        <PrescriptionForm
          mode="create"
          role={role}
          patientId={patient.id}
          visitId={visit.id}
          initialValues={initialDoctorProfile}
          isSubmitting={isSubmitting}
          submitError={submitError}
          onDoctorProfileChange={rememberDoctorProfile}
          onSubmit={handleSubmit}
          onCancel={() => navigate(`/visits/${visit.id}`)}
        />
      ) : null}
      {!isLoadingContext && !contextError && patient && visit && role !== "doctor" ? (
        <section className="panel">
          <p className="status-error">Only doctors can author prescriptions in this workflow.</p>
          <Link className="secondary-button link-button" to={`/visits/${visit.id}`}>
            Return to visit
          </Link>
        </section>
      ) : null}
    </div>
  );
}
