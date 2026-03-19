export type DemoRole = "admin" | "doctor" | "receptionist";

const STORAGE_KEY = "nd-demo-role";
const SESSION_KEY = "nd-demo-session";

export interface DemoSession {
  role: DemoRole;
  userId: string | null;
  doctorProfileId: string | null;
  fullName: string | null;
  email: string | null;
}

export function isDemoRole(value: string | null): value is DemoRole {
  return value === "admin" || value === "doctor" || value === "receptionist";
}

export function getStoredDemoRole(): DemoRole | null {
  const session = getStoredDemoSession();
  if (session) {
    return session.role;
  }

  const storedRole = window.localStorage.getItem(STORAGE_KEY);
  if (isDemoRole(storedRole)) {
    return storedRole;
  }

  return null;
}

export function storeDemoRole(role: DemoRole): void {
  window.localStorage.setItem(STORAGE_KEY, role);
  const currentSession = getStoredDemoSession();
  if (currentSession) {
    storeDemoSession({
      ...currentSession,
      role,
      userId: role === "doctor" ? currentSession.userId : null,
      doctorProfileId: role === "doctor" ? currentSession.doctorProfileId : null,
      fullName: role === "doctor" ? currentSession.fullName : null,
      email: role === "doctor" ? currentSession.email : null,
    });
  }
}

export function clearStoredDemoRole(): void {
  window.localStorage.removeItem(STORAGE_KEY);
  window.localStorage.removeItem(SESSION_KEY);
}

export function getStoredDemoSession(): DemoSession | null {
  try {
    const raw = window.localStorage.getItem(SESSION_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as Partial<DemoSession>;
    const parsedRole = parsed?.role ?? null;
    if (!parsed || !isDemoRole(parsedRole)) {
      return null;
    }

    return {
      role: parsedRole,
      userId: normalizeNullable(parsed.userId),
      doctorProfileId: normalizeNullable(parsed.doctorProfileId),
      fullName: normalizeNullable(parsed.fullName),
      email: normalizeNullable(parsed.email),
    };
  } catch {
    return null;
  }
}

export function storeDemoSession(session: DemoSession): void {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  window.localStorage.setItem(STORAGE_KEY, session.role);
}

export function updateStoredDemoSession(patch: Partial<DemoSession>): void {
  const current = getStoredDemoSession();
  if (!current) {
    return;
  }

  const next: DemoSession = {
    ...current,
    ...patch,
    role: patch.role && isDemoRole(patch.role) ? patch.role : current.role,
  };
  storeDemoSession(next);
}

function normalizeNullable(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized || null;
}
