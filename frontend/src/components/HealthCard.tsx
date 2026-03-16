import type { HealthResponse } from "../app/api";
import { StatusBadge } from "./ui/StatusBadge";

interface HealthCardProps {
  health: HealthResponse | null;
  error: string | null;
}

export function HealthCard({ health, error }: HealthCardProps) {
  const isConnected = Boolean(health && !error);
  const tone = isConnected ? "healthy" : error ? "failed" : "neutral";
  const label = isConnected ? "Connected" : error ? "Failed" : "Checking";

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-300">API Status</p>
          <StatusBadge label={label} tone={tone} />
        </div>

        {health ? (
          <dl className="space-y-1 text-sm text-slate-500 dark:text-slate-400">
            <div className="flex items-center justify-between gap-3">
              <dt>Service</dt>
              <dd className="font-medium text-slate-700 dark:text-slate-200">{health.service}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt>Environment</dt>
              <dd className="font-medium text-slate-700 dark:text-slate-200">{health.environment}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt>Version</dt>
              <dd className="font-medium text-slate-700 dark:text-slate-200">{health.version}</dd>
            </div>
          </dl>
        ) : (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {error ?? "Checking backend health..."}
          </p>
        )}
      </div>
    </section>
  );
}
