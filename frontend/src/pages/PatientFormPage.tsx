import { useEffect, useState } from "react";
import { Link, useNavigate, useOutletContext, useParams } from "react-router-dom";

import {
  createPatient,
  getPatient,
  updatePatient,
  type Patient,
  type PatientFormPayload,
} from "../app/api";
import { PatientForm } from "../components/PatientForm";
import type { AppLayoutContext } from "../components/AppLayout";

interface PatientFormPageProps {
  mode: "create" | "edit";
}

export function PatientFormPage({ mode }: PatientFormPageProps) {
  const { role } = useOutletContext<AppLayoutContext>();
  const navigate = useNavigate();
  const { patientId } = useParams<{ patientId: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(mode === "edit");

  useEffect(() => {
    const resolvedPatientId = patientId!;
    if (mode !== "edit" || !resolvedPatientId) {
      return;
    }

    let active = true;

    async function loadPatient() {
      try {
        const response = await getPatient(role, resolvedPatientId);
        if (!active) {
          return;
        }

        setPatient(response);
        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setPatient(null);
        setError(loadError instanceof Error ? loadError.message : "Unable to load patient");
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadPatient();

    return () => {
      active = false;
    };
  }, [mode, patientId, role]);

  async function handleSubmit(values: PatientFormPayload) {
    setIsSubmitting(true);
    setError(null);

    try {
      const normalizedValues = normalizePayload(values);
      if (mode === "create") {
        const created = await createPatient(role, normalizedValues);
        navigate(`/patients/${created.id}`);
        return;
      }

      const resolvedPatientId = patientId;
      if (!resolvedPatientId) {
        throw new Error("Missing patient id");
      }

      const updated = await updatePatient(role, resolvedPatientId, normalizedValues);
      navigate(`/patients/${updated.id}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to save patient");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (role !== "admin") {
    return (
      <section className="panel">
        <p className="status-error">Only admins can create or edit patients in this phase.</p>
        <Link className="secondary-button link-button" to="/patients">
          Back to patient list
        </Link>
      </section>
    );
  }

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">{mode === "create" ? "Create patient" : "Edit patient"}</p>
          <h2 className="section-title">
            {mode === "create" ? "New patient record" : patient ? patient.record_number : "Loading..."}
          </h2>
        </div>
        <Link className="secondary-button link-button" to="/patients">
          Cancel
        </Link>
      </section>

      {error ? <p className="status-error">{error}</p> : null}
      {isLoading ? (
        <section className="panel">
          <p>Loading patient...</p>
        </section>
      ) : (
        <PatientForm
          initialValues={
            patient
              ? {
                  record_number: patient.record_number,
                  first_name: patient.first_name,
                  last_name: patient.last_name,
                  date_of_birth: patient.date_of_birth,
                  email: patient.email ?? "",
                  phone: patient.phone ?? "",
                  city: patient.city ?? "",
                  notes: patient.notes ?? "",
                }
              : undefined
          }
          isSubmitting={isSubmitting}
          submitLabel={mode === "create" ? "Create patient" : "Save changes"}
          onSubmit={handleSubmit}
        />
      )}
    </div>
  );
}

function normalizePayload(values: PatientFormPayload): PatientFormPayload {
  return {
    record_number: values.record_number.trim(),
    first_name: values.first_name.trim(),
    last_name: values.last_name.trim(),
    date_of_birth: values.date_of_birth,
    email: values.email.trim(),
    phone: values.phone.trim(),
    city: values.city.trim(),
    notes: values.notes.trim(),
  };
}
