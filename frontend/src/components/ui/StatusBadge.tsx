interface StatusBadgeProps {
  label: string;
  tone: "scheduled" | "completed" | "cancelled" | "no_show" | "healthy" | "failed" | "neutral";
}

const toneStyles: Record<StatusBadgeProps["tone"], string> = {
  scheduled: "bg-blue-50 text-blue-700 ring-blue-600/20",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  cancelled: "bg-rose-50 text-rose-700 ring-rose-600/20",
  no_show: "bg-slate-100 text-slate-700 ring-slate-500/20",
  healthy: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  failed: "bg-rose-50 text-rose-700 ring-rose-600/20",
  neutral: "bg-slate-100 text-slate-700 ring-slate-500/20",
};

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${toneStyles[tone]}`}
    >
      {label}
    </span>
  );
}
