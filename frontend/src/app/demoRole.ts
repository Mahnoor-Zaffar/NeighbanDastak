export type DemoRole = "admin" | "doctor";

const STORAGE_KEY = "nd-demo-role";

export function isDemoRole(value: string | null): value is DemoRole {
  return value === "admin" || value === "doctor";
}

export function getStoredDemoRole(): DemoRole | null {
  const storedRole = window.localStorage.getItem(STORAGE_KEY);
  if (isDemoRole(storedRole)) {
    return storedRole;
  }

  return null;
}

export function storeDemoRole(role: DemoRole): void {
  window.localStorage.setItem(STORAGE_KEY, role);
}

export function clearStoredDemoRole(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}
