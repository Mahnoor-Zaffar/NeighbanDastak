import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";

import type { PatientFormPayload } from "../app/api";

const RECORD_NUMBER_REGEX = /^PAT-[A-Z0-9-]{1,28}$/;
const PHONE_REGEX = /^[0-9+() -]{7,20}$/;

interface PatientFormProps {
  initialValues?: PatientFormPayload;
  isSubmitting: boolean;
  submitLabel: string;
  onSubmit: (values: PatientFormPayload) => Promise<void>;
}

export function PatientForm({
  initialValues,
  isSubmitting,
  submitLabel,
  onSubmit,
}: PatientFormProps) {
  const [formState, setFormState] = useState<PatientFormPayload>({
    record_number: initialValues?.record_number ?? "",
    first_name: initialValues?.first_name ?? "",
    last_name: initialValues?.last_name ?? "",
    date_of_birth: initialValues?.date_of_birth ?? "",
    email: initialValues?.email ?? "",
    phone: initialValues?.phone ?? "",
    city: initialValues?.city ?? "",
    notes: initialValues?.notes ?? "",
  });
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (!initialValues) {
      return;
    }

    setFormState(initialValues);
  }, [initialValues]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized: PatientFormPayload = {
      record_number: formState.record_number.trim().toUpperCase(),
      first_name: formState.first_name.trim(),
      last_name: formState.last_name.trim(),
      date_of_birth: formState.date_of_birth,
      email: formState.email.trim(),
      phone: formState.phone.trim(),
      city: formState.city.trim(),
      notes: formState.notes.trim(),
    };

    if (!normalized.first_name || !normalized.last_name || !normalized.date_of_birth) {
      setFormError("First name, last name, and date of birth are required.");
      return;
    }
    if (normalized.record_number && !RECORD_NUMBER_REGEX.test(normalized.record_number)) {
      setFormError("Record number must follow PAT-XXXX format.");
      return;
    }
    if (normalized.phone && !PHONE_REGEX.test(normalized.phone)) {
      setFormError("Phone must contain 7 to 20 digits or phone symbols.");
      return;
    }

    setFormError(null);
    await onSubmit(normalized);
  }

  function handleChange(event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const { name, value } = event.target;
    setFormState((current) => ({ ...current, [name]: value }));
  }

  return (
    <form className="panel form-stack" onSubmit={handleSubmit}>
      <div className="grid-two">
        <label className="field-stack">
          <span className="field-label">Record number</span>
          <input
            className="text-input"
            name="record_number"
            value={formState.record_number}
            onChange={handleChange}
            placeholder="Leave blank to auto-generate"
            maxLength={32}
          />
        </label>
        <label className="field-stack">
          <span className="field-label">Date of birth</span>
          <input
            required
            className="text-input"
            type="date"
            name="date_of_birth"
            value={formState.date_of_birth}
            onChange={handleChange}
            min="1900-01-01"
            max={new Date().toISOString().slice(0, 10)}
          />
        </label>
      </div>

      <div className="grid-two">
        <label className="field-stack">
          <span className="field-label">First name</span>
          <input
            required
            className="text-input"
            name="first_name"
            value={formState.first_name}
            onChange={handleChange}
            maxLength={100}
          />
        </label>
        <label className="field-stack">
          <span className="field-label">Last name</span>
          <input
            required
            className="text-input"
            name="last_name"
            value={formState.last_name}
            onChange={handleChange}
            maxLength={100}
          />
        </label>
      </div>

      <div className="grid-two">
        <label className="field-stack">
          <span className="field-label">Email</span>
          <input
            className="text-input"
            type="email"
            name="email"
            value={formState.email}
            onChange={handleChange}
            maxLength={255}
          />
        </label>
        <label className="field-stack">
          <span className="field-label">Phone</span>
          <input
            className="text-input"
            name="phone"
            value={formState.phone}
            onChange={handleChange}
            maxLength={20}
          />
        </label>
      </div>

      <label className="field-stack">
        <span className="field-label">City</span>
        <input className="text-input" maxLength={120} name="city" value={formState.city} onChange={handleChange} />
      </label>

      <label className="field-stack">
        <span className="field-label">Notes</span>
        <textarea
          className="text-area"
          name="notes"
          rows={4}
          value={formState.notes}
          onChange={handleChange}
          maxLength={1000}
        />
      </label>

      {formError ? <p className="status-error">{formError}</p> : null}
      <button className="primary-button" disabled={isSubmitting} type="submit">
        {isSubmitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
