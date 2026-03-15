import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { fetchHealth, type HealthResponse } from "../app/api";
import { clearStoredDemoRole, getStoredDemoRole, storeDemoRole, type DemoRole } from "../app/demoRole";
import { HealthCard } from "./HealthCard";

export interface AppLayoutContext {
  role: DemoRole;
}

export function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [role, setRole] = useState<DemoRole>(() => getStoredDemoRole() ?? "doctor");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadHealth() {
      try {
        const response = await fetchHealth();
        if (!active) {
          return;
        }

        setHealth(response);
        setHealthError(null);
      } catch (error) {
        if (!active) {
          return;
        }

        setHealth(null);
        setHealthError(error instanceof Error ? error.message : "Unable to load health status");
      }
    }

    void loadHealth();

    return () => {
      active = false;
    };
  }, []);

  function handleRoleChange(nextRole: DemoRole) {
    storeDemoRole(nextRole);
    setRole(nextRole);
  }

  function handleSignOut() {
    clearStoredDemoRole();
    navigate("/auth", { replace: true });
  }

  const roleLabel = role === "admin" ? "Admin" : "Doctor";

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  return (
    <main className="app-layout">
      <aside id="demo-sidebar" className={mobileNavOpen ? "sidebar mobile-open" : "sidebar"}>
        <div className="sidebar-block">
          <p className="eyebrow">Phase 6 demo</p>
          <h1 className="sidebar-title">
            <Link className="brand-link" to="/appointments">
              NigehbaanDastak
            </Link>
          </h1>
          <p className="muted">
            Minimal clinic MVP demo covering auth simulation, patients, appointments, and visits.
          </p>
        </div>

        <label className="field-stack">
          <span className="field-label">Demo role</span>
          <select
            className="text-input"
            value={role}
            onChange={(event) => handleRoleChange(event.target.value as DemoRole)}
          >
            <option value="admin">Admin</option>
            <option value="doctor">Doctor</option>
          </select>
        </label>
        <button className="secondary-button" type="button" onClick={handleSignOut}>
          Switch demo user
        </button>

        <nav className="nav-stack">
          <NavLink className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")} to="/appointments">
            Appointments
          </NavLink>
          <NavLink className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")} to="/appointments/new">
            New appointment
          </NavLink>
          <NavLink className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")} to="/visits/new">
            New visit
          </NavLink>
          <NavLink className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")} to="/patients">
            Patients
          </NavLink>
          {role === "admin" ? (
            <NavLink
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
              to="/patients/new"
            >
              New patient
            </NavLink>
          ) : null}
        </nav>

        <HealthCard health={health} error={healthError} />
      </aside>

      <section className="content-shell">
        <div className="mobile-topbar">
          <button
            className="secondary-button"
            type="button"
            aria-controls="demo-sidebar"
            aria-expanded={mobileNavOpen}
            onClick={() => setMobileNavOpen((current) => !current)}
          >
            {mobileNavOpen ? "Hide menu" : "Show menu"}
          </button>
          <span className="mobile-role">Role: {roleLabel}</span>
        </div>
        <Outlet context={{ role } satisfies AppLayoutContext} />
      </section>
    </main>
  );
}
