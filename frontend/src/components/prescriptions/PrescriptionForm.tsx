import { useMemo, useState, type FormEvent } from "react";

import type { DemoRole, PrescriptionItemFormPayload } from "../../app/api";

export interface PrescriptionFormValues {
  doctor_id: string;
  doctor_name: string;
  diagnosis_summary: string;
  notes: string;
  items: PrescriptionItemFormPayload[];
}

interface PrescriptionFormProps {
  mode: "create" | "edit";
  role: DemoRole;
  patientId: string;
  visitId: string;
  initialValues?: Partial<PrescriptionFormValues>;
  isSubmitting: boolean;
  submitError: string | null;
  onSubmit: (values: PrescriptionFormValues) => Promise<void>;
  onDoctorProfileChange?: (doctorId: string, doctorName: string) => void;
  onCancel?: () => void;
}

function emptyMedicineItem(): PrescriptionItemFormPayload {
  return {
    medicine_name: "",
    dosage: "",
    frequency: "",
    duration: "",
    instructions: "",
  };
}

export function PrescriptionForm({
  mode,
  role,
  patientId,
  visitId,
  initialValues,
  isSubmitting,
  submitError,
  onSubmit,
  onDoctorProfileChange,
  onCancel,
}: PrescriptionFormProps) {
  const [doctorId, setDoctorId] = useState(initialValues?.doctor_id ?? "");
  const [doctorName, setDoctorName] = useState(initialValues?.doctor_name ?? "");
  const [diagnosisSummary, setDiagnosisSummary] = useState(initialValues?.diagnosis_summary ?? "");
  const [notes, setNotes] = useState(initialValues?.notes ?? "");
  const [items, setItems] = useState<PrescriptionItemFormPayload[]>(
    initialValues?.items?.length ? initialValues.items : [emptyMedicineItem()],
  );
  const [validationError, setValidationError] = useState<string | null>(null);

  const isReadOnlyRole = role === "receptionist";
  const modeLabel = mode === "create" ? "Create prescription" : "Update prescription";
  const submitLabel = mode === "create" ? "Save prescription" : "Save changes";

  const canSubmit = useMemo(() => {
    return !isSubmitting && !isReadOnlyRole;
  }, [isReadOnlyRole, isSubmitting]);

  function updateMedicineRow(index: number, patch: Partial<PrescriptionItemFormPayload>) {
    setItems((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)));
  }

  function addMedicineRow() {
    setItems((current) => [...current, emptyMedicineItem()]);
  }

  function removeMedicineRow(index: number) {
    setItems((current) => {
      if (current.length === 1) {
        return current;
      }
      return current.filter((_, itemIndex) => itemIndex !== index);
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);

    if (mode === "create" && !doctorId.trim()) {
      setValidationError("Doctor ID is required to author this prescription.");
      return;
    }
    if (!diagnosisSummary.trim()) {
      setValidationError("Diagnosis summary is required.");
      return;
    }
    if (items.length === 0) {
      setValidationError("At least one medicine item is required.");
      return;
    }

    const firstIncompleteIndex = items.findIndex(
      (item) =>
        !item.medicine_name.trim() || !item.dosage.trim() || !item.frequency.trim() || !item.duration.trim(),
    );
    if (firstIncompleteIndex >= 0) {
      setValidationError(`Medicine row ${firstIncompleteIndex + 1} is missing required fields.`);
      return;
    }

    await onSubmit({
      doctor_id: doctorId.trim(),
      doctor_name: doctorName.trim(),
      diagnosis_summary: diagnosisSummary,
      notes,
      items,
    });
  }

  return (
    <form className="panel form-stack" onSubmit={(event) => void handleSubmit(event)}>
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <p className="font-medium text-slate-900">{modeLabel}</p>
        <p className="mt-1">Patient ID: {patientId}</p>
        <p>Visit ID: {visitId}</p>
      </div>

      {mode === "create" ? (
        <>
          <label className="field-stack">
            <span className="field-label">Doctor ID</span>
            <input
              className="text-input"
              placeholder="UUID of doctor user profile"
              value={doctorId}
              onChange={(event) => {
                const nextId = event.target.value;
                setDoctorId(nextId);
                onDoctorProfileChange?.(nextId, doctorName);
              }}
              required
              disabled={isReadOnlyRole}
            />
          </label>
          <label className="field-stack">
            <span className="field-label">Doctor name</span>
            <input
              className="text-input"
              placeholder="e.g. Dr. Ayesha Khan"
              value={doctorName}
              onChange={(event) => {
                const nextName = event.target.value;
                setDoctorName(nextName);
                onDoctorProfileChange?.(doctorId, nextName);
              }}
              disabled={isReadOnlyRole}
            />
            <p className="muted-note">Used in print/export output and saved locally on this browser.</p>
          </label>
        </>
      ) : null}

      <label className="field-stack">
        <span className="field-label">Diagnosis summary</span>
        <input
          className="text-input"
          maxLength={255}
          value={diagnosisSummary}
          onChange={(event) => setDiagnosisSummary(event.target.value)}
          required
          disabled={isReadOnlyRole}
        />
      </label>

      <label className="field-stack">
        <span className="field-label">Notes</span>
        <textarea
          className="text-area"
          rows={4}
          maxLength={2000}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          disabled={isReadOnlyRole}
        />
      </label>

      <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-600">Medicines</h3>
          <button className="secondary-button" type="button" onClick={addMedicineRow} disabled={isReadOnlyRole}>
            Add medicine
          </button>
        </div>

        <div className="space-y-3">
          {items.map((item, index) => (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3" key={`medicine-row-${index}`}>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-800">Medicine #{index + 1}</p>
                <button
                  className="table-button"
                  type="button"
                  onClick={() => removeMedicineRow(index)}
                  disabled={isReadOnlyRole || items.length === 1}
                >
                  Remove
                </button>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <label className="field-stack">
                  <span className="field-label">Medicine name</span>
                  <input
                    className="text-input"
                    value={item.medicine_name}
                    onChange={(event) => updateMedicineRow(index, { medicine_name: event.target.value })}
                    required
                    disabled={isReadOnlyRole}
                  />
                </label>
                <label className="field-stack">
                  <span className="field-label">Dosage</span>
                  <input
                    className="text-input"
                    value={item.dosage}
                    onChange={(event) => updateMedicineRow(index, { dosage: event.target.value })}
                    required
                    disabled={isReadOnlyRole}
                  />
                </label>
                <label className="field-stack">
                  <span className="field-label">Frequency</span>
                  <input
                    className="text-input"
                    value={item.frequency}
                    onChange={(event) => updateMedicineRow(index, { frequency: event.target.value })}
                    required
                    disabled={isReadOnlyRole}
                  />
                </label>
                <label className="field-stack">
                  <span className="field-label">Duration</span>
                  <input
                    className="text-input"
                    value={item.duration}
                    onChange={(event) => updateMedicineRow(index, { duration: event.target.value })}
                    required
                    disabled={isReadOnlyRole}
                  />
                </label>
              </div>
              <label className="field-stack mt-3">
                <span className="field-label">Instructions</span>
                <textarea
                  className="text-area"
                  rows={2}
                  value={item.instructions}
                  onChange={(event) => updateMedicineRow(index, { instructions: event.target.value })}
                  disabled={isReadOnlyRole}
                />
              </label>
            </div>
          ))}
        </div>
      </div>

      {isReadOnlyRole ? <p className="status-error">Receptionist role cannot create or edit prescriptions.</p> : null}
      {validationError ? <p className="status-error">{validationError}</p> : null}
      {submitError ? <p className="status-error">{submitError}</p> : null}

      <div className="action-row">
        {onCancel ? (
          <button className="secondary-button" type="button" onClick={onCancel}>
            Cancel
          </button>
        ) : null}
        <button className="primary-button" type="submit" disabled={!canSubmit}>
          {isSubmitting ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}
