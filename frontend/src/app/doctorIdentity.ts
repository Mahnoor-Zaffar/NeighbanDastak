import { getStoredDemoSession, updateStoredDemoSession } from "./demoRole";

const PROFILE_ID_KEY = "nd-doctor-profile-id";
const PROFILE_NAME_KEY = "nd-doctor-display-name";
const DIRECTORY_KEY = "nd-doctor-directory";

export function getStoredDoctorProfileId(): string {
  const session = getStoredDemoSession();
  if (session?.role === "doctor" && session.doctorProfileId) {
    return session.doctorProfileId;
  }
  return window.localStorage.getItem(PROFILE_ID_KEY) ?? "";
}

export function storeDoctorProfileId(doctorId: string): void {
  const normalized = doctorId.trim();
  if (!normalized) {
    window.localStorage.removeItem(PROFILE_ID_KEY);
    updateStoredDemoSession({
      userId: null,
      doctorProfileId: null,
    });
    return;
  }

  window.localStorage.setItem(PROFILE_ID_KEY, normalized);
  updateStoredDemoSession({
    userId: normalized,
    doctorProfileId: normalized,
  });
}

export function getStoredDoctorDisplayName(): string {
  const session = getStoredDemoSession();
  if (session?.role === "doctor" && session.fullName) {
    return session.fullName;
  }
  return window.localStorage.getItem(PROFILE_NAME_KEY) ?? "";
}

export function storeDoctorDisplayName(doctorName: string): void {
  const normalized = doctorName.trim();
  if (!normalized) {
    window.localStorage.removeItem(PROFILE_NAME_KEY);
    updateStoredDemoSession({
      fullName: null,
    });
    return;
  }

  window.localStorage.setItem(PROFILE_NAME_KEY, normalized);
  updateStoredDemoSession({
    fullName: normalized,
  });
}

export function rememberDoctorProfile(doctorId: string, doctorName: string): void {
  const normalizedId = doctorId.trim();
  const normalizedName = doctorName.trim();

  if (!normalizedId) {
    return;
  }
  storeDoctorProfileId(normalizedId);
  if (normalizedName) {
    storeDoctorDisplayName(normalizedName);
  }

  const parsed = readDoctorDirectory();
  if (normalizedName) {
    parsed[normalizedId] = normalizedName;
    window.localStorage.setItem(DIRECTORY_KEY, JSON.stringify(parsed));
  }
}

export function resolveDoctorDisplayName(doctorId: string): string {
  const parsed = readDoctorDirectory();
  const fromDirectory = parsed[doctorId];
  if (fromDirectory) {
    return fromDirectory;
  }

  const profileId = getStoredDoctorProfileId();
  const profileName = getStoredDoctorDisplayName();
  if (profileId && doctorId === profileId && profileName) {
    return profileName;
  }

  return "Attending Doctor";
}

function readDoctorDirectory(): Record<string, string> {
  try {
    const raw = window.localStorage.getItem(DIRECTORY_KEY);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}
