import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  CalendarPlus,
  ClipboardPlus,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  Share2,
  UserPlus,
  Users,
  X,
  type LucideIcon,
} from "lucide-react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { fetchHealth, type HealthResponse } from "../app/api";
import { clearStoredDemoRole, getStoredDemoRole, storeDemoRole, type DemoRole } from "../app/demoRole";
import { StatCard } from "./dashboard/StatCard";
import { HealthCard } from "./HealthCard";

export interface AppLayoutContext {
  role: DemoRole;
}

interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  end?: boolean;
}

const primaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition duration-200 hover:bg-indigo-700";

const secondaryButtonClass =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition duration-200 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800";

const primaryNav: NavItem[] = [
  { label: "Dashboard", to: "/appointments", icon: LayoutDashboard, end: true },
  { label: "Patients", to: "/patients", icon: Users },
  { label: "Visits", to: "/visits/new", icon: ClipboardPlus },
];

const quickCreateNav: NavItem[] = [
  { label: "New Appointment", to: "/appointments/new", icon: CalendarPlus },
];

export function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [role, setRole] = useState<DemoRole>(() => getStoredDemoRole() ?? "doctor");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const roleLabel = role === "admin" ? "Admin" : "Doctor";
  const pageMeta = useMemo(() => getPageMeta(location.pathname, roleLabel), [location.pathname, roleLabel]);

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

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  function handleRoleChange(nextRole: DemoRole) {
    storeDemoRole(nextRole);
    setRole(nextRole);
  }

  function handleSignOut() {
    clearStoredDemoRole();
    navigate("/auth", { replace: true });
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto grid min-h-screen max-w-[1600px] lg:grid-cols-[280px_minmax(0,1fr)]">
        <button
          aria-hidden={!mobileNavOpen}
          className={`fixed inset-0 z-30 bg-slate-900/30 transition duration-200 lg:hidden ${
            mobileNavOpen ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
          }`}
          onClick={() => setMobileNavOpen(false)}
          tabIndex={mobileNavOpen ? 0 : -1}
          type="button"
        />

        <aside
          id="demo-sidebar"
          className={`fixed inset-y-0 left-0 z-40 w-[280px] border-r border-slate-200 bg-slate-50 px-4 py-4 transition duration-200 dark:border-slate-800 dark:bg-slate-900 lg:static lg:translate-x-0 ${
            mobileNavOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between">
              <Link className="flex items-center gap-2 text-slate-900 dark:text-slate-100" to="/appointments">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600 text-sm font-semibold text-white">
                  N
                </span>
                <span className="text-sm font-semibold tracking-tight">NigehbaanDastak</span>
              </Link>
              <button
                className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 text-slate-600 transition duration-200 hover:bg-slate-100 lg:hidden"
                onClick={() => setMobileNavOpen(false)}
                type="button"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <nav className="mt-6 space-y-5">
              <NavGroup items={primaryNav} title="Workspace" />
              <NavGroup
                items={role === "admin" ? [...quickCreateNav, { label: "New Patient", to: "/patients/new", icon: UserPlus }] : quickCreateNav}
                title="Quick Create"
              />
            </nav>

            <div className="mt-6 space-y-4 border-t border-slate-200 pt-4 dark:border-slate-800">
              <label className="block space-y-2">
                <span className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">Role</span>
                <select
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition duration-200 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                  value={role}
                  onChange={(event) => handleRoleChange(event.target.value as DemoRole)}
                >
                  <option value="admin">Admin</option>
                  <option value="doctor">Doctor</option>
                </select>
              </label>

              <button className={secondaryButtonClass} onClick={handleSignOut} type="button">
                <LogOut className="h-4 w-4" />
                Switch demo user
              </button>
            </div>

            <div className="mt-5">
              <HealthCard error={healthError} health={health} />
            </div>
          </div>
        </aside>

        <section className="min-w-0">
          <div className="mx-auto flex max-w-7xl flex-col space-y-6 px-6 py-6">
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 shadow-sm lg:hidden dark:border-slate-800 dark:bg-slate-900">
              <button
                aria-controls="demo-sidebar"
                aria-expanded={mobileNavOpen}
                className={secondaryButtonClass}
                onClick={() => setMobileNavOpen((current) => !current)}
                type="button"
              >
                <Menu className="h-4 w-4" />
                {mobileNavOpen ? "Hide menu" : "Menu"}
              </button>
              <span className="text-sm font-medium text-slate-600 dark:text-slate-300">{roleLabel}</span>
            </div>

            <header className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-2">
                  <h1 className="text-3xl font-semibold tracking-tight">{pageMeta.title}</h1>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{pageMeta.description}</p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <label className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input
                      className="h-10 w-56 rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                      placeholder="Search"
                      readOnly
                    />
                  </label>

                  <span className="inline-flex items-center rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 ring-1 ring-inset ring-indigo-200 dark:bg-indigo-500/20 dark:text-indigo-200 dark:ring-indigo-400/40">
                    {roleLabel}
                  </span>

                  <button className={primaryButtonClass} type="button">
                    <Share2 className="h-4 w-4" />
                    Share access
                  </button>
                </div>
              </div>
            </header>

            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              <StatCard
                accentClassName="bg-indigo-50 text-indigo-600"
                description="Currently under care"
                icon={Users}
                title="Active Patients"
                value="34"
              />
              <StatCard
                accentClassName="bg-sky-50 text-sky-600"
                description="Scheduled in queue"
                icon={Activity}
                title="Upcoming Appointments"
                value="12"
              />
              <StatCard
                accentClassName="bg-emerald-50 text-emerald-600"
                description="Visits opened today"
                icon={ClipboardPlus}
                title="Visits Today"
                value="7"
              />
            </section>

            <div className="space-y-6">
              <Outlet context={{ role } satisfies AppLayoutContext} />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function NavGroup({ title, items }: { title: string; items: NavItem[] }) {
  return (
    <div className="space-y-2">
      <p className="px-3 text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">{title}</p>
      <div className="space-y-1">
        {items.map((item) => (
          <NavLink
            key={`${item.to}-${item.label}`}
            className={({ isActive }) =>
              [
                "group flex items-center gap-3 rounded-lg border px-3 py-2.5 text-sm font-medium transition duration-200",
                isActive
                  ? "border-indigo-100 bg-indigo-50 text-indigo-700 dark:border-indigo-500/40 dark:bg-indigo-500/15 dark:text-indigo-200"
                  : "border-transparent text-slate-600 hover:border-slate-200 hover:bg-white hover:text-slate-900 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:bg-slate-800",
              ].join(" ")
            }
            end={item.end}
            to={item.to}
          >
            <item.icon className="h-4 w-4" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </div>
    </div>
  );
}

function getPageMeta(pathname: string, roleLabel: string): { title: string; description: string } {
  if (pathname === "/appointments/new") {
    return {
      title: "Create Appointment",
      description: "Schedule a new appointment and capture initial notes.",
    };
  }

  if (pathname === "/patients") {
    return {
      title: "Patient Directory",
      description: "Manage records, search patients, and review their care details.",
    };
  }

  if (pathname === "/patients/new") {
    return {
      title: "Add Patient",
      description: "Create a new patient profile with demographic and contact information.",
    };
  }

  if (pathname.startsWith("/visits/new")) {
    return {
      title: "Create Visit",
      description: "Start a clinical visit from an appointment or direct intake.",
    };
  }

  return {
    title: `Welcome, ${roleLabel}`,
    description: "Track appointments, patient flow, and operational status in one view.",
  };
}
