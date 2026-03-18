import { useMemo, useState, type FormEvent } from "react";

import type { DemoRole } from "../../app/api";

export interface FollowUpFormValues {
  doctor_id: string;
  doctor_name: string;
  due_date: string;
  reason: string;
  notes: string;
}

interface FollowUpFormProps {
  role: DemoRole;
  patientId: string;
  visitId: string;
  initialValues?: Partial<FollowUpFormValues>;
  isSubmitting: boolean;
  submitError: string | null;
  onSubmit: (values: FollowUpFormValues) => Promise<void>;
  onDoctorProfileChange?: (doctorId: string, doctorName: string) => void;
  onCancel?: () => void;
}

export function FollowUpForm({
  role,
  patientId,
  visitId,
  initialValues,
  isSubmitting,
  submitError,
  onSubmit,
  onDoctorProfileChange,
  onCancel,
}: FollowUpFormProps) {
  const [doctorId, setDoctorId] = useState(initialValues?.doctor_id ?? "");
  const [doctorName, setDoctorName] = useState(initialValues?.doctor_name ?? "");
  const [dueDate, setDueDate] = useState(initialValues?.due_date ?? "");
  const [reason, setReason] = useState(initialValues?.reason ?? "");
  const [notes, setNotes] = useState(initialValues?.notes ?? "");
  const [validationError, setValidationError] = useState<string | null>(null);

  const isReadOnlyRole = role === "receptionist";
  const canSubmit = useMemo(() => !isReadOnlyRole && !isSubmitting, [isReadOnlyRole, isSubmitting]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);

    if (!doctorId.trim()) {
      setValidationError("Doctor profile ID is required to create follow-up reminders.");
      return;
    }
    if (!dueDate) {
      setValidationError("Due date is required.");
      return;
    }
    if (!reason.trim()) {
      setValidationError("Reason is required.");
      return;
    }

    await onSubmit({
      doctor_id: doctorId.trim(),
      doctor_name: doctorName.trim(),
      due_date: dueDate,
      reason,
      notes,
    });
  }

  return (
    <form className="panel form-stack" onSubmit={(event) => void handleSubmit(event)}>
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <p className="font-medium text-slate-900">Create follow-up reminder</p>
        <p className="mt-1">Patient ID: {patientId}</p>
        <p>Visit ID: {visitId}</p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <label className="field-stack">
          <span className="field-label">Doctor profile ID</span>
          <input
            className="text-input"
            value={doctorId}
            onChange={(event) => {
              const nextId = event.target.value;
              setDoctorId(nextId);
              onDoctorProfileChange?.(nextId, doctorName);
            }}
            placeholder="UUID from doctor account"
            required
            disabled={isReadOnlyRole}
          />
        </label>
        <label className="field-stack">
          <span className="field-label">Doctor display name</span>
          <input
            className="text-input"
            value={doctorName}
            onChange={(event) => {
              const nextName = event.target.value;
              setDoctorName(nextName);
              onDoctorProfileChange?.(doctorId, nextName);
            }}
            placeholder="e.g. Dr. Ayesha Khan"
            disabled={isReadOnlyRole}
          />
          <p className="muted-note">Saved locally for smoother clinical workflows.</p>
        </label>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <label className="field-stack">
          <span className="field-label">Due date</span>
          <input
            className="text-input"
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
            required
            disabled={isReadOnlyRole}
          />
        </label>
        <label className="field-stack">
          <span className="field-label">Reason</span>
          <input
            className="text-input"
            maxLength={255}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Why this follow-up is needed"
            required
            disabled={isReadOnlyRole}
          />
        </label>
      </div>

      <label className="field-stack">
        <span className="field-label">Notes</span>
        <textarea
          className="text-area"
          rows={3}
          maxLength={2000}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          disabled={isReadOnlyRole}
        />
      </label>

      {isReadOnlyRole ? <p className="status-error">Receptionist role cannot create follow-up reminders.</p> : null}
      {validationError ? <p className="status-error">{validationError}</p> : null}
      {submitError ? <p className="status-error">{submitError}</p> : null}

      <div className="action-row">
        {onCancel ? (
          <button className="secondary-button" type="button" onClick={onCancel}>
            Cancel
          </button>
        ) : null}
        <button className="primary-button" type="submit" disabled={!canSubmit}>
          {isSubmitting ? "Saving..." : "Save follow-up"}
        </button>
      </div>
    </form>
  );
}
