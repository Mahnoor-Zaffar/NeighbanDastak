import { Navigate, Outlet, useLocation } from "react-router-dom";

import { getStoredDemoRole, getStoredDemoSession } from "../app/demoRole";

export function AuthGate() {
  const location = useLocation();
  const role = getStoredDemoRole();
  const session = getStoredDemoSession();

  if (!role) {
    const target = `${location.pathname}${location.search}`;
    return <Navigate replace state={{ from: target }} to="/auth" />;
  }

  if (role === "doctor" && (!session || !session.doctorProfileId)) {
    const target = `${location.pathname}${location.search}`;
    return <Navigate replace state={{ from: target }} to="/auth" />;
  }

  return <Outlet />;
}
