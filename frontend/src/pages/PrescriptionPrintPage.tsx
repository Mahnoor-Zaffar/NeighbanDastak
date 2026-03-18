import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getPatient, getPrescription, type Patient, type Prescription } from "../app/api";
import { resolveDoctorDisplayName } from "../app/doctorIdentity";
import { getStoredDemoRole } from "../app/demoRole";

export function PrescriptionPrintPage() {
  const navigate = useNavigate();
  const { prescriptionId } = useParams<{ prescriptionId: string }>();
  const [prescription, setPrescription] = useState<Prescription | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const role = getStoredDemoRole() ?? "doctor";
  const doctorName = useMemo(
    () => (prescription ? resolveDoctorDisplayName(prescription.doctor_id) : "Attending Doctor"),
    [prescription],
  );

  useEffect(() => {
    const resolvedPrescriptionId = prescriptionId ?? "";
    if (!resolvedPrescriptionId) {
      setIsLoading(false);
      setError("Missing prescription identifier.");
      return;
    }

    let active = true;
    async function loadDocument() {
      setIsLoading(true);
      try {
        const prescriptionResponse = await getPrescription(role, resolvedPrescriptionId);
        if (!active) {
          return;
        }
        setPrescription(prescriptionResponse);

        const patientResponse = await getPatient(role, prescriptionResponse.patient_id).catch(() => null);
        if (!active) {
          return;
        }
        setPatient(patientResponse);
        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setPrescription(null);
        setPatient(null);
        setError(loadError instanceof Error ? loadError.message : "Unable to load printable prescription");
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadDocument();
    return () => {
      active = false;
    };
  }, [prescriptionId, role]);

  return (
    <main className="print-page-shell">
      <div className="print-toolbar no-print">
        <button className="secondary-button" onClick={() => navigate(-1)} type="button">
          Back
        </button>
        <button className="primary-button" onClick={() => window.print()} type="button">
          Print / Save PDF
        </button>
        {prescription ? (
          <Link className="secondary-button link-button" to={`/prescriptions/${prescription.id}`}>
            Open prescription detail
          </Link>
        ) : null}
      </div>

      {isLoading ? (
        <section className="print-loading-card">
          <p>Preparing printable prescription...</p>
        </section>
      ) : null}
      {error ? (
        <section className="print-loading-card">
          <p className="status-error">{error}</p>
        </section>
      ) : null}

      {!isLoading && !error && prescription ? (
        <article className="prescription-print-sheet">
          <header className="prescription-print-header">
            <div>
              <p className="clinic-brand">NigehbaanDastak Clinic</p>
              <p className="clinic-meta">Community Care Center</p>
              <p className="clinic-meta">Karachi, Pakistan | +92 21 5555 0123</p>
            </div>
            <div className="clinic-license">
              <p>Prescription Document</p>
              <p>No: {prescription.id.slice(0, 8).toUpperCase()}</p>
            </div>
          </header>

          <section className="prescription-patient-grid">
            <div>
              <dt>Patient Name</dt>
              <dd>{patient ? `${patient.first_name} ${patient.last_name}` : "Unknown patient"}</dd>
            </div>
            <div>
              <dt>Date</dt>
              <dd>{new Date(prescription.created_at).toLocaleDateString()}</dd>
            </div>
            <div>
              <dt>Doctor Name</dt>
              <dd>{doctorName}</dd>
            </div>
            <div>
              <dt>Doctor ID</dt>
              <dd>{prescription.doctor_id}</dd>
            </div>
          </section>

          <section className="prescription-block">
            <h2>Diagnosis Summary</h2>
            <p>{prescription.diagnosis_summary}</p>
          </section>

          <section className="prescription-block">
            <h2>Medicines</h2>
            <table className="prescription-print-table">
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Dosage</th>
                  <th>Frequency</th>
                  <th>Duration</th>
                  <th>Instructions</th>
                </tr>
              </thead>
              <tbody>
                {prescription.items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.medicine_name}</td>
                    <td>{item.dosage}</td>
                    <td>{item.frequency}</td>
                    <td>{item.duration}</td>
                    <td>{item.instructions ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="prescription-block">
            <h2>General Notes</h2>
            <p>{prescription.notes ?? "No additional notes."}</p>
          </section>

          <footer className="prescription-footer">
            <p>This document is generated from NigehbaanDastak clinical records.</p>
            <p>Doctor Signature: __________________________</p>
          </footer>
        </article>
      ) : null}
    </main>
  );
}
