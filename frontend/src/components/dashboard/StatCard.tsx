import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string;
  description: string;
  icon: LucideIcon;
  accentClassName: string;
}

export function StatCard({ title, value, description, icon: Icon, accentClassName }: StatCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-sm text-slate-500 dark:text-slate-400">{title}</p>
          <p className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{value}</p>
          <p className="text-sm text-slate-500 dark:text-slate-400">{description}</p>
        </div>
        <span className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${accentClassName}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>
    </article>
  );
}
