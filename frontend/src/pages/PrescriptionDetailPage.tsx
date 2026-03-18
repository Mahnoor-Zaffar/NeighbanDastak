import { useEffect, useState } from "react";
import { Link, useNavigate, useOutletContext, useParams } from "react-router-dom";

import {
  deletePrescription,
  getPatient,
  getPrescription,
  getVisit,
  updatePrescription,
  type Patient,
  type Prescription,
  type Visit,
} from "../app/api";
import type { AppLayoutContext } from "../components/AppLayout";
import { resolveDoctorDisplayName } from "../app/doctorIdentity";
import { PrescriptionDetailCard } from "../components/prescriptions/PrescriptionDetailCard";
import { PrescriptionForm, type PrescriptionFormValues } from "../components/prescriptions/PrescriptionForm";

export function PrescriptionDetailPage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const { prescriptionId } = useParams<{ prescriptionId: string }>();
  const navigate = useNavigate();
  const [prescription, setPrescription] = useState<Prescription | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [visit, setVisit] = useState<Visit | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const canWrite = role === "doctor";
  const doctorName = prescription ? resolveDoctorDisplayName(prescription.doctor_id) : "Attending Doctor";

  useEffect(() => {
    const resolvedPrescriptionId = prescriptionId ?? "";
    if (!resolvedPrescriptionId) {
      setIsLoading(false);
      setError("Missing prescription identifier.");
      return;
    }

    let active = true;
    async function loadPrescription() {
      setIsLoading(true);
      try {
        const response = await getPrescription(role, resolvedPrescriptionId);
        if (!active) {
          return;
        }
        setPrescription(response);
        setError(null);

        const [patientResponse, visitResponse] = await Promise.all([
          getPatient(role, response.patient_id).catch(() => null),
          getVisit(role, response.visit_id).catch(() => null),
        ]);
        if (!active) {
          return;
        }
        setPatient(patientResponse);
        setVisit(visitResponse);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setPrescription(null);
        setPatient(null);
        setVisit(null);
        setError(loadError instanceof Error ? loadError.message : "Unable to load prescription");
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadPrescription();
    return () => {
      active = false;
    };
  }, [prescriptionId, role]);

  async function handleUpdate(values: PrescriptionFormValues) {
    if (!prescription) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const updated = await updatePrescription(role, prescription.id, {
        diagnosis_summary: values.diagnosis_summary,
        notes: values.notes,
        items: values.items,
      });
      setPrescription(updated);
      setIsEditing(false);
    } catch (updateError) {
      setSubmitError(updateError instanceof Error ? updateError.message : "Unable to update prescription");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!prescription || !canWrite) {
      return;
    }

    setIsDeleting(true);
    setError(null);
    try {
      await deletePrescription(role, prescription.id);
      navigate(`/patients/${prescription.patient_id}`, { replace: true });
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to delete prescription");
      setIsDeleting(false);
    }
  }

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">Prescription detail</p>
          <h2 className="section-title">Medication plan</h2>
          {patient ? (
            <p className="lede">
              Patient: {patient.first_name} {patient.last_name}
            </p>
          ) : null}
        </div>
        <div className="action-row">
          {visit ? (
            <Link className="secondary-button link-button" to={`/visits/${visit.id}`}>
              View visit
            </Link>
          ) : null}
          {prescription ? (
            <Link className="secondary-button link-button" to={`/patients/${prescription.patient_id}`}>
              Back to patient
            </Link>
          ) : null}
          {prescription ? (
            <Link className="secondary-button link-button" to={`/print/prescriptions/${prescription.id}`}>
              Print / Save PDF
            </Link>
          ) : null}
          {canWrite && prescription ? (
            <button className="secondary-button" type="button" onClick={() => setIsEditing((current) => !current)}>
              {isEditing ? "Close editor" : "Edit"}
            </button>
          ) : null}
          {canWrite && prescription ? (
            <button className="table-button" type="button" onClick={() => void handleDelete()} disabled={isDeleting}>
              {isDeleting ? "Deleting..." : "Delete"}
            </button>
          ) : null}
        </div>
      </section>

      {isLoading ? (
        <section className="panel">
          <p>Loading prescription...</p>
        </section>
      ) : null}
      {error ? <p className="status-error">{error}</p> : null}

      {!isLoading && prescription ? <PrescriptionDetailCard prescription={prescription} doctorName={doctorName} /> : null}

      {!isLoading && isEditing && prescription ? (
        <PrescriptionForm
          key={`${prescription.id}-${prescription.updated_at}`}
          mode="edit"
          role={role}
          patientId={prescription.patient_id}
          visitId={prescription.visit_id}
          initialValues={{
            doctor_name: doctorName,
            diagnosis_summary: prescription.diagnosis_summary,
            notes: prescription.notes ?? "",
            items: prescription.items.map((item) => ({
              medicine_name: item.medicine_name,
              dosage: item.dosage,
              frequency: item.frequency,
              duration: item.duration,
              instructions: item.instructions ?? "",
            })),
          }}
          isSubmitting={isSubmitting}
          submitError={submitError}
          onSubmit={handleUpdate}
          onCancel={() => setIsEditing(false)}
        />
      ) : null}
    </div>
  );
}
