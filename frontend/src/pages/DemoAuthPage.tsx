import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { getStoredDemoRole, storeDemoRole, type DemoRole } from "../app/demoRole";

export function DemoAuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedRole, setSelectedRole] = useState<DemoRole>("doctor");

  const fromPath = (location.state as { from?: string } | null)?.from ?? "/appointments";

  useEffect(() => {
    const storedRole = getStoredDemoRole();
    if (storedRole) {
      navigate(fromPath, { replace: true });
    }
  }, [fromPath, navigate]);

  function handleContinue() {
    storeDemoRole(selectedRole);
    navigate(fromPath, { replace: true });
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
            onClick={() => setSelectedRole("doctor")}
          >
            Doctor
            <span>Read/search + appointment/visit actions</span>
          </button>
          <button
            className={selectedRole === "admin" ? "role-button active" : "role-button"}
            type="button"
            onClick={() => setSelectedRole("admin")}
          >
            Admin
            <span>Full demo permissions including patient lifecycle</span>
          </button>
        </div>

        <button className="primary-button auth-continue" type="button" onClick={handleContinue}>
          Enter demo
        </button>
      </section>
    </main>
  );
}
