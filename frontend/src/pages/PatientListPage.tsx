import { useEffect, useState, type FormEvent } from "react";
import { Link, useOutletContext } from "react-router-dom";

import { archivePatient, listPatients, type Patient, type PatientListResponse } from "../app/api";
import type { AppLayoutContext } from "../components/AppLayout";

export function PatientListPage() {
  const { role } = useOutletContext<AppLayoutContext>();
  const [data, setData] = useState<PatientListResponse | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionBusyId, setActionBusyId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadPatients() {
      setLoading(true);
      try {
        const response = await listPatients(role, searchTerm, includeArchived);
        if (!active) {
          return;
        }

        setData(response);
        setError(null);
      } catch (loadError) {
        if (!active) {
          return;
        }

        setData(null);
        setError(loadError instanceof Error ? loadError.message : "Unable to load patients");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadPatients();

    return () => {
      active = false;
    };
  }, [includeArchived, reloadKey, role, searchTerm]);

  async function handleArchive(patient: Patient) {
    setError(null);
    setActionBusyId(patient.id);
    try {
      await archivePatient(role, patient.id);
      const refreshed = await listPatients(role, searchTerm, includeArchived);
      setData(refreshed);
    } catch (archiveError) {
      setError(archiveError instanceof Error ? archiveError.message : "Unable to archive patient");
    } finally {
      setActionBusyId(null);
    }
  }

  function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSearchTerm(searchInput.trim());
  }

  return (
    <div className="content-stack">
      <section className="panel panel-header">
        <div>
          <p className="eyebrow">Patient directory</p>
          <h2 className="section-title">Synthetic demo records</h2>
          <p className="lede">
            Doctors can view and search patients. Admins can create, update, and archive.
          </p>
        </div>
        {role === "admin" ? (
          <Link className="primary-button link-button" to="/patients/new">
            Add patient
          </Link>
        ) : null}
      </section>

      <section className="panel">
        <form className="toolbar" onSubmit={handleSearchSubmit}>
          <input
            className="text-input"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by name, record number, email, or phone"
          />
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(event) => setIncludeArchived(event.target.checked)}
            />
            <span>Include archived</span>
          </label>
          <button className="secondary-button" type="submit">
            Search
          </button>
        </form>

        {loading ? <p>Loading patients...</p> : null}
        {error ? (
          <div className="empty-state">
            <p className="status-error">{error}</p>
            <button className="secondary-button" type="button" onClick={() => setReloadKey((current) => current + 1)}>
              Retry
            </button>
          </div>
        ) : null}
        {!loading && !error && data?.items.length === 0 ? (
          <div className="empty-state">
            <p>No patients found.</p>
            {role === "admin" ? (
              <Link className="primary-button link-button" to="/patients/new">
                Add patient
              </Link>
            ) : null}
          </div>
        ) : null}
        {data?.items.length ? (
          <PatientTable patients={data.items} role={role} onArchive={handleArchive} actionBusyId={actionBusyId} />
        ) : null}
      </section>
    </div>
  );
}

interface PatientTableProps {
  patients: Patient[];
  role: AppLayoutContext["role"];
  onArchive: (patient: Patient) => Promise<void>;
  actionBusyId: string | null;
}

function PatientTable({ patients, role, onArchive, actionBusyId }: PatientTableProps) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Record</th>
            <th>Name</th>
            <th>DOB</th>
            <th>City</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((patient) => (
            <tr key={patient.id}>
              <td>{patient.record_number}</td>
              <td>
                {patient.first_name} {patient.last_name}
              </td>
              <td>{patient.date_of_birth}</td>
              <td>{patient.city ?? "—"}</td>
              <td>{patient.archived_at ? "Archived" : "Active"}</td>
              <td className="table-actions">
                <Link className="table-link" to={`/patients/${patient.id}`}>
                  View
                </Link>
                {role === "admin" ? (
                  <>
                    <Link className="table-link" to={`/patients/${patient.id}/edit`}>
                      Edit
                    </Link>
                    {!patient.archived_at ? (
                      <button
                        className="table-button"
                        type="button"
                        disabled={actionBusyId === patient.id}
                        onClick={() => void onArchive(patient)}
                      >
                        {actionBusyId === patient.id ? "Archiving..." : "Archive"}
                      </button>
                    ) : null}
                  </>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
