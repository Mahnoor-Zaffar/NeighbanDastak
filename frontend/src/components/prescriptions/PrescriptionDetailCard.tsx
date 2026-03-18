import type { Prescription } from "../../app/api";

interface PrescriptionDetailCardProps {
  prescription: Prescription;
  doctorName: string;
}

export function PrescriptionDetailCard({ prescription, doctorName }: PrescriptionDetailCardProps) {
  return (
    <section className="panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">Prescription</p>
          <h2 className="section-title">{prescription.diagnosis_summary}</h2>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          <p>Authored: {new Date(prescription.created_at).toLocaleString()}</p>
          <p>Doctor: {doctorName}</p>
        </div>
      </div>

      <div className="detail-grid">
        <div>
          <dt>Patient ID</dt>
          <dd>{prescription.patient_id}</dd>
        </div>
        <div>
          <dt>Visit ID</dt>
          <dd>{prescription.visit_id}</dd>
        </div>
        <div>
          <dt>Updated</dt>
          <dd>{new Date(prescription.updated_at).toLocaleString()}</dd>
        </div>
        <div>
          <dt>Notes</dt>
          <dd>{prescription.notes ?? "—"}</dd>
        </div>
      </div>

      <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-600">Medicine orders</h3>
        <div className="overflow-x-auto">
          <table className="data-table">
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
        </div>
      </div>
    </section>
  );
}
