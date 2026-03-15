import { Navigate, Outlet, useLocation } from "react-router-dom";

import { getStoredDemoRole } from "../app/demoRole";

export function AuthGate() {
  const location = useLocation();
  const role = getStoredDemoRole();

  if (!role) {
    const target = `${location.pathname}${location.search}`;
    return <Navigate replace state={{ from: target }} to="/auth" />;
  }

  return <Outlet />;
}
