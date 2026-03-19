import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { listDemoDoctorProfiles, loginDemoUser, type DemoDoctorProfile } from "../app/api";
import { getStoredDemoRole, getStoredDemoSession, storeDemoSession, type DemoRole } from "../app/demoRole";
import { rememberDoctorProfile } from "../app/doctorIdentity";

export function DemoAuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedRole, setSelectedRole] = useState<DemoRole>("doctor");
  const [doctorProfiles, setDoctorProfiles] = useState<DemoDoctorProfile[]>([]);
  const [selectedDoctorProfileId, setSelectedDoctorProfileId] = useState("");
  const [loadingDoctors, setLoadingDoctors] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fromPath = (location.state as { from?: string } | null)?.from ?? "/appointments";

  useEffect(() => {
    const storedRole = getStoredDemoRole();
    const storedSession = getStoredDemoSession();
    if (storedRole && (storedRole !== "doctor" || !!storedSession?.doctorProfileId)) {
      navigate(fromPath, { replace: true });
    }
  }, [fromPath, navigate]);

  useEffect(() => {
    if (selectedRole !== "doctor") {
      return;
    }

    let active = true;
    async function loadDoctorProfiles() {
      setLoadingDoctors(true);
      setError(null);
      try {
        const response = await listDemoDoctorProfiles();
        if (!active) {
          return;
        }
        setDoctorProfiles(response.items);
        setSelectedDoctorProfileId((current) => current || response.items[0]?.id || "");
      } catch (loadError) {
        if (!active) {
          return;
        }
        setDoctorProfiles([]);
        setSelectedDoctorProfileId("");
        setError(loadError instanceof Error ? loadError.message : "Unable to load doctor profiles");
      } finally {
        if (active) {
          setLoadingDoctors(false);
        }
      }
    }

    void loadDoctorProfiles();
    return () => {
      active = false;
    };
  }, [selectedRole]);

  async function handleContinue() {
    setSubmitting(true);
    setError(null);
    try {
      const currentUser = await loginDemoUser({
        role: selectedRole,
        doctor_profile_id: selectedRole === "doctor" ? selectedDoctorProfileId || undefined : undefined,
      });

      storeDemoSession({
        role: currentUser.role,
        userId: currentUser.user_id,
        doctorProfileId: currentUser.doctor_profile_id,
        fullName: currentUser.full_name,
        email: currentUser.email,
      });
      if (currentUser.doctor_profile_id) {
        rememberDoctorProfile(currentUser.doctor_profile_id, currentUser.full_name ?? "");
      }
      navigate(fromPath, { replace: true });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to start demo session");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <p className="eyebrow">Demo access</p>
        <h1>Choose a role to continue</h1>
        <p className="lede">
          This MVP frontend uses role simulation for demo readiness. You can switch roles later in the sidebar.
        </p>

        <div className="auth-role-grid">
          <button
            className={selectedRole === "doctor" ? "role-button active" : "role-button"}
            type="button"
            onClick={() => {
              setSelectedRole("doctor");
              setError(null);
            }}
          >
            Doctor
            <span>Read/search + appointment/visit actions</span>
          </button>
          <button
            className={selectedRole === "admin" ? "role-button active" : "role-button"}
            type="button"
            onClick={() => {
              setSelectedRole("admin");
              setError(null);
            }}
          >
            Admin
            <span>Full demo permissions including patient lifecycle</span>
          </button>
          <button
            className={selectedRole === "receptionist" ? "role-button active" : "role-button"}
            type="button"
            onClick={() => {
              setSelectedRole("receptionist");
              setError(null);
            }}
          >
            Receptionist
            <span>Read-only intake simulation with no clinical write controls</span>
          </button>
        </div>

        {selectedRole === "doctor" ? (
          <label className="field-stack">
            <span className="field-label">Doctor profile</span>
            <select
              className="text-input"
              value={selectedDoctorProfileId}
              onChange={(event) => setSelectedDoctorProfileId(event.target.value)}
              disabled={loadingDoctors || doctorProfiles.length === 0}
            >
              {doctorProfiles.length === 0 ? <option value="">No doctor profiles found</option> : null}
              {doctorProfiles.map((doctorProfile) => (
                <option key={doctorProfile.id} value={doctorProfile.id}>
                  {doctorProfile.full_name}
                </option>
              ))}
            </select>
            <p className="muted-note">
              {loadingDoctors ? "Loading doctor profiles..." : "Your doctor profile ID is linked automatically."}
            </p>
          </label>
        ) : null}

        {error ? <p className="status-error">{error}</p> : null}

        <button
          className="primary-button auth-continue"
          type="button"
          onClick={() => void handleContinue()}
          disabled={submitting || (selectedRole === "doctor" && !selectedDoctorProfileId)}
        >
          {submitting ? "Entering..." : "Enter demo"}
        </button>
      </section>
    </main>
  );
}
