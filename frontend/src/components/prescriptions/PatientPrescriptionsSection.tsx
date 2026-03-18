import { Link } from "react-router-dom";

import type { DemoRole, Prescription } from "../../app/api";

interface PatientPrescriptionsSectionProps {
  role: DemoRole;
  patientId: string;
  loading: boolean;
  error: string | null;
  prescriptions: Prescription[];
}

export function PatientPrescriptionsSection({
  role,
  patientId,
  loading,
  error,
  prescriptions,
}: PatientPrescriptionsSectionProps) {
  const canCreate = role === "doctor";

  return (
    <section className="panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">Prescription history</p>
          <h3 className="text-2xl font-semibold tracking-tight text-slate-900">Clinical medication records</h3>
          <p className="mt-1 text-sm text-slate-500">
            Review past prescriptions and jump to detailed medicine instructions.
          </p>
        </div>
        {canCreate ? (
          <Link className="secondary-button link-button" to={`/visits/new?patient_id=${patientId}`}>
            Start a visit to prescribe
          </Link>
        ) : null}
      </div>

      {loading ? <p className="muted-note">Loading prescription history...</p> : null}
      {error ? <p className="status-error">{error}</p> : null}
      {!loading && !error && prescriptions.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
          No prescriptions available for this patient yet.
        </div>
      ) : null}
      {prescriptions.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Diagnosis</th>
                <th>Medicines</th>
                <th>Visit</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {prescriptions.map((prescription) => (
                <tr key={prescription.id}>
                  <td>{new Date(prescription.created_at).toLocaleString()}</td>
                  <td>{prescription.diagnosis_summary}</td>
                  <td>{prescription.items.length}</td>
                  <td>{prescription.visit_id.slice(0, 8)}...</td>
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
  );
}
